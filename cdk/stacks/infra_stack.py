import os
from constructs import Construct
from cdktf_cdktf_provider_google.provider import GoogleProvider
from cdktf_cdktf_provider_google.storage_bucket import StorageBucket
from cdktf_cdktf_provider_google.firestore_database import FirestoreDatabase
from cdktf_cdktf_provider_google.service_account import ServiceAccount
from cdktf_cdktf_provider_google.project_iam_member import ProjectIamMember
from cdktf_cdktf_provider_google.artifact_registry_repository import ArtifactRegistryRepository
from cdktf_cdktf_provider_google.cloud_run_v2_service import CloudRunV2Service
from cdktf_cdktf_provider_google.cloud_run_v2_service_iam_member import CloudRunV2ServiceIamMember
from cdktf_cdktf_provider_google.project_service import ProjectService
from cdktf_cdktf_provider_google.storage_bucket_iam_member import StorageBucketIamMember
from cdktf_cdktf_provider_google.cloudfunctions2_function import Cloudfunctions2Function
from cdktf_cdktf_provider_google.pubsub_topic import PubsubTopic
from cdktf import TerraformStack, GcsBackend, TerraformVariable
from cdktf_cdktf_provider_google.storage_bucket_object import StorageBucketObject

class InfraStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        project_id = "ts-eras-quiz"
        region = "europe-central2"

        # ---------------------------
        # Terraform backend
        # ---------------------------
        GcsBackend(
            self,
            bucket="ts-eras-quiz-tfstate",
            prefix="cdktf/infra-stack",
        )

        # ---------------------------
        # Provider
        # ---------------------------
        GoogleProvider(
            self,
            "google",
            project=project_id,
            region=region,
        )

        # ---------------------------
        # REQUIRED APIS
        # ---------------------------
        run_api = ProjectService(self, "run-api", service="run.googleapis.com", disable_on_destroy=False)
        firestore_api = ProjectService(self, "firestore-api", service="firestore.googleapis.com", disable_on_destroy=False)
        artifact_api = ProjectService(self, "artifact-api", service="artifactregistry.googleapis.com", disable_on_destroy=False)
        iam_api = ProjectService(self, "iam-api", service="iam.googleapis.com", disable_on_destroy=False)
        storage_api = ProjectService(self, "storage-api", service="storage.googleapis.com", disable_on_destroy=False)
        pubsub_api = ProjectService(self, "pubsub-api", service="pubsub.googleapis.com", disable_on_destroy=False)
        cloudbuild_api = ProjectService(self, "cloudbuild-api", service="cloudbuild.googleapis.com", disable_on_destroy=False)
        cloudfunctions_api = ProjectService(self, "cloudfunctions-api", service="cloudfunctions.googleapis.com", disable_on_destroy=False)
        eventarc_api = ProjectService(self, "eventarc-api", service="eventarc.googleapis.com", disable_on_destroy=False)

        # ---------------------------
        # Firestore
        # ---------------------------
        firestore_db = FirestoreDatabase(
            self,
            "firestore",
            name="(default)",
            location_id="eur3",
            type="FIRESTORE_NATIVE",
            deletion_policy="DELETE",
        )

        firestore_db.node.add_dependency(firestore_api)

        # ---------------------------
        # Storage
        # ---------------------------
        images_bucket = StorageBucket(
            self,
            "images-bucket",
            name="ts-eras-quiz-images",
            location="EU",
            uniform_bucket_level_access=True,
            force_destroy=True,
        )

        images_bucket.node.add_dependency(storage_api)

        public_access = StorageBucketIamMember(
            self,
            "public-access",
            bucket=images_bucket.name,
            role="roles/storage.objectViewer",
            member="allUsers",
        )

        public_access.node.add_dependency(images_bucket)

        # ---------------------------
        # Artifact Registry
        # ---------------------------
        backend_repo = ArtifactRegistryRepository(
            self,
            "backend-repo",
            location=region,
            repository_id="ts-eras-quiz-docker-repo",
            format="DOCKER",
            description="Docker images",
        )
        
        backend_repo.node.add_dependency(artifact_api)

        # ---------------------------
        # Service Account
        # ---------------------------
        backend_sa = ServiceAccount(
            self,
            "backend-sa",
            account_id="backend-sa",
            display_name="Backend Service Account",
        )

        backend_sa.node.add_dependency(iam_api)

        quiz_func_sa = ServiceAccount(
            self,
            "quiz-func-sa",
            account_id="quiz-function-sa",
        )

        # ---------------------------
        # IAM permissions
        # ---------------------------
        firestore_access = ProjectIamMember(
            self,
            "backend-firestore",
            project=project_id,
            role="roles/datastore.user",
            member=f"serviceAccount:{backend_sa.email}",
        )
        firestore_access.node.add_dependency(firestore_db)

        storage_access = ProjectIamMember(
            self,
            "backend-storage",
            project=project_id,
            role="roles/storage.objectAdmin",
            member=f"serviceAccount:{backend_sa.email}",
        )

        storage_access.node.add_dependency(images_bucket)

        ProjectIamMember(
            self,
            "backend-pubsub-publisher",
            project=project_id,
            role="roles/pubsub.publisher",
            member=f"serviceAccount:{backend_sa.email}",
        )

        ProjectIamMember(
            self,
            "quiz-metric-writer",
            project=project_id,
            role="roles/monitoring.metricWriter",
            member=f"serviceAccount:{quiz_func_sa.email}",
        )

        # ---------------------------
        # Cloud Run
        # ---------------------------
        backend_service = CloudRunV2Service(
            self,
            "backend-service",
            name="backend",
            location=region,
            ingress="INGRESS_TRAFFIC_ALL",
            deletion_protection=False,
            template={
                "service_account": backend_sa.email,
                "containers": [
                    {
                        "image": "gcr.io/google-samples/hello-app:1.0",
                    }
                ],
            },
        )
        backend_service.node.add_dependency(run_api)
        backend_service.node.add_dependency(backend_sa)

        # ---------------------------
        # Public access
        # ---------------------------
        public_invoker = CloudRunV2ServiceIamMember(
            self,
            "public-invoker",
            name=backend_service.name,
            location=region,
            role="roles/run.invoker",
            member="allUsers",
        )

        public_invoker.node.add_dependency(backend_service)

        # ---------------------------
        # Pub/Sub
        # ---------------------------
        quiz_topic = PubsubTopic(self, "quiz-topic", name="quiz-topic")
        quiz_topic.node.add_dependency(pubsub_api)

        # ---------------------------
        # Pub/Sub Topic
        # ---------------------------
        zip_path = os.path.join(os.path.dirname(__file__), "..", "quiz_processor.zip")

        quiz_zip = StorageBucketObject(
            self,
            "quiz-zip",
            bucket=images_bucket.name,
            name="quiz_processor.zip",
            source=zip_path,
        )

        # ---------------------------
        # Variables
        # ---------------------------
        sendgrid_api_key = TerraformVariable(
            self,
            "sendgrid_api_key",
            type="string",
            sensitive=True,
        )

        # ---------------------------
        # Cloud Functions
        # ---------------------------
        Cloudfunctions2Function(
            self,
            "quiz-processor",
            name="quiz-processor",
            location=region,
            build_config={
                "runtime": "python311",
                "entry_point": "quiz_event_handler",
                "source": {
                    "storage_source": {
                        "bucket": images_bucket.name,
                        "object": quiz_zip.name,
                    }
                },
            },
            service_config={
                "service_account_email": quiz_func_sa.email,
                "available_memory": "256M",
                "timeout_seconds": 60,
                "environment_variables": {
                    "GCP_PROJECT_ID": project_id,
                    "SENDGRID_API_KEY": sendgrid_api_key.string_value,
                },
            },
            event_trigger={
                "event_type": "google.cloud.pubsub.topic.v1.messagePublished",
                "pubsub_topic": quiz_topic.id,
                "retry_policy": "RETRY_POLICY_RETRY",
            },
        )
