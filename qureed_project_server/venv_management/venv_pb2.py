from qureed_project_server import server_pb2_grpc, server_pb2
from qureed_project_server.venv_management.venv_manager import VenvManager

class VenvManagementServicer(server_pb2_grpc.VenvManagementServicer):
    """
    VenvManagementServicer implements the sevicer (as defined in
    the protos/server.proto). It defines all rpc gateways
    """

    def Connect(self, request, context):
        print("CLIENT IS ATTEMPTING TO CONNECT TO THIS SERVER")
        venv_manager = VenvManager()
        try:
            venv_manager.connect(request.venv_path)
            return server_pb2.VenvConnectResponse(
                status="success",
                message=f"Connected to {request.venv_path}")
        except Exception as e:
            return server_pb2.VenvConnectResponse(
                status="failure",
                message=f"Connection to venv failed due to error: {e}")
            

    def Freeze(self, request, context):
        venv_manager = VenvManager()
        if venv_manager.venv:
            try:
                return server_pb2.FreezeResponse(
                    status="success",
                    packages=venv_manager.freeze())
            except Exception as e:
                return server_pb2.FreezeResponse(
                    status="failure",
                    message=f"Freeze failed due to error: {e}")
                
        else:
            return server_pb2.FreezeResponse(status="failure", message="No venv connected")

    def Install(self, request, context):
        venv_manager = VenvManager()
        if venv_manager.venv:
            try:
                venv_manager.install(request.package)
                return server_pb2.InstallResponse(
                    status="success",
                    message=f"Succesfully installed: {request.package}")
            except Exception as e:
                return server_pb2.InstallResponse(
                    status="failure",
                    message=f"Installing {request.package} failed due to error: {e}")
        else:
            return server_pb2.InstallResponse(
                status="failure",
                message="No venv connected")

    def Uninstall(self, request, context):
        venv_manager = VenvManager()
        if venv_manager.venv:
            try:
                venv_manager.uninstall(request.package)
                return server_pb2.UninstallResponse(
                    status="success",
                    message=f"Package {request.package} succesfully uninstalled"
                    )
            except Exception as e:
                return server_pb2.UninstallResponse(
                    status="failure",
                    message=f"Package {request.package} not uninstalled due to error: {e}"
                    )
        else:
            return server_pb2.UninstallResponse(
                status="failure", message=f"No venv connected")
