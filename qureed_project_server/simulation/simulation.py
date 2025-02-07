import argparse
import asyncio
import json
import time
from pathlib import Path

from qureed.simulation import Simulation

from qureed_project_server.client import GrpcClient
from qureed_project_server import server_pb2
from qureed_project_server.logic_modules import (
    LogicModuleEnum, LogicModuleHandler
)

LMH = LogicModuleHandler()


class JSONExecution():
    def __init__(self, scheme, duration):
        self.scheme = scheme
        self.duration = duration
        self.devices = []
        self.connections = []


    def assemble_simulation(self):
        BM = LMH.get_logic(LogicModuleEnum.BOARD_MANAGER)
        BM.open_scheme(self.scheme)
        self.devices = BM.devices.copy()
        self.connections = BM.connection.copy()

    def run(self):
        try:
            sim = Simulation.get_instance()
            sim.run_des(self.duration)
        except Exception as e:
            print("Something went wrong")
            print(e)




async def send_test_log(port:int):
    client = GrpcClient(server_address=f"127.0.0.1:{port}")
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--scheme", type=str, required=True)
    parser.add_argument("--base-dir", type=str, required=True)
    parser.add_argument("--duration", type=int, default=1)
    args = parser.parse_args()

    VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
    VM.path = Path(args.base_dir) / ".venv"

    JE = JSONExecution(scheme=args.scheme, duration=args.duration)
    JE.assemble_simulation()

if __name__ == "__main__":
    main()
