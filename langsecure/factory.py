from typing import Callable, Dict, Type, Union, Literal

# Define a registry to hold class and function implementations
ImplementorsRegistry: Dict[str, Union[Type, Callable]] = {}

def implements(id: str):
    def decorator(implementor: Union[Type, Callable]):
        ImplementorsRegistry[id] = implementor
        return implementor
    return decorator

def get(id: str, if_not_found :Literal["ignore", "raise"]= "ignore"):
    implementor = ImplementorsRegistry.get(id, None)
    if implementor is None:
        if if_not_found == "raise":
            raise ValueError(f"No implementor registered with name: {id}")

    return implementor
