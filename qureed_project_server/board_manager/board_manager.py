from qureed_project_server.logic_modules import LogicModuleEnum,LogicModuleHandler

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

        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)
        for device_descriptor in scheme["devices"]:
            device_class = QM.get_class(device_descriptor["device"])
            device = device_class(uid=device_descriptor["uuid"])
            self.devices.append(device)

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
            
    def get_device(self, uuid:str) -> object:
        filtered_devices = [d for d in self.devices if d.ref.uuid==uuid]
        if len(filtered_devices) == 1:
            return filtered_devices[0]
        else:
            raise Exception("Device Not found on the current board")
        
