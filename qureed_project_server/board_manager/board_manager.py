import json
from qureed_project_server.logic_modules import LogicModuleEnum,LogicModuleHandler
from qureed_project_server import server_pb2
from google.protobuf.struct_pb2 import Struct

LMH = LogicModuleHandler()

class BoardManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BoardManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
            
    def __init__(self):
        if not hasattr(self, "initialized"):
            LMH.register(LogicModuleEnum.BOARD_MANAGER, self)
            self.opened_scheme = None
            self.initialized = True
            self.devices = []
            self.connections = []

    def open_scheme(self, scheme_name, scheme):
        self.opened_scheme=scheme_name
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
            device1 = self.get_device(signal_descriptor["conn"][0]["device_uuid"])
            device2 = self.get_device(signal_descriptor["conn"][1]["device_uuid"])
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

    def save_scheme(self,  request:server_pb2.SaveBoardRequest):
        print("SAVING SCHEME")
        json_file_descriptor = {
            "devices":[],
            "connections":[]
        }
        for device in request.devices:
            dev_instance = self.get_device(device.uuid)
            dev_descriptor = {
                "device":device.module_class,
                "location":list(device.location),
                "uuid":device.uuid,
                "properties":self.serialize_properties(dev_instance.properties),
                }
            json_file_descriptor["devices"].append(dev_descriptor)

        for signal in self.connections:
            signal_descriptor = {
                "signal":f"{type(signal).__module__}.{type(signal).__name__}",
                "conn":[]
                }
            for port in signal.ports:
                port_descriptor = {
                    "device_uuid":port.device.ref.uuid,
                    "port":port.label
                    }
                signal_descriptor["conn"].append(port_descriptor)
            json_file_descriptor["connections"].append(signal_descriptor)

        with open(self.opened_scheme, "w") as json_file:
            json.dump(json_file_descriptor,json_file, indent=2)
        

    def serialize_properties(self, properties):
        if isinstance(properties, dict):
            return {k:self.serialize_properties(v) for k,v in properties.items()}
        elif isinstance(properties, type):
            return properties.__name__
        elif isinstance(properties,object):
            return str(properties)
        return properties

    def deserialize_properties(self, properties, custom_type_mapping=None):
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

        # Combine default and custom type mappings
        type_mapping = {**default_type_mapping, **custom_type_mapping}

        def deserialize_value(value):
            if isinstance(value, dict):
                # Recursively deserialize nested dictionaries
                return {k: deserialize_value(v) for k, v in value.items()}
            elif isinstance(value, str) and value in type_mapping:
                # Convert type name strings back into type objects
                return type_mapping[value]
            return value

        return deserialize_value(properties)
    
    def get_device(self, uuid:str) -> object:
        filtered_devices = [d for d in self.devices if d.ref.uuid==uuid]
        if len(filtered_devices) == 1:
            return filtered_devices[0]
        else:
            raise Exception("Device Not found on the current board")

    def add_device(self, device_msg):
        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)
        device_class = QM.get_class(device_msg.module_class)
        device = device_class(uid=device_msg.uuid)
        uuid = device.ref.uuid
        self.devices.append(device)
        return uuid

    def connect_devices(self, connect_request:server_pb2.ConnectDevicesRequest):
        """
        Connects the two devices on the board.
        """
        dev1=self.get_device(connect_request.device_uuid_1)
        dev2=self.get_device(connect_request.device_uuid_2)

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

        sig=sig_cls()
        dev1.register_signal(signal=sig, port_label=connect_request.device_port_1)
        dev2.register_signal(signal=sig, port_label=connect_request.device_port_2)
        self.connections.append(sig)

    def disconnect_devices(self, disconnect_request:server_pb2.DisconnectDevicesRequest):
        
        dev1=self.get_device(disconnect_request.device_uuid_1)
        dev2=self.get_device(disconnect_request.device_uuid_2)

        if dev1 == dev2:
            raise Exception("Cannot disconnect from self!")

        sig1 = dev1.ports[disconnect_request.device_port_1].signal
        sig2 = dev2.ports[disconnect_request.device_port_2].signal

        if not sig1 == sig2:
            raise Exception("Multiple signals per port not yet supported!")

        for p in sig1.ports:
            p.signal = None
        self.connections.remove(sig1)
        
        
