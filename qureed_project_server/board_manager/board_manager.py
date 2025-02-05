import json
from pathlib import Path
from qureed_project_server.logic_modules import (
    LogicModuleEnum,
    LogicModuleHandler
)
from qureed_project_server import server_pb2
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import MessageToDict

LMH = LogicModuleHandler()


class DeviceConnectionError(Exception):
    """Raised when an invalid device connection is requested"""


class NoSchemeOpenedError(Exception):
    """Raised when no scheme is opened, but is expected to be"""


class BoardManager:
    """
    BoardManager (Singleton) manages the board

    BoardManager opens (loads) a scheme and saves the scheme. Additionally it
    manages the addition and removal of devices and connections.

    Attributes:
    opened_scheme (Optional[str]): Currently opened scheme
        (None if no scheme is opened)
    initialized (bool): Initialization flag for the Singleton pattern
    devices (list): List of devices on the current board
    connections (list): List of connections on the current board

    Methods:
    open_scheme(board:str): Opens a new scheme
    save_scheme(request:SaveBoardRequest): Saves the scheme, gets
        positions from the given request
    serialize_properties(properties:dict): Serialize the properties of a
        device before saving them
    deserialize_properties (properties:dict,
                            custom_type_mapping:Optional[dict]):
        Deserialize the properties when loading a board
    get_device(uuid:str): Gets a device from the current board
    add_device(device_msg:Device): Creates a new device on the current board
    connect_devices(connect_request:ConnectDevicesRequest): Creates
        a connection between two ports on two devices
    disconnect_devices(disconnect_request:DisconnectDevicesRequest): Removes
        specified connection between two devices
    remove_device(device:Device): Removes specified device from the
        current board
    update_device_properties(device:Device): Updates the properties of an
        existing device on the board

    Examples:
    ---------
    Example of how to use the class
        >>> from qureed_project_server.logic_modules import (
        >>> LogicModuleEnum,LogicModuleHandler)
        >>> BM = LogicModuleEnum().get_logic(LogicModuleEnum.BOARD_MANAGER)
        >>> BM.open_scheme("main.json")
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BoardManager, cls).__new__(
                cls, *args, **kwargs
            )
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            LMH.register(LogicModuleEnum.BOARD_MANAGER, self)
            self.opened_scheme = None
            self.initialized = True
            self.devices = []
            self.connections = []

    def open_scheme(
            self,
            board: str
            ) -> tuple[list[server_pb2.Device], list[server_pb2.Connection]]:
        """
        Opens a given scheme, this means that old devices and connectinos are
        erased and new ones are loaded. It returns the devices and connections
        of the new scheme.

        Parameters:
        -----------
        board (str): Relative location of the scheme within a project

        Returns:
        --------
        tuple[list[Device], list[Connection]]: tuple with lists of
        devices and connections respectively
        """
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        project_root = Path(VM.path).parents[0]
        scheme_name = project_root / board
        with open(scheme_name, "r") as f:
            scheme = json.load(f)

        self.opened_scheme = scheme_name
        self.devices = []
        self.connections = []
        devices_msg = []
        connections_msg = []

        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)

        for device_descriptor in scheme.get("devices", []):
            device_class = QM.get_class(device_descriptor["device"])
            device = device_class(uid=device_descriptor["uuid"])
            if "properties" in device_descriptor:
                device.properties = device_descriptor["properties"]

            self.devices.append(device)
            device_msg = QM.create_device_message(device_class)
            device_msg.uuid = device_descriptor["uuid"]
            if "properties" in device_descriptor:
                # Create a Struct object and populate it
                properties = Struct()
                properties.update(device_descriptor["properties"])

                # Assign it to the device_properties field
                device_msg.device_properties.properties.CopyFrom(properties)
                device_msg.location.extend(device_descriptor["location"])
                devices_msg.append(device_msg)

        for signal_descriptor in scheme.get("connections", []):
            signal_class = QM.get_class(signal_descriptor["signal"])
            signal = signal_class()
            device1 = self.get_device(
                signal_descriptor["conn"][0]["device_uuid"])
            device2 = self.get_device(
                signal_descriptor["conn"][1]["device_uuid"])
            device1.register_signal(
                signal=signal,
                port_label=signal_descriptor["conn"][0]["port"]
                )
            device2.register_signal(
                signal=signal,
                port_label=signal_descriptor["conn"][1]["port"]
                )
            self.connections.append(signal)
            connection_msg = server_pb2.Connection(
                device_one_uuid=device1.ref.uuid,
                device_two_uuid=device2.ref.uuid,
                device_one_port_label=signal_descriptor["conn"][0]["port"],
                device_two_port_label=signal_descriptor["conn"][1]["port"],
                signal=signal_descriptor["signal"]
                )
            connections_msg.append(connection_msg)
        return devices_msg, connections_msg

    def save_scheme(self, request: server_pb2.SaveBoardRequest) -> None:
        """
        Saves the currently opened scheme, the positions of the
        devices on the board are compiled from the request.

        Parameters:
        -----------
        request (SaveBoardRequest): the request for the saving
        of the board, the request includes the positions of the
        devices
        """
        json_file_descriptor = {
            "devices": [],
            "connections": []
        }
        for device in request.devices:
            dev_instance = self.get_device(device.uuid)
            dev_descriptor = {
                "device": device.module_class,
                "location": list(device.location),
                "uuid": device.uuid,
                "properties": self.serialize_properties(
                    dev_instance.properties),
                }
            json_file_descriptor["devices"].append(dev_descriptor)

        for signal in self.connections:
            signal_descriptor = {
                "signal": f"{type(signal).__module__}.{type(signal).__name__}",
                "conn": []
                }
            for port in signal.ports:
                port_descriptor = {
                    "device_uuid": port.device.ref.uuid,
                    "port": port.label
                    }
                signal_descriptor["conn"].append(port_descriptor)
            json_file_descriptor["connections"].append(signal_descriptor)

        with open(self.opened_scheme, "w") as json_file:
            json.dump(json_file_descriptor, json_file, indent=2)

    def serialize_properties(self, properties: dict) -> dict:
        """
        Recursively serialize the given properties. Turns the types
        into strings. (e.g. int -> 'int')

        Parameters:
        -----------
        properties (dict): Properties of a device

        Returns:
        --------
        dict: Serialized properties
        """
        if isinstance(properties, dict):
            return {k: self.serialize_properties(v) for
                    k, v in properties.items()}
        elif isinstance(properties, type):
            return properties.__name__
        elif isinstance(properties, object):
            return str(properties)
        return properties

    def deserialize_properties(
            self,
            properties: dict,
            custom_type_mapping: dict = None) -> dict:
        """
        Deserialize properties (e.g. "str" -> str)

        Parameters:
        -----------
        properties (dict): properties to deserialize
        custom_type_mappind (Optional[dict]): additional
            type mapping

        Returns:
        --------
        dict: Deserialized properties
        """
        if custom_type_mapping is None:
            custom_type_mapping = {}

        default_type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "NoneType": type(None),
        }

        type_mapping = {**default_type_mapping, **custom_type_mapping}

        def deserialize_value(value):
            if isinstance(value, dict):
                return {k: deserialize_value(v) for k, v in value.items()}
            elif isinstance(value, str) and value in type_mapping:
                return type_mapping[value]
            return value

        return deserialize_value(properties)

    def get_device(self, uuid: str) -> object:
        """
        Gets the device instance from the current board

        Parameters:
        uuid (str): UUID of the device which is requested

        Returns:
        --------
        device: Device with the UUID if found

        Raises:
        -------
        Exception: if device is not found
        """
        filtered_devices = [d for d in self.devices if d.ref.uuid == uuid]
        if len(filtered_devices) == 1:
            return filtered_devices[0]
        else:
            raise Exception("Device Not found on the current board")

    def add_device(self, device_msg: server_pb2.Device) -> str:
        """
        Adds a device to a currently opened board, raises an
        Exception if no board is opened

        Parameters:
        -----------
        device_msg (Device): device to be added

        Returns:
        --------
        str: uuid of the newly created device

        Raises:
        -------
        NoSchemeOpenedError
            If no scheme is currently opened
        """
        if self.opened_scheme is None:
            raise NoSchemeOpenedError("No Scheme is currently opened")
        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)
        device_class = QM.get_class(device_msg.module_class)
        device = device_class(uid=device_msg.uuid)
        uuid = device.ref.uuid
        self.devices.append(device)
        return str(uuid)

    def connect_devices(
            self,
            connect_request: server_pb2.ConnectDevicesRequest) -> None:
        """
        Connects two existing devices, The connection (devices and ports) is
        specified in the connect_request.

        Parameters:
        -----------
        connect_request (ConnectDevicesRequest): Request defining the desired
            connection.
        """
        dev1 = self.get_device(connect_request.device_uuid_1)
        dev2 = self.get_device(connect_request.device_uuid_2)

        if dev1 == dev2:
            raise Exception("Cannot connect to self!")

        sig_cls_1 = dev1.ports[connect_request.device_port_1].signal_type
        sig_cls_2 = dev2.ports[connect_request.device_port_2].signal_type
        sig_cls = None
        if issubclass(sig_cls_1, sig_cls_2):
            sig_cls = sig_cls_1
        elif issubclass(sig_cls_2, sig_cls_1):
            sig_cls = sig_cls_2
        else:
            raise Exception("Signals Hierarchies Diverge")

        sig = sig_cls()
        dev1.register_signal(
            signal=sig,
            port_label=connect_request.device_port_1)
        dev2.register_signal(
            signal=sig,
            port_label=connect_request.device_port_2)
        self.connections.append(sig)

    def disconnect_devices(
            self,
            disconnect_request: server_pb2.DisconnectDevicesRequest
            ) -> None:
        """
        Disconnect the devices as given in the disconnect_request

        Parameters:
        -----------
        disconnect_request (DisconnectDevicesRequest): The request to
            disconnect the devices.

        Raises:
        -------
        DeviceConnectionError
            If attempting to disconnect a device from itself or if multile
            signals per port are not yet supported
        """

        dev1 = self.get_device(disconnect_request.device_uuid_1)
        dev2 = self.get_device(disconnect_request.device_uuid_2)

        if dev1 == dev2:
            raise DeviceConnectionError("Cannot disconnect from self!")

        sig1 = dev1.ports[disconnect_request.device_port_1].signal
        sig2 = dev2.ports[disconnect_request.device_port_2].signal

        if not sig1 == sig2:
            raise DeviceConnectionError(
                "Multiple signals per port not yet supported!"
            )

        for p in sig1.ports:
            p.signal = None
        self.connections.remove(sig1)

    def remove_device(self, device_uuid: str) -> None:
        """
        Removes a device from the board

        Parameters:
        -----------
        device_uuid (str): the uuid of the device to be removed
        """
        dev = self.get_device(device_uuid)
        self.devices.remove(dev)

    def update_device_properties(self, device: server_pb2.Device) -> None:
        """
        Updates the properties of the device

        Parameters:
        -----------
        device (Device): A device message with new properties
        """
        dev = self.get_device(device.uuid)
        new_properties = MessageToDict(device.device_properties.properties)

        for key, item in new_properties.items():
            if "value" in item:
                value = item["value"]
                if item['type'] == "int":
                    value = int(value)
                dev.set_property(key, value)
