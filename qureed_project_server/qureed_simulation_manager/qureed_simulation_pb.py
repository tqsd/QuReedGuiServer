import traceback
import time

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
        try:
            SiM = LMH.get_logic(LogicModuleEnum.SIMULATION_MANAGER)
            SiM.start_simulation(request.scheme_path, request.simulation_id)
            return server_pb2.StartSimulationResponse(
                status="success"
            )
        except Exception as e:
            print("AN ERROR")
            traceback.print_exc()
            return server_pb2.StartSimulationResponse(
                status="failure",
                message=f"Simulation Starting failed due to: {e}"
            )

    def StopSimulation(self, request, context):
        print("Stopping the simulation")
        try:
            SiM = LMH.get_logic(LogicModuleEnum.SIMULATION_MANAGER)
            SiM.stop_simulation()
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
        print("SOME LOGS SUBMITTED")
        SiM = LMH.get_logic(LogicModuleEnum.SIMULATION_MANAGER)
        self.send_log_to_gui(request.log)
        print("Tried to send the logs to the gui")

    def SimulationLogStream(self, request, context):
        print("Subscribing to logs")
        self.client_context = context
        try: 
            while context.is_active():
                time.sleep(1)
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            self.client_context = None

    def send_log_to_gui(self, message):
        print("send_logs_to_gui")
        if not hasattr(self, "client_context"):
            print("No GUI Client context")
            return
        print("GUI IS REQUESTING LOGS")

        self.client_context.write(
            server_pb2.SimulationLogStreamResponse(
                log=message
            )
        )

