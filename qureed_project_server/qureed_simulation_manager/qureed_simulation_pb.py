import traceback

from qureed_project_server import server_pb2_grpc, server_pb2
from qureed_project_server.logic_modules import (
    LogicModuleEnum, LogicModuleHandler
)

LMH = LogicModuleHandler()

class QuReedSimulationServicer(server_pb2_grpc.QuReedSimulationServicer):
    """
    QuReedSimulationServicer
    """

    def StartSimulation(self, request, context):
        print("Starting the simulation")
        try:
            SiM = LMH.get_logic(LogicModuleEnum.SIMULATION_MANAGER)
            SiM.start_simulation()
            return server_pb2.StartSimulationResponse(
                status="success"
            )
        except Exception as e:
            traceback.print_exc()
            return server_pb2.StartSimulationResponse(
                status="failure",
                message=f"Simulation Starting failed due to: {e}"
            )

    def StopSimulation(self, request, context):
        print("Stopping the simulation")
        try:
            SiM = LMH.get_logic(LogicModuleEnum.SIMULATION_MANAGER)
            return server_pb2.StopSimulationResponse(
                status="success"
            )
        except Exception as e:
            traceback.print_exc()
            return server_pb2.StopSimulationResponse(
                status="failure",
                message=f"Simulation Stopping failed due to: {e}"
            )
            
    def SimulationLogging(self, request, context):
        print(request)


    def SimulationLogSubmission(self, request, context):
        print(f"Received log submission: {request}")
        return server_pb2.SubmitSimulationLogResponse()