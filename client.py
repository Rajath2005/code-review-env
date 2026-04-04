from openenv.core.env_server import EnvClient
from models import CodeReviewAction, CodeReviewObservation

class CodeReviewEnvClient(EnvClient):
    action_class = CodeReviewAction
    observation_class = CodeReviewObservation
    def reset(self, task_name="bug_identification"):
        return super().reset(task_name=task_name)
