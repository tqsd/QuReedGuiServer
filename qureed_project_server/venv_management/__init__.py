from .venv_manager import VenvManager
from .venv_pb2 import VenvManagementServicer

# Automatically intitialize singleton modules
VM = VenvManager()
