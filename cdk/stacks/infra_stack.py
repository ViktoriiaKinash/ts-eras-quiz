from constructs import Construct
from cdktf import TerraformStack, GcsBackend
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
        crm_api = ProjectService(self, "crm-api", service="cloudresourcemanager.googleapis.com", disable_on_destroy=False)
        storage_api = ProjectService(self, "cloud-storage-api", service="storage.googleapis.com", disable_on_destroy=False)
        cloudfunctions_api = ProjectService(self, "cloud-functions-api", service="cloudfunctions.googleapis.com", disable_on_destroy=False)
        pubsub_api = ProjectService(self, "pubsub-api", service="pubsub.googleapis.com", disable_on_destroy=False)
        compute_api = ProjectService(self, "compute-api", service="compute.googleapis.com", disable_on_destroy=False)

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
        ).node.add_dependency(firestore_api)

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
        ).node.add_dependency(storage_api)

        StorageBucketIamMember(
            self,
            "public-access",
            bucket=images_bucket.name,
            role="roles/storage.objectViewer",
            member="allUsers",
        ).node.add_dependency(images_bucket)

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
        ).node.add_dependency(artifact_api)

        # ---------------------------
        # Service Account
        # ---------------------------
        backend_sa = ServiceAccount(
            self,
            "backend-sa",
            account_id="backend-sa",
            display_name="Backend Service Account",
        ).node.add_dependency(iam_api)

        # ---------------------------
        # IAM permissions
        # ---------------------------
        ProjectIamMember(
            self,
            "firestore-access",
            project=project_id,
            role="roles/datastore.user",
            member=f"serviceAccount:{backend_sa.email}",
        ).node.add_dependency(firestore_db)

        ProjectIamMember(
            self,
            "storage-access",
            project=project_id,
            role="roles/storage.objectAdmin",
            member=f"serviceAccount:{backend_sa.email}",
        ).node.add_dependency(images_bucket)

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
        CloudRunV2ServiceIamMember(
            self,
            "public-invoker",
            name=backend_service.name,
            location=backend_service.location,
            role="roles/run.invoker",
            member="allUsers",
        ).node.add_dependency(backend_service)
