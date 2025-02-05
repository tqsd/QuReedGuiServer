import asyncio
import grpc
from qureed_project_server import server_pb2, server_pb2_grpc


class GrpcClient:
    """
    GrpcClient for comuniction, this client exposes all servicers for the
    communication with the server.
    """
    def __init__(self, server_address):
        """
        Initializes the gRPC client.

        Args:
            server_address (str): Address of the gRPC server (e.g., "localhost:50051").
        """
        self.server_address = server_address
        self.channel = grpc.aio.insecure_channel(server_address)
        self.venv_stub = server_pb2_grpc.VenvManagementStub(self.channel)
        self.qm_stub = server_pb2_grpc.QuReedManagementStub(self.channel)
        self.server_stub = server_pb2_grpc.ServerManagementStub(self.channel)

    async def call(self, callable_function, message):
        """
        Executes a gRPC call asynchronously.

        Args:
            callable_function (callable): The gRPC stub method to execute.
            message: The protobuf message to send.

        Returns:
            str: The response from the gRPC server.
        """
        try:
            response = await callable_function(message)
            return response
        except grpc.aio.AioRpcError as e:
            return f"gRPC error: {e}"

    async def close(self):
        """Closes the gRPC channel."""
        await self.channel.close()


# Example Usage
async def main():
    client = GrpcClient("localhost:50051")

    # Call Connect using the generic method
    connect_response = await client.call(
        client.venv_stub.Connect,
        server_pb2.VenvConnectRequest(venv_path="/home/simon/tmp/c/.venv/")
    )
    print(connect_response)

    # Call GetDevices using the generic method
    devices_response = await client.call(
        client.qm_stub.GetDevices,
        server_pb2.GetDevicesRequest()
    )
    print(devices_response)

    # Close the client
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
