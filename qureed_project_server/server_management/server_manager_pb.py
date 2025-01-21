from qureed_project_server import server_pb2, server_pb2_grpc

class ServerManagementServicer(server_pb2_grpc.ServerManagementServicer):
    def Status(self, request, context):
        return server_pb2.StatusResponse(status="success", message="server is running")
    
    def Terminate(self, request, context):
        return server_pb2.TerminateResponse(status="success", message="Server terminated")
