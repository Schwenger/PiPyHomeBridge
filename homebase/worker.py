"Module contains naught but an abstract base class for general workers."

from abc import ABC, abstractmethod


class Worker(ABC):
    "Abstract base class for a worker in the smart home app."

    def run(self):
        "Starts running the worker; will never return."
        self._run()

    @abstractmethod
    def _run(self):
        "Starts running the worker; will never return."
