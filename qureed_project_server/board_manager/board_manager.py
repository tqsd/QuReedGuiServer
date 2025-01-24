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

    def open_scheme(self, scheme):
        self.devices = []
        self.connections = []
        devices_msg = []
        connections_msg = []

        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)
        for device_descriptor in scheme["devices"]:
            device_class = QM.get_class(device_descriptor["device"])
            device = device_class(uid=device_descriptor["uuid"])
            if "properties" in device_descriptor:
                device.properties = device_descriptor["properties"]

            self.devices.append(device)
            device_msg = QM.create_device_message(device_class)
            print(device_msg)
            device_msg.uuid = device_descriptor["uuid"]
            if "properties" in device_descriptor:
                # Create a Struct object and populate it
                properties = Struct()
                properties.update(device_descriptor["properties"])

                # Assign it to the device_properties field
                device_msg.device_properties.properties.CopyFrom(properties)
                device_msg.location.extend(device_descriptor["location"])
                devices_msg.append(device_msg)

        for signal_descriptor in scheme["connections"]:
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
            connection_msg = server_pb2.Connection(
                device_one_uuid=device1.ref.uuid,
                device_two_uuid=device2.ref.uuid,
                device_one_port_label=signal_descriptor["conn"][0]["port"],
                device_two_port_label=signal_descriptor["conn"][1]["port"],
                signal=signal_descriptor["signal"]
                )
            connections_msg.append(connection_msg)
            
        return devices_msg, connections_msg 
    def get_device(self, uuid:str) -> object:
        filtered_devices = [d for d in self.devices if d.ref.uuid==uuid]
        if len(filtered_devices) == 1:
            return filtered_devices[0]
        else:
            raise Exception("Device Not found on the current board")
        
