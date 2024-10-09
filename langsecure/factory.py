# langsecure/factory.py

from typing import Callable, Dict, Type, Union

ImplementorsRegistry: Dict[str, Union[Type, Callable]] = {}

def register(id: str, implementor: Union[Type, Callable]):
    ImplementorsRegistry[id] = implementor

def get(id: str, if_not_found: str = "ignore"):
    implementor = ImplementorsRegistry.get(id)
    if implementor is None and if_not_found == "raise":
        raise ValueError(f"No implementor registered with name: {id}")
    return implementor
