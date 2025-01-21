from concurrent import futures
import argparse
import grpc
import server_pb2
import server_pb2_grpc
import venv


class ServerManagementServicer(server_pb2_grpc.ServerManagementServicer):
    def Status(self, request, context):
        return server_pb2.StatusResponse(status="success", message="server is running")
    
    def Terminate(self, request, context):
        return server_pb2.TerminateResponse(status="success", message="Server terminated")

    
class VenvManagementServicer(server_pb2_grpc.VenvManagementServicer):
    def Freeze(self, request, context):
        return server_pb2.FreezeResponse(status="success", packages="package1==1.0\npackage2==2.0")

    def Install(self, request, context):
        return server_pb2.InstallResponse(status="success", message=f"Installed {request.package}")

    def Uninstall(self, request, context):
        return server_pb2.UninstallResponse(status="success", message=f"Uninstalled {request.package}")
    
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
