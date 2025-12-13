from constructs import Construct
from cdktf import TerraformStack, GcsBackend
from cdktf_cdktf_provider_google.provider import GoogleProvider
from cdktf_cdktf_provider_google.storage_bucket import StorageBucket
from cdktf_cdktf_provider_google.firestore_database import FirestoreDatabase
from cdktf_cdktf_provider_google.service_account import ServiceAccount
from cdktf_cdktf_provider_google.project_iam_member import ProjectIamMember

class InfraStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        GcsBackend(
            self,
            bucket="ts-eras-quiz-tfstate",
            prefix="cdktf/infra-stack",
        )

        GoogleProvider(
            self,
            "google",
            project="ts-eras-quiz",
            region="europe-central2",
        )

        # FirestoreDatabase(
        #     self,
        #     "firestore",
        #     name="(default)",
        #     location_id="europe-central2",
        #     type="NATIVE",
        #     project="ts-eras-quiz",
        # )

        StorageBucket(
            self,
            "images-bucket",
            name="ts-eras-quiz-images",
            location="EU",
            uniform_bucket_level_access=True,
            force_destroy=True,
        )

        # backend_sa = ServiceAccount(
        #     self,
        #     "backend-sa",
        #     account_id="backend-sa",
        #     display_name="Backend Service Account",
        # )

        # ProjectIamMember(
        #     self,
        #     "firestore-access",
        #     role="roles/datastore.user",
        #     member=f"serviceAccount:{backend_sa.email}",
        # )

        # ProjectIamMember(
        #     self,
        #     "storage-access",
        #     role="roles/storage.objectViewer",
        #     member=f"serviceAccount:{backend_sa.email}",
        # )

