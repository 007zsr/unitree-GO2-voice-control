from __future__ import annotations

from abc import ABC, abstractmethod
from threading import Event

from src.models import RobotActionResult, RobotCommand, RobotState


class BaseRobotAdapter(ABC):
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> RobotState:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self, command: RobotCommand, cancel_event: Event | None = None
    ) -> RobotActionResult:
        raise NotImplementedError

    @abstractmethod
    def stop(self, command_id: str = "manual_stop") -> RobotActionResult:
        raise NotImplementedError
