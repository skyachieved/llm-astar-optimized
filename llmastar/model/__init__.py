from .chatgpt import ChatGPT


def __getattr__(name):
    # Llama3 pulls in torch/transformers; import it only when it is actually requested.
    if name == "Llama3":
        from .llama3 import Llama3
        return Llama3
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
