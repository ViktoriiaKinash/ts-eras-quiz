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

class InfraStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)
        project_id = "ts-eras-quiz"

        GcsBackend(
            self,
            bucket="ts-eras-quiz-tfstate",
            prefix="cdktf/infra-stack",
        )

        GoogleProvider(
            self,
            "google",
            project=project_id,
            region="europe-central2",
        )

        FirestoreDatabase(
            self,
            "firestore",
            name="(default)",
            location_id="eur3",
            type="NATIVE",
        )

        StorageBucket(
            self,
            "images-bucket",
            name="ts-eras-quiz-images",
            location="EU",
            uniform_bucket_level_access=True,
            force_destroy=True,
        )

        ArtifactRegistryRepository(
            self,
            "backend-repo",
            location="europe-central2",
            repository_id="ts-eras-quiz-docker-repo",
            format="DOCKER",
            description="Docker images",
        )

        backend_sa = ServiceAccount(
            self,
            "backend-sa",
            account_id="backend-sa",
            display_name="Backend Service Account",
        )

        ProjectIamMember(
            self,
            "firestore-access",
            project=project_id,
            role="roles/datastore.user",
            member=f"serviceAccount:{backend_sa.email}",
        )

        ProjectIamMember(
            self,
            "storage-access",
            project=project_id,
            role="roles/storage.objectAdmin",
            member=f"serviceAccount:{backend_sa.email}",
        )

        backend_service = CloudRunV2Service(
            self,
            "backend-service",
            name="backend",
            location="europe-central2",
            ingress="INGRESS_TRAFFIC_ALL",
            template={
                "service_account": backend_sa.email,
                "containers": [
                    {
                        "image": "europe-central2-docker.pkg.dev/ts-eras-quiz/ts-eras-quiz-docker-repo/backend:latest",
                        "ports": {
                            "container_port": 8080
                        },
                    }
                ],
            },
        )

        CloudRunV2ServiceIamMember(
            self,
            "public-invoker",
            name=backend_service.name,
            location=backend_service.location,
            role="roles/run.invoker",
            member="allUsers",
        )
