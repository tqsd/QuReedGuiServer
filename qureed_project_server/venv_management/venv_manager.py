from virtualenvapi.manage import VirtualEnvironment

from qureed_project_server.logic_modules import LogicModuleEnum, LogicModuleHandler

LMH = LogicModuleHandler()

class VenvManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VenvManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
            
    def __init__(self):
        if not hasattr(self, "initialized"):
            self.venv = None
            LMH.register(LogicModuleEnum.VENV_MANAGER, self)
            self.initialized = True

    def connect(self, path):
        self.venv = VirtualEnvironment(path)

    def install(self, package):
        print("Installing")
        self.venv.install(package)

    def uninstall(self, package):
        self.venv.uninstall(package)

    def freeze(self):
        packages = []
        for package, version in self.venv.installed_packages:
            if version is None:
                packages.append(package)  # Append the package name only if the version is None
            else:
                packages.append(f"{package}=={version}")  # Format as 'name==version'

        return "\n".join(packages)
