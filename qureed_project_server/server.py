from concurrent import futures
import argparse
import grpc
import server_pb2
import server_pb2_grpc
import venv

from qureed_project_server.venv_management import VenvManagementServicer
from qureed_project_server.server_management import ServerManagementServicer

    
    
def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add services to the server
    server_pb2_grpc.add_ServerManagementServicer_to_server(ServerManagementServicer(server), server)
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
