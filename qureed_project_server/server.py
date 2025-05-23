from concurrent import futures
import argparse
import grpc

from qureed_project_server import server_pb2_grpc
from qureed_project_server.venv_management import VenvManagementServicer
from qureed_project_server.server_management import ServerManagementServicer
from qureed_project_server.qureed_manager import QuReemManagementService
from qureed_project_server.qureed_simulation_manager import QuReedSimulationServicer
from qureed_project_server.logic_modules import (
    LogicModuleEnum, LogicModuleHandler
)



def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    SiM = LogicModuleHandler().get_logic(LogicModuleEnum.SIMULATION_MANAGER)
    sim_servicer = QuReedSimulationServicer()
    SiM.register_simulation_servicer(sim_servicer)
    # Add services to the server
    server_pb2_grpc.add_ServerManagementServicer_to_server(
        ServerManagementServicer(server), server
    )
    server_pb2_grpc.add_VenvManagementServicer_to_server(
        VenvManagementServicer(), server
    )
    server_pb2_grpc.add_QuReedManagementServicer_to_server(
        QuReemManagementService(), server
    )
    server_pb2_grpc.add_QuReedSimulationServicer_to_server(
        sim_servicer, server
    )

    # Bind to a port
    server.add_insecure_port(f"127.0.0.1:{port}")
    print(f"BINDING TO 127.0.0.1::{port}")

    SiM.set_port(port)
    server.start()
    print(f"Server started on port {port}")
    server.wait_for_termination()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    serve(args.port)


if __name__ == "__main__":
    main()
