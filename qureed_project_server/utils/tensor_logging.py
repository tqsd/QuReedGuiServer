import numpy as np
from qureed_project_server.server_pb2 import Tensor

def message_from_tensor(tensor: np.ndarray) -> Tensor:
    """
    Converts a NumPy tensor (real or complex) to a gRPC Tensor message.
    If the tensor is real, the imaginary part is set to zeros.
    """
    tensor = np.array(tensor)
    real_values = tensor.real.flatten().tolist()  # Extract real part
    imag_values = tensor.imag.flatten().tolist() if np.iscomplexobj(tensor) else [0.0] * tensor.size  # Handle real tensors
    shape = list(tensor.shape)  # Store tensor dimensions
    ten = Tensor(real_values=real_values, imag_values=imag_values, shape=shape)

    new_tensor = tensor_from_message(ten)
    return ten

def tensor_from_message(tensor_message: Tensor) -> np.ndarray:
    """
    Converts a gRPC Tensor message back into a NumPy tensor.
    If all imaginary values are zero, returns a real tensor.
    """
    try:
        shape = tuple(tensor_message.shape)  # Get tensor shape
        real_part = np.array(tensor_message.real_values).reshape(shape)
        imag_part = np.array(tensor_message.imag_values).reshape(shape)

        # If all imaginary values are zero, return a real tensor
        if np.all(imag_part == 0):
            return real_part
        return real_part + 1j * imag_part  # Return complex tensor
    except Exception as e:
        print(e)
        return np.array([0])