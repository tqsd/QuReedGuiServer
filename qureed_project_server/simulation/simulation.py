import argparse
import threading
import asyncio
import json
import time
import traceback
from pathlib import Path

from qureed.simulation import Simulation
from qureed.extra.logging import set_logging_hook

from qureed_project_server.client import GrpcClient
from qureed_project_server import server_pb2
from qureed_project_server.logic_modules import (
    LogicModuleEnum, LogicModuleHandler
)

LMH = LogicModuleHandler()


class JSONExecution():
    def __init__(self, scheme, duration, port, simulation_id):
        self.scheme = scheme
        self.duration = duration
        self.grpc_client = None
        self.grpc_thread = None
        self.simulation_id = simulation_id
        self.devices = []
        self.connections = []

        def grpc_thread_func():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.grpc_client = GrpcClient(server_address=f"127.0.0.1:{port}")
            self.loop.run_forever()

        # Start the gRPC thread if not already running
        if self.grpc_thread is None:
            self.grpc_thread = threading.Thread(target=grpc_thread_func, daemon=True)
            self.grpc_thread.start()

        while self.grpc_client is None:
            time.sleep(0.1)  # Small delay to ensure it's created

    def assemble_simulation(self):
        BM = LMH.get_logic(LogicModuleEnum.BOARD_MANAGER)
        BM.open_scheme(self.scheme)

    def run(self):
        try:
            sim = Simulation.get_instance()
            sim.run_des(
                self.duration
                )
        except Exception as e:
            traceback.print_exc()
            print("Something went wrong")
            print(e)

    def run_in_loop(self, coro):
        """
        Utility method to run a coroutine in the correct event loop.
        """
        if self.loop is None:
            raise RuntimeError("Event loop is not initialized. Did you call start()?")

        # Submit the coroutine to the correct loop
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()
 
    def send_logs(self, log_entry, *args, **kwargs):
        print("SHOULD SEND LOGS")
        key_translation = {
            "simulation_time":"simulation_timestamp",
            "timestamp":"timestamp",
            "message":"message",
            "logger":"log_type",
            "device_name":"device_name",
            "device_type":"device_type",
        }
        simulation_log_entry = {}
        for key, new_key in key_translation.items():
            if key in log_entry.keys():
                simulation_log_entry[new_key] = log_entry[key]
        simulation_log_entry["simulation_id"]=self.simulation_id
        print(simulation_log_entry)

        log_message = server_pb2.SimulationLog(
            **simulation_log_entry
        )

        async def submit_logs():
            response = await self.grpc_client.call(
                self.grpc_client.simulation_stub.SimulationLogSubmission,
                server_pb2.SubmitSimulationLogRequest(
                    log=log_message
                )
            )
        
        self.run_in_loop(submit_logs())
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        print(log_message)



async def send_test_log(port:int):
    print("SHOULD SEND?")
    try:
        log_message = server_pb2.SimulationLog(
            timestamp=float(time.time()),
            simulation_timestamp=0.0,
            log_type="INFO",
            device_name="TEST DEVICE",
            message=f"This is only a test message"
        )
        print(log_message)
        response = await client.call(
            client.simulation_stub.SimulationLogSubmission,
            server_pb2.SubmitSimulationLogRequest(
                log=log_message
            )
        )
        print(response)
    finally:
        await client.close()

def main():
    """
    Main function, executes the given simulation
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--scheme", type=str, required=True)
    parser.add_argument("--base-dir", type=str, required=True)
    parser.add_argument("--duration", type=int, default=1)
    parser.add_argument("--simulation-id", type=str)
    args = parser.parse_args()

    VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
    VM.path = Path(args.base_dir) / ".venv"

    #client = GrpcClient(server_address=f"127.0.0.1:{args.port}")


    JE = JSONExecution(
        scheme=args.scheme, 
        duration=args.duration,
        port=args.port,
        simulation_id=args.simulation_id
        )
    set_logging_hook(JE.send_logs)
    JE.assemble_simulation()

    JE.run()

if __name__ == "__main__":
    main()
