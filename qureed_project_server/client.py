import grpc
import server_pb2
import server_pb2_grpc

def run():
    # Connect to the server
    with grpc.insecure_channel("localhost:50051") as channel:
        # Create stubs for the services
        server_stub = server_pb2_grpc.ServerManagementStub(channel)
        venv_stub = server_pb2_grpc.VenvManagementStub(channel)
        
        # Call ServerManagement Status
        status_response = server_stub.Status(server_pb2.StatusRequest())
        print(f"Status: {status_response.status}, Message: {status_response.message}")
        
        # Call VenvManagement Freeze
        freeze_response = venv_stub.Freeze(server_pb2.FreezeRequest())
        print(f"Freeze Packages:\n{freeze_response.packages}")

if __name__ == "__main__":
    run()
