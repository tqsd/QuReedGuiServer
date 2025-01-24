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
            return server_pb2.GetDevicesResponse(
                status="failure",
                message=f"Error in fetching the devices: {e}"
                )

    def OpenBoard(self, request, context):
        QM = LMH.get_logic(LogicModuleEnum.QUREED_MANAGER)
        try:
            devices_msg, connections_msg = QM.open_scheme(request.board)

            return server_pb2.OpenBoardResponse(
                status="success",
                devices=devices_msg,
                connections=connections_msg
                )
        except Exception as e:
            traceback.print_exc()
            return server_pb2.OpenBoardResponse(
                status="failure",
                message=f"Error when opening board {request.board} the devices: {e}"
                )
