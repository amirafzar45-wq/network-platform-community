from abc import ABC, abstractmethod

class NetworkProvider(ABC):
    vendor = "generic"

    @abstractmethod
    def get_snapshot(self) -> dict: ...

    @abstractmethod
    def export_config(self) -> str: ...
