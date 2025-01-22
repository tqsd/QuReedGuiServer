from enum import StrEnum

class LogicModuleEnum(StrEnum):
    VENV_MANAGER = "venv_manager"
    QUREED_MANAGER = "qureed_manager"

class LogicModuleHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LogicModuleHandler, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self,"initialized"):
            self.modules = {}
            self.initialized=True

    def register(self, module_type:LogicModuleEnum, module):
        self.modules[module_type]=module

    def get_logic(self, module_type):
        return self.modules[module_type]
