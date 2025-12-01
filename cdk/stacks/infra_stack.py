from constructs import Construct
from cdktf import TerraformStack
from cdktf_cdktf_provider_google.provider import GoogleProvider

class InfraStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        GoogleProvider(
            self,
            "google",
            project="ts-eras-quiz",
            region="europe-central2",
        )

