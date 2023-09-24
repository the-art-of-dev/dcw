from dcw.deployment import DCWDeployment
from dcw.task import DCWTask


class DCWDeploymentConfig:
    def __init__(self, name: str, type: str, unit: str, env: str) -> None:
        self.name = name
        self.type = type
        self.unit = unit
        self.env = env



class DCWTenant:
    def __init__(self, name: str, deployments: [DCWDeployment], tasks: [DCWTask]) -> None:
        self.name = name
        self.deployments = deployments
        self.tasks = tasks

    
