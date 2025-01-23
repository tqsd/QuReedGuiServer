import traceback
from qureed_project_server import server_pb2_grpc, server_pb2
from qureed_project_server.logic_modules import LogicModuleHandler, LogicModuleEnum

LMH = LogicModuleHandler()

class QuReemManagementService(server_pb2_grpc.QuReedManagementServicer):

    def GetDevices(self, request, context):
        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)
        try:
            devices, message = QM.get_devices()
            # Convert to Protobuf message
            return server_pb2.GetDevicesResponse(
                status="success",
                devices=devices,
                message=message
            )
            
        except Exception as e:
            print("ERROR", e)
            return server_pb2.GetDevicesResponse(
                status="failure",
                message=f"Error in fetching the devices: {e}"
                )

        
