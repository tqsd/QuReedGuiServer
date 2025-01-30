from pathlib import Path
import sys
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
            self.path = None
            LMH.register(LogicModuleEnum.VENV_MANAGER, self)
            self.initialized = True

    def connect(self, path:str) -> None:
        """
        Connects to the project "runtime"

        Parameters:
        -----------
        - path: str
            path to the venv inside of the project
        Notes:
        ------
           This method also imports the project into the system path
        """
        self.path = path
        self.venv = VirtualEnvironment(path)
        # Add the 'custom' directory to sys.path

        custom_path = Path(self.path).parents[0] / "custom"
        # Add the parent of 'custom' to sys.path
        custom_base_path = Path(self.path).parents[0]
        if str(custom_base_path) not in sys.path:
            sys.path.insert(0, str(custom_base_path))
            print(f"Added to sys.path: {custom_base_path}")
        if not custom_path.exists():
            print(f"Warning: 'custom' directory not found at {custom_path}.")
        elif str(custom_path) not in sys.path:
            sys.path.insert(0, str(custom_path))
            print(f"'custom' directory added to sys.path: {custom_path}")

        print(f"Loading 'custom' as a package")
        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)
        QM.load_custom_as_package()


    def install(self, package:str) -> None:
        """
        Installs the package into the activated environment.
        """
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
