import json
import re
import sys
import importlib.util
import inspect
import traceback
import os
from pathlib import Path
from qureed_project_server.logic_modules import LogicModuleEnum,LogicModuleHandler
from qureed_project_server import server_pb2
from google.protobuf.json_format import MessageToDict
import pkgutil
from jinja2 import Environment, FileSystemLoader

LMH = LogicModuleHandler()

class QuReedManager:
    """
    QuReedManager (Singleton) manages different aspects of the QuReed

    It manages the dynamic importing and the 

    Attributes:
    -----------
    initialized (bool): Initialization flag for the Singleton Pattern

    Methods:
    --------
    get_devices(): Gets all the devices (Built-in and Custom in the project)    
    get_all_icons(): Gets all icons (Built-in and Custom in the project)
    get_all_signals(): Gets all signals (Built-in and Custom in the project)
    generate_new_device(device): Generates new Custom device in the project
    get_icon_location(icon): Gets abs location of the requested icon
    create_device_message(device_class): Generates a device message from 
        the device class
    load_custom_as_package(): Loads Custom (custom elements in the project)
    get_device(device_request): Dynamically loadst the device module and
        returns the class in list
    create_device_message_from_module(module): Creates the list of device
        messages from the given module
    get_class(module_class): Gets a class defined by the module.class notation
    
    Examples:
    ---------
    Example of usage:
        >>> from qureed_project_server.logic_modules import (
        >>> LogicModuleEnum,LogicModuleHandler)
        >>> QM = LogicModuleEnum().get_logic(LogicModuleEnum.QUREED_MANAGER)
        >>> devices = QM.get_devices()
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(QuReedManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            LMH.register(LogicModuleEnum.QUREED_MANAGER, self)
            self.initialized = True

    def get_devices(self) -> tuple[list[server_pb2.Device], str]:
        """
        Get all of the devices available in the project (Built-in and Custom)

        It transverses the custom directory and the directory of 'qureed' to 
        assemble the list of existing devices

        Returns:
        --------
        tuple[list[Device], str]: Returns the tuple of the list of existing devices
            as messages and a message string if anything went wrong
        """
        try:
            VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
            spec = importlib.util.find_spec("qureed")
            if not spec or not spec.submodule_search_locations:
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
                        module_name = "qureed."+str(module_path.relative_to(qureed_path)).replace(os.sep, ".").replace(".py", "")

                        # Dynamically import the module
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        try:
                            spec.loader.exec_module(module)
                        except Exception as e:
                            continue
                        device_message = self.create_device_message_from_module(module)
                        device_list.extend(device_message)

                
            custom_module = Path(VM.path).parents[0] / "custom"
            spec = importlib.util.spec_from_file_location("custom", custom_module)

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
            traceback.print_exc()

    def get_all_icons(self):
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        icons = []
        # Get built in icons
        loader = pkgutil.get_loader("qureed")
        try:
            qureed_icons = importlib.import_module("qureed.assets.icon_list")
        except ModuleNotFoundError:
            print("Failed to import qureed.assets.icon_list")
        if loader and loader.is_package("qureed") and qureed_icons:
            for icon_name, icon_file in vars(qureed_icons).items():
                if isinstance(icon_file, str) and icon_file.endswith(".png"):  # Filter only image files
                    icon_abs_path = self.get_icon_location(icon_file)
                    icons.append(
                        server_pb2.GetIconResponse(
                            name=icon_name,  # Name like "BEAM_SPLITTER"
                            abs_path=icon_abs_path  # Absolute path of the icon
                        )
                    )
        # Get Custom Icons
        
        custom_icons_path = Path(VM.path).parents[0] / "custom" / "icons"
        custom_base_path = Path(VM.path).parents[0]
        if custom_icons_path.exists() and custom_icons_path.is_dir():
            for icon_file in custom_icons_path.glob("*.png"):  # Only .png files
                icons.append(
                    server_pb2.GetIconResponse(
                        name=str(icon_file.relative_to(custom_base_path)),
                        abs_path=str(icon_file.resolve())  # Get absolute path
                    )
                )


        return icons

    def get_all_signals(self):
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        signals = set()

        spec = importlib.util.find_spec("qureed")
        if not spec or not spec.submodule_search_locations:
            return []

        qureed_path = Path(next(iter(spec.submodule_search_locations)))
        GenericSignal = self.get_class("qureed.signals.generic_signal.GenericSignal")
        builtin_signals_path = qureed_path / "signals"
        custom_signals_path = Path(VM.path).parents[0] / "custom" / "signals"

        # Getting builtin QuReed Devices
        for root, _, files in os.walk(builtin_signals_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_path = Path(root) / file
                    module_name = "qureed."+str(module_path.relative_to(qureed_path)).replace(os.sep, ".").replace(".py", "")

                    # Dynamically import the module
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(module)
                    except Exception as e:
                        continue
                    
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        if inspect.isclass(attr) and issubclass(attr, GenericSignal) or attr is GenericSignal:
                            if attr not in signals:
                                signals.add(attr)
        
        # Getting Custom Devices
        custom_path = Path(VM.path).parents[0]
        for root, _, files in os.walk(custom_signals_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_path = Path(root) / file
                    module_name = str(module_path.relative_to(custom_path)).replace(os.sep, ".").replace(".py", "")
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(module)
                    except Exception as e:
                        continue
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if inspect.isclass(attr) and issubclass(attr, GenericSignal) or attr is GenericSignal:
                            if attr not in signals:
                                signals.add(attr)
        signals_msg = []
        
        for s in signals:
            signals_msg.append(server_pb2.Signal(
                module_class = f"{s.__module__}.{s.__qualname__}",
                name=s.__qualname__
            ))
        return signals_msg

    def generate_new_device(self, device:server_pb2.Device):
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        template_module = importlib.import_module("qureed.templates")
        template_dir = os.path.dirname(os.path.abspath(template_module.__file__))
        template_path = str(Path(template_dir))
        file_name = re.sub(r'(?<!^)(?=[A-Z])', '_', device.gui_name).lower().replace(" ", "")
        file_name += ".py"
        class_name = device.gui_name.title().replace(" ", "")
        
        env=Environment(loader=FileSystemLoader(template_path))
        template=env.get_template("device_template.jinja")
        input_ports={
            port.label:port.signal_type for port in
            device.ports if port.direction == "input"
            }
        output_ports={
            port.label:port.signal_type for port in
            device.ports if port.direction == "output"
            }
        properties=MessageToDict(device.device_properties.properties)
        gui_icon=device.icon.name
        gui_icon = gui_icon.replace("\\", "/")

        rendered_device = template.render(
            name=device.gui_name,
            class_name=class_name,
            tags=list(device.gui_tags),
            input_ports=input_ports,
            output_ports=output_ports,
            gui_icon=gui_icon,
            properties=properties,
            custom=True
            )

        file_location = Path(VM.path).parents[0] / "custom" / "devices" / file_name
        if file_location.exists():
            raise Exception("Device with this name already exists")
        with open(file_location, "w") as f:
            f.write(rendered_device)

    def get_icon_location(self, icon):
        if not icon:
            return ""

        # Normalize the icon path to use forward slashes (cross-platform)
        normalized_icon = icon.replace("\\", "/")
        
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)

        if "custom/icons" in normalized_icon:
            return str(Path(VM.path).parents[0] / normalized_icon.lstrip("/"))
        else:
            loader = pkgutil.get_loader("qureed")
            if loader and loader.is_package("qureed"):
                return str(Path(loader.get_filename()).parent / "assets" / normalized_icon)

    def create_device_message(self, device_class):
        BM = LMH.get_logic(LogicModuleEnum.BOARD_MANAGER)
        class_name = device_class.__name__
        module_class = f"{device_class.__module__}.{device_class.__qualname__}"
        gui_name = getattr(device_class, "gui_name", None)
        if not isinstance(gui_name, str):
            gui_name = class_name

        gui_tags = getattr(device_class, "gui_tags", None)
        gui_icon = self.get_icon_location(getattr(device_class, "gui_icon", None))
        
        ports = []
        if hasattr(device_class, "ports"):
            if isinstance(device_class.ports, dict):
                for port_name, port in device_class.ports.items():
                    ports.append(server_pb2.Port(
                        label=port.label,
                        direction=port.direction,
                        signal_type=str(port.signal_type.__name__)
                    ))

        device_instance = device_class()
        properties = BM.serialize_properties(device_instance.properties)
        del device_instance

        device_msg = server_pb2.Device(
            class_name=class_name,
            gui_name=gui_name,
            module_class=module_class,
            ports=ports,
            gui_tags=gui_tags,
            device_properties=server_pb2.DeviceProperties(
                properties=properties),
            icon=server_pb2.GetIconResponse(
                abs_path=gui_icon)
            )

        return device_msg

    def load_custom_as_package(self):
        """
        Load Custom as a package, so that custom modules
        can be handled easily
        """
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        custom_path = Path(VM.path).parents[0] / "custom"

        # Ensure 'custom'is in sys.path
        if str(custom_path.parent) not in sys.path:
            sys.path.insert(0, str(custom_path.parent))

        spec = importlib.util.find_spec("custom")
        if spec is None:
            raise ImportError("Could not find 'custom' package!")

        custom = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(custom)

        def import_submodules(package_name):
            package=importlib.import_module(package_name)
            if hasattr(package, "__path__"):
                for _, submodule_name, is_pkg in pkgutil.walk_packages(
                        package.__path__, package.__name__ + "."):
                    try:
                        submodule = importlib.import_module(submodule_name)
                        parent_name = ".".join(submodule_name.split(".")[:-1])
                        parent_module = importlib.import_module(parent_name)
                        setattr(parent_module, submodule_name.split(".")[-1], submodule) 

                        if is_pkg:
                            import_submodules(submodule_name)
                    except ModuleNotFoundError:
                        print(f"Warning: '{submodule_name}' could not be loaded.")
                    
        import_submodules("custom.signals")
        import_submodules("custom.devices")
 
    def get_device(self, device_request:server_pb2.GetDeviceRequest):
        """
        Gets the device, based on the module class representation or based on
        the module path
        """

        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)

        custom_devices_path = Path(VM.path).parents[0] / "custom" / "devices"
        try:
            if device_request.module_class:
                pass

            elif device_request.module_path:
                module_path = Path(device_request.module_path)
                module_name = str(module_path.relative_to(custom_devices_path)).replace(os.sep, ".").replace(".py", "")

                # Dynamically import the module
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                device_message = self.create_device_message_from_module(module)
                return device_message[0]
        except Exception as e:
            traceback.print_exc()
        raise Exception("No device found")

    def create_device_message_from_module(self, module):
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        BM = LMH.get_logic(LogicModuleEnum.BOARD_MANAGER)
        project_root = Path(VM.path).parents[0]
        device_classes = []
        device_messages = []

        GenericDevice = self.get_class("qureed.devices.generic_device.GenericDevice")
        GenericFiber = self.get_class("qureed.devices.fiber.generic_fiber.GenericFiber")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if inspect.isclass(attr) and issubclass(attr, GenericDevice) and attr is not GenericDevice:
                device_classes.append(attr)

                class_name = attr.__name__
                gui_name = getattr(attr, "gui_name", None)
                try:
                    gui_icon = self.get_icon_location(getattr(attr, "gui_icon", None))
                except Exception as e:
                    continue
                gui_tags = getattr(attr, "gui_tags", None)
                module_path = Path(module.__file__)

                try:
                    # Try to calculate the relative path
                    if module.__name__.startswith("qureed"):
                        module_name = module.__name__
                    else:
                        relative_path = module_path.relative_to(project_root).with_suffix("")
                        module_name = ".".join(relative_path.parts)
                except ValueError:
                    # Fallback to using the absolute path if outside project_root
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
                attr_instance = attr()
                properties = BM.serialize_properties(attr_instance.properties)
                del attr_instance
                device_message = server_pb2.Device(
                    class_name=class_name,
                    gui_name=gui_name,
                    module_class=f"{module_name}.{class_name}",
                    ports=ports,
                    gui_tags=gui_tags,
                    device_properties=server_pb2.DeviceProperties(
                        properties=properties),
                    icon=server_pb2.GetIconResponse(
                        abs_path=gui_icon
                    )
                )

                device_messages.append(device_message)

        return device_messages

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
            traceback.print_exc()
            print(f"Module '{module_name}' not found.")
            print(sys.path)
            print(sys.executable)
            raise
        except AttributeError:
            traceback.print_exc()
            print(f"Class '{class_name}' not found in module '{module_name}'.")
            raise
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred: {e}")
            raise
