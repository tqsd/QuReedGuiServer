import os
from pathlib import Path
import sys
import subprocess
import threading

from qureed_project_server.logic_modules import (
    LogicModuleEnum, LogicModuleHandler
)

LMH = LogicModuleHandler()

class SimulationAlreadyRunningError(Exception):
    """Only one simulation can be executed at one time"""


class PortNotSetError(Exception):
    """Raised if port accessed but not configured"""

class QuReedSimulationManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(QuReedSimulationManager, cls).__new__(
                cls, *args, **kwargs
                )
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            LMH.register(LogicModuleEnum.SIMULATION_MANAGER, self)
            self.initialized = True
            self.port = None
            self.running_simulation = None
            self.simulation_servicer = None 

    def set_port(self, port):
        self.port = port

    def poll_server_output(self):
        """
        Method that polls the server output and displays it in the
        stdout of the GUI process.
        """
        if self.running_simulation:
            def poll(process):
                try:
                    # Read stdout
                    for line in iter(process.stdout.readline, ""):
                        if line.strip():  # Print only non-empty lines
                            print(f"[SIM STDOUT] {line.strip()}")
                    # Read stderr
                    for line in iter(process.stderr.readline, ""):
                        if line.strip():
                            print(f"[SIM STDERR] {line.strip()}")
                finally:
                    print("SIMULATION STOPPED")
                    process.stdout.close()
                    process.stderr.close()

            # Start the thread
            output_thread = threading.Thread(
                target=poll, args=(self.running_simulation,), daemon=True
            )
            output_thread.start()

    def register_simulation_servicer(self, servicer):
        self.simulation_servicer = servicer


    def start_simulation(self, scheme:str, simulation_id:str, simulation_time:float):
        if self.running_simulation:
            raise SimulationAlreadyRunningError(
                "Only one simulation can be running at a time."
            )
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        cmd = "qureed_simulate.exe" if sys.platform == "win32" else "qureed_simulate"

        if VM.path is None or VM.path == "None":
            python_executable = Path(os.environ.get("QUREED_PY_EXE"))
            sim_executable = (python_executable.parent / cmd).resolve()
        else:
            sim_executable = path(vm.path) / cmd

        if VM.path is None or VM.path == "None":
            project_root = Path(os.environ.get("QUREED_CWD"))
        else:
            project_root = Path(VM.path).parents[0]


        if not python_executable.exists():
            raise FileNotFoundError(
                f"Executable not found {python_executable}"
            )
        if not self.port:
            raise PortNotSetError(
                f"Port was never set!"
            ) 
        base_command = [
            str(sim_executable),
            "--base-dir", str(project_root),
            "--port", str(self.port),
            "--scheme", scheme,
            "--simulation-id", simulation_id,
            "--duration", str(simulation_time)
        ]

        env = {
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "LC_ALL": "en_US.UTF-8",
            "PYTHONBUFFERED": "1"
        }

        if sys.platform == "win32":
            # On Windows, prepare a full command with chcp + run
            win_command = [
                "chcp 65001",
                "&&",  # correct: separate the commands
                " ".join(base_command)
            ]
            command = ["start", "cmd", "/k", " ".join(win_command) + " & exit"]
            shell = True
        else:
            # On Linux/macOS, no chcp needed, no shell
            command = base_command
            shell = False
        if sys.platform == "win32":
            command = ["start", "cmd", "/k", " ".join(command) + " & exit"]
        print(command)
        self.running_simulation = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            shell=shell,
            encoding="utf-8",
            env=env
        )
        print(" ".join(command))
        print("Simulation Subprocess started")
        self.poll_server_output()
        

    def log_submission(self, request):
        """
        Method handles the submission of logs
        """
        VM = LMH.get_logic(LogicModuleEnum.VENV_MANAGER)
        if self.simulation_servicer:
            self.simulation_servicer.send_log_to_gui(log)

    def handle_simulation_end(self):
        print("ENDING THE SIMULATION -------")
        self.running_simulation = None
