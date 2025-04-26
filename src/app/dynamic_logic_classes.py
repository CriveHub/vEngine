from abc import ABC, abstractmethod

class LogicBlock(ABC):
    """Base class for dynamic logic blocks."""

    @abstractmethod
    def execute(self, context):
        """Execute the logic block with given context."""
        pass

# Existing dynamic logic classes below can inherit from LogicBlock

import asyncio
from global_context import global_data_pool

class MyBlock:
    version = "1.0"
    def __init__(self, name):
        self.name = name
        self.counter = 0

    async def execute(self):
        self.counter += 1
        try:
            value = global_data_pool.get_variable("profinet_value")
        except Exception as e:
            value = f"Errore: {e}"
        print(f"{self.name} eseguito, contatore: {self.counter}, valore dal driver: {value}")

    def get_state(self):
        return {"counter": self.counter}

    def set_state(self, state):
        self.counter = state.get("counter", 0)

logic_blocks = {
    "block1": MyBlock("Block1")
}

def swap_logic(namespace: str, version: str):
    """Hot-swap logic blocks by namespace and version tag (stub)."""
    # TODO: implement secure reload of logic modules by namespace/version
    pass


import importlib

def swap_logic(namespace: str, module_name: str):
    """Hot-swap logic module by name, reloading its code."""
    try:
        module = importlib.import_module(namespace + '.' + module_name)
        importlib.reload(module)
    except ImportError:
        raise
