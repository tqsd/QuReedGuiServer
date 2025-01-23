import grpc
import server_pb2
import server_pb2_grpc


def run():
    # Connect to the server
    with grpc.insecure_channel("localhost:50051") as channel:
        # Create stubs for the services
        server_stub = server_pb2_grpc.ServerManagementStub(channel)
        venv_stub = server_pb2_grpc.VenvManagementStub(channel)
        qm_stub = server_pb2_grpc.QuReedManagementStub(channel)
        
        # Connect to the Venv
        venv_connect_response = venv_stub.Connect(
            server_pb2.VenvConnectRequest(venv_path="/home/simon/tmp/c/.venv/"))
        print(venv_connect_response)
        
        
        # Call VenvManagement Freeze
        # freeze_response = venv_stub.Freeze(server_pb2.FreezeRequest())
        # print(f"Freeze Packages:\n{freeze_response.packages}")

        devices_response = qm_stub.GetDevices(server_pb2.GetDevicesRequest())
        print(devices_response)
        #server_terminate_response = server_stub.Terminate(server_pb2.TerminateRequest())
        #print(f"Server Terminate Response:\n{server_terminate_response}")


if __name__ == "__main__":
    run()
