from cdktf import Construct, TerraformStack, TerraformBackend
from cdktf import TerraformStack
from cdktf_cdktf_provider_google.provider import GoogleProvider
from cdktf_cdktf_provider_google.storage_bucket import StorageBucket

class InfraStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        TerraformBackend.google(
            self,
            bucket="ts-eras-quiz-tfstate",
            prefix="cdktf/infra-stack"
        )

        GoogleProvider(
            self,
            "google",
            project="ts-eras-quiz",
            region="europe-central2",
        )

        StorageBucket(
            self,
            "test-bucket",
            name="ts-eras-quiz-test-bucket-unique",
            location="EU",
            force_destroy=True,
        )
