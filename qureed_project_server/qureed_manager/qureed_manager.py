import importlib.util
import inspect
import traceback
import os
from pathlib import Path
from qureed_project_server.logic_modules import LogicModuleEnum,LogicModuleHandler
from qureed_project_server import server_pb2
from qureed.devices.generic_device import GenericDevice

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
                        device_message = self.create_device_message(module)
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
                        device_message = self.create_device_message(module)
                        device_list.extend(device_message)
                        
            
            return device_list, message

        except Exception as e:
            print(e)
            traceback.print_exc()

    def create_device_message(self, module):
        device_classes = []
        device_messages = []

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if inspect.isclass(attr) and issubclass(attr, GenericDevice) and attr is not GenericDevice:
                device_classes.append(attr)

                class_name = attr.__name__
                gui_name = getattr(attr, "gui_name", None)
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
                    ports=ports
                )

                device_messages.append(device_message)

        return device_messages
