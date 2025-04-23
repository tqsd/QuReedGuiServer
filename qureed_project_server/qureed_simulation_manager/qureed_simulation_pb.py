import traceback
import queue
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
            SiM.start_simulation(request.scheme_path, request.simulation_id, request.simulation_time)
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
        pass

    def SimulationLogSubmission(self, request, context):
        SiM = LMH.get_logic(LogicModuleEnum.SIMULATION_MANAGER)
        if hasattr(self, "log_handler"):
            self.log_handler(request.log)


    def SimulationLogStream(self, request, context):
        log_queue = queue.Queue()

        def log_handler(message):
            log_queue.put(message)

        self.log_handler = log_handler

        try:
            while context.is_active():
                try:
                    log_message = log_queue.get(timeout=1)
                    yield server_pb2.SimulationLogStreamResponse(
                        log=log_message
                    )
                    if log_message.end:
                        SiM = LMH.get_logic(LogicModuleEnum.SIMULATION_MANAGER)
                        SiM.handle_simulation_end()
                        break
                except queue.Empty:
                    pass
        except Exception as e:
            print(f"Log streame error: {e}")
        finally:
            self.log_handler = None