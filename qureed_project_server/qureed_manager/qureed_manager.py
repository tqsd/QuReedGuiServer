import json
import sys
import importlib.util
import inspect
import traceback
import os
from pathlib import Path
from qureed_project_server.logic_modules import LogicModuleEnum,LogicModuleHandler
from qureed_project_server import server_pb2
import pkgutil
#from qureed.devices.generic_device import GenericDevice

LMH = LogicModuleHandler()

class QuReedManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(QuReedManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
            
    def __init__(self):
        if not hasattr(self, "initialized"):
            LMH.register(LogicModuleEnum.QUREED_MANAGER, self)
            self.opened_scheme = None
            self.initialized = True

    def get_devices(self):
        try:
            VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
            spec = importlib.util.find_spec("qureed")
            if not spec or not spec.submodule_search_locations:
                print("Could not locate 'qureed' package")
                return []

            qureed_path = Path(next(iter(spec.submodule_search_locations)))
            builtin_devices_path = qureed_path / "devices"
            custom_devices_path = Path(VM.path).parents[0] / "custom" / "devices"
            message = ""

            if not qureed_path.exists():
                message = f"Builtin devices not found in {qureed_path}"
            if not qureed_path.exists():
                message += f"\nCustom devices not found in {custom_devices_path}"


            device_list = []

            
            # Getting builtin QuReed Devices
            for root, _, files in os.walk(builtin_devices_path):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        module_path = Path(root) / file
                        module_name = str(module_path.relative_to(qureed_path)).replace(os.sep, ".").replace(".py", "")

                        # Dynamically import the module
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        try:
                            spec.loader.exec_module(module)
                        except Exception as e:
                            continue
                        device_message = self.create_device_message_from_module(module)
                        device_list.extend(device_message)

            # Getting Custom Devices
            for root, _, files in os.walk(custom_devices_path):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        module_path = Path(root) / file
                        module_name = str(module_path.relative_to(custom_devices_path)).replace(os.sep, ".").replace(".py", "")
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        try:
                            spec.loader.exec_module(module)
                        except Exception as e:
                            continue
                        device_message = self.create_device_message_from_module(module)
                        device_list.extend(device_message)
                        
            
            return device_list, message

        except Exception as e:
            print(e)
            traceback.print_exc()

    def get_icon_location(self, icon):

        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        
        if "custom" in icon.split("/"):
            return str(Path(VM.path).parents[0] / icon.lstrip("/"))
        else:
            loader = pkgutil.get_loader("qureed")
            if loader and loader.is_package("qureed"):
                return str(Path(loader.get_filename()).parent / "assets" /icon)
            

    def create_device_message(self, device_class):
        class_name = device_class.__name__
        print(class_name)
        module_class = f"{device_class.__module__}.{device_class.__qualname__}"
        print(module_class)
        gui_name = getattr(device_class, "gui_name", None)
        if not isinstance(gui_name, str):
            gui_name = class_name

        gui_tags = getattr(device_class, "gui_tags", None)
        gui_icon = self.get_icon_location(getattr(device_class, "gui_icon", None))
        print("GUI ICON")
        print(gui_icon)
        
        ports = []
        if hasattr(device_class, "ports"):
            print("HAS PORTS")
            if isinstance(device_class.ports, dict):
                for port_name, port in device_class.ports.items():
                    ports.append(server_pb2.Port(
                        label=port.label,
                        direction=port.direction,
                        signal_type=str(port.signal_type.__name__)
                    ))

        device_msg = server_pb2.Device(
            class_name=class_name,
            gui_name=gui_name,
            module_class=module_class,
            ports=ports,
            gui_tags=gui_tags,
            icon=server_pb2.GetIconResponse(
                abs_path=gui_icon
                )
            )

        return device_msg

    def create_device_message_from_module(self, module):
        device_classes = []
        device_messages = []

        GenericDevice = self.get_class("qureed.devices.generic_device.GenericDevice")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if inspect.isclass(attr) and issubclass(attr, GenericDevice) and attr is not GenericDevice:
                device_classes.append(attr)

                class_name = attr.__name__
                gui_name = getattr(attr, "gui_name", None)
                gui_icon = getattr(attr, "gui_icon", None)
                gui_tags = getattr(attr, "gui_tags", None)
                module_name = module.__name__

                # Handle ports if defined
                ports = []
                if hasattr(attr, "ports"):
                    if isinstance(attr.ports, dict):
                        for port_name, port in attr.ports.items():
                            ports.append(server_pb2.Port(
                                label=port.label,
                                direction=port.direction,
                                signal_type=str(port.signal_type.__name__)
                            ))
                if not isinstance(gui_name, str):
                    gui_name = class_name

                # Construct the Device Protobuf message
                device_message = server_pb2.Device(
                    class_name=class_name,
                    gui_name=gui_name,
                    module_class=f"{module_name}.{class_name}",
                    ports=ports,
                    gui_tags=gui_tags,
                )

                device_messages.append(device_message)

        return device_messages

    def open_scheme(self, board):
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        BM = LMH.get_logic(LogicModuleEnum.BOARD_MANAGER)
        project_root = Path(VM.path).parents[0]
        scheme = project_root / board

        print(scheme)

        with open(scheme, "r") as f:
            data = json.load(f)


        print("We have the data, is there an error")
        return BM.open_scheme(data)

    def get_class(self, mc: str):
        """
        Gets the class based on the device_mc

        Parameters:
        - mc: str
            A string describing the module and class path.
            Example: "qureed.devices.variables.variable.Variable"

        Returns:
        - class: type
            The requested class if found.

        Raises:
        - ModuleNotFoundError: If the module is not found.
        - AttributeError: If the class is not found in the module.
        """
        try:
            # Split the module path and class name
            *module_path, class_name = mc.split(".")
            module_name = ".".join(module_path)

            # Import the module dynamically
            module = importlib.import_module(module_name)

            # Get the class from the module
            cls = getattr(module, class_name)

            return cls
        except ModuleNotFoundError:
            print(f"Module '{module_name}' not found.")
            print(sys.path)
            print(sys.executable)
            raise
        except AttributeError:
            print(f"Class '{class_name}' not found in module '{module_name}'.")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
