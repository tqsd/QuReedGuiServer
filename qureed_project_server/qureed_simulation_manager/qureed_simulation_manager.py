
from qureed_project_server.logic_modules import (
    LogicModuleEnum, LogicModuleHandler
)

LMH = LogicModuleHandler()

class SimulationAlreadyRunningError(Exception):
    """Only one simulation can be executed at one time"""

class QuReedSimulationManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(QuReedSimulationManager, cls).__new__(
                cls, *args, **kwargs
                )
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            LMH.register(LogicModuleEnum.SIMULATION_MANAGER, self)
            self.initialized = True
            self.running_simulation = None

    def start_simulation(self, scheme):
        if self.running_simulation:
            raise SimulationAlreadyRunningError(
                "Only one simulation can be running at a time."
            )

        