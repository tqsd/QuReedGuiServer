from pathlib import Path
import sys
from virtualenvapi.manage import VirtualEnvironment

from qureed_project_server.logic_modules import LogicModuleEnum, LogicModuleHandler

LMH = LogicModuleHandler()

class VenvManager:
    """
    VenvManager (Singleton) manages the virtual environment. It establishes the
    connection to the project venv as well as installing and uninstalling the
    packages

    Attributes:
    -----------
    venv (VirtualEnvironment): virtual environment wrapper
    path (str): absolute path to the virtual environment
    initialized (bool): Initialization flag for the Singleton Pattern

    Methods:
    --------
    connect(path:str): Connect to the venv
    install(package:str): Tries to install the requested package
    uninstall(package:str): Tries to uninstall the requested package
    freeze(package:str): Returns the list of installed packages
        like `pip freeze`

    Examples:
    ---------
    Example of usage:
        >>> from qureed_project_server.logic_modules import (
        >>> LogicModuleEnum,LogicModuleHandler)
        >>> VM = LogicModuleEnum().get_logic(LogicModuleEnum.VENV_MANAGER)
        >>> # Assuming .venv is stored in '.venv'
        >>> devices = QM.connect('.venv')
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VenvManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
            
    def __init__(self):
        if not hasattr(self, "initialized"):
            self.venv = None
            self.path = None
            self.client_id = None
            LMH.register(LogicModuleEnum.VENV_MANAGER, self)
            self.initialized = True

    def connect(self, path:str, context) -> None:
        """
        Connects to the project "runtime"

        Parameters:
        -----------
        path: str
            path to the venv inside of the project
        Notes:
        ------
           This method also imports the project into the system path
        """
        self.path = path
        self.venv = VirtualEnvironment(path)
        # Add the 'custom' directory to sys.path
        self.gui_client = context

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

        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)
        QM.load_custom_as_package()
        # Preemptively import all devices
        QM.get_devices()
        print("CONNECTED")


    def install(self, package:str) -> None:
        """
        Installs the package into the activated environment.

        Parameters:
        -----------
        package (str): the name of the package to install
        """
        self.venv.install(package)

    def uninstall(self, package) -> None:
        """
        Uninstalls the package into the activated environment.

        Parameters:
        -----------
        package (str): the name of the package to uninstall
        """
        self.venv.uninstall(package)

    def freeze(self) -> str:
        """
        Returns the list of installed packages

        Returns:
        --------
        str: String where installed packages are given separated by new line
        """
        packages = []
        for package, version in self.venv.installed_packages:
            if version is None:
                packages.append(package)
            else:
                packages.append(f"{package}=={version}")

        return "\n".join(packages)
