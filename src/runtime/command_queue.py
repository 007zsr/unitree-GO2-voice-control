from __future__ import annotations

from collections import deque
from threading import Condition, Event, Thread
from typing import Any

from src.commands.command_catalog import CommandCatalog
from src.logging.event_logger import EventLogger
from src.models import CommandPlan, RobotActionResult, RobotCommand
from src.robot.base_adapter import BaseRobotAdapter


class CommandQueue:
    def __init__(
        self,
        adapter: BaseRobotAdapter,
        catalog: CommandCatalog,
        logger: EventLogger,
        config: dict[str, Any] | None = None,
    ):
        self.adapter = adapter
        self.catalog = catalog
        self.logger = logger
        self.config = config or {}
        self.status: dict[str, str] = {}
        self.results: dict[str, RobotActionResult] = {}
        self._pending: deque[RobotCommand] = deque()
        self._condition = Condition()
        self._shutdown = False
        self._worker: Thread | None = None
        self._current: RobotCommand | None = None
        self._cancel_event: Event | None = None

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._worker = Thread(target=self._run, name="go2-command-queue", daemon=True)
        self._worker.start()

    def submit(self, command: RobotCommand) -> str:
        if command.intent == "stop":
            return self.submit_stop(command)
        with self._condition:
            if self._current is not None:
                current_spec = self.catalog.get(self._current.intent)
                if current_spec and current_spec.can_interrupt:
                    if self._cancel_event:
                        self._cancel_event.set()
                    self.logger.emergency_stop(
                        self._current.command_id,
                        "new interrupting command arrived",
                        next_command_id=command.command_id,
                    )
                else:
                    self.status[command.command_id] = "rejected"
                    return "rejected_busy"
            self.status[command.command_id] = "safety_checked"
            self._pending.append(command)
            self._condition.notify()
            return "queued"

    def submit_plan(self, plan: CommandPlan) -> list[str]:
        statuses: list[str] = []
        for command in plan.commands:
            status = self.submit(command)
            statuses.append(status)
            if status.startswith("rejected") or command.intent == "stop":
                break
        return statuses

    def submit_stop(self, command: RobotCommand) -> str:
        with self._condition:
            if self._cancel_event:
                self._cancel_event.set()
            for pending in list(self._pending):
                self.status[pending.command_id] = "rejected"
            self._pending.clear()
            self.status[command.command_id] = "safety_checked"
            self._pending.appendleft(command)
            self._condition.notify()
            self.logger.emergency_stop(command.command_id, "stop command submitted")
            return "emergency_queued"

    def wait_until_idle(self, timeout_sec: float = 10.0) -> bool:
        import time

        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            with self._condition:
                if self._current is None and not self._pending:
                    return True
            time.sleep(0.05)
        return False

    def current_command_id(self) -> str | None:
        with self._condition:
            return self._current.command_id if self._current else None

    def pending_count(self) -> int:
        with self._condition:
            return len(self._pending)

    def shutdown(self) -> None:
        with self._condition:
            self._shutdown = True
            if self._cancel_event:
                self._cancel_event.set()
            self._condition.notify_all()
        if self._worker:
            self._worker.join(timeout=3)

    def _run(self) -> None:
        while True:
            with self._condition:
                while not self._pending and not self._shutdown:
                    self._condition.wait(timeout=0.1)
                if self._shutdown:
                    return
                command = self._pending.popleft()
                self._current = command
                self._cancel_event = Event()
                self.status[command.command_id] = "executing"
            try:
                result = self.adapter.execute(command, self._cancel_event)
                self.results[command.command_id] = result
                if self._cancel_event.is_set() or command.intent == "stop":
                    self.status[command.command_id] = "stopped"
                elif result.success:
                    self.status[command.command_id] = "completed"
                else:
                    self.status[command.command_id] = "rejected"
                    self._clear_pending_after_failure(command, result.message)
                self.logger.log(
                    "go2",
                    "adapter_execute_result",
                    command_id=command.command_id,
                    command=command.to_dict(),
                    result=result.to_dict(),
                    queue_status=self.status[command.command_id],
                )
            except Exception as exc:
                self.status[command.command_id] = "rejected"
                self.logger.exception(
                    "go2",
                    "adapter_execute_exception",
                    exc,
                    command_id=command.command_id,
                    command=command.to_dict(),
                )
                self._safe_stop(command.command_id, "adapter exception")
                self._clear_pending_after_failure(command, str(exc))
            finally:
                with self._condition:
                    self._current = None
                    self._cancel_event = None
                    self._condition.notify_all()

    def _safe_stop(self, command_id: str, reason: str) -> None:
        try:
            result = self.adapter.stop(command_id)
            self.logger.emergency_stop(command_id, reason, result=result.to_dict())
        except Exception as exc:
            self.logger.exception("go2", "safe_stop_failed", exc, command_id=command_id)

    def _clear_pending_after_failure(self, command: RobotCommand, reason: str) -> None:
        with self._condition:
            for pending in list(self._pending):
                self.status[pending.command_id] = "rejected"
            self._pending.clear()
        self.logger.log(
            "session",
            "queue_cleared_after_failure",
            command_id=command.command_id,
            reason=reason,
        )
