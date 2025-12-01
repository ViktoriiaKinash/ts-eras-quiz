from constructs import Construct
from cdktf import App
from stacks.infra_stack import InfraStack

app = App()

InfraStack(app, "infra")

app.synth()
