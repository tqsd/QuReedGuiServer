from concurrent import futures
import argparse
import grpc
import server_pb2
import server_pb2_grpc
import venv

from qureed_project_server.venv_management import VenvManager


class ServerManagementServicer(server_pb2_grpc.ServerManagementServicer):
    def Status(self, request, context):
        return server_pb2.StatusResponse(status="success", message="server is running")
    
    def Terminate(self, request, context):
        return server_pb2.TerminateResponse(status="success", message="Server terminated")

    
class VenvManagementServicer(server_pb2_grpc.VenvManagementServicer):

    def Connect(self, request, context):
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
    
def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add services to the server
    server_pb2_grpc.add_ServerManagementServicer_to_server(ServerManagementServicer(), server)
    server_pb2_grpc.add_VenvManagementServicer_to_server(VenvManagementServicer(), server)
    
    # Bind to a port
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Server started on port {port}")
    server.wait_for_termination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    
    serve(args.port)
