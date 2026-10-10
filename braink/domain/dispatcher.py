"""Agentic work module dispatch adapter.

Maps BRAINK_SERVER deployment queue to AGENTIC_AI_SERVER function generation.
Implements PAIR.BRAINK_TO_AGENTIC_AI from R12 genome execution map.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class ModuleType(str, Enum):
    """Work module classification."""

    RUNTIME = "runtime"
    SERVICE = "service"
    ADAPTER = "adapter"
    VALIDATOR = "validator"
    COMPOSITOR = "compositor"


class DispatchState(str, Enum):
    """Dispatch lifecycle state."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkModule:
    """Agentic work module definition."""

    module_id: str
    module_type: ModuleType
    module_name: str
    purpose: str
    input_spec: Dict[str, Any]
    output_spec: Dict[str, Any]
    dependencies: List[str]
    executor: str
    test_requirements: List[str]


@dataclass
class DispatchRecord:
    """Dispatch execution record."""

    dispatch_id: str
    server_from: str
    server_to: str
    module: WorkModule
    state: DispatchState
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkModuleDispatcher:
    """Dispatches work modules from BRAINK_SERVER to AGENTIC_AI_SERVER."""

    def __init__(self, executors: Optional[Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]] = None) -> None:
        """Initialize dispatcher."""
        self._modules: Dict[str, WorkModule] = {}
        self._executors = dict(executors or {})
        if any(not callable(fn) for fn in self._executors.values()):
            raise ValueError("Executor bindings must be callable")
        self._dispatch_queue: List[DispatchRecord] = []
        self._completed: List[DispatchRecord] = []
        self._failed: List[DispatchRecord] = []

    def register_module(self, module: WorkModule) -> None:
        """Register a work module for potential dispatch.

        Args:
            module: WorkModule to register
        """
        if not module.module_id or not module.executor:
            raise ValueError("Module identity and executor binding are required")
        if module.module_id in self._modules:
            raise ValueError("Module identity already registered")
        self._modules[module.module_id] = module

    def dispatch(
        self,
        dispatch_id: str,
        module: WorkModule,
        input_data: Dict[str, Any],
        target_server: str = "AGENTIC_AI_SERVER",
    ) -> DispatchRecord:
        """Dispatch a work module to target server.

        Args:
            dispatch_id: Unique dispatch identifier
            module: WorkModule to dispatch
            input_data: Input data for module execution
            target_server: Target server (default AGENTIC_AI_SERVER)

        Returns:
            DispatchRecord tracking this dispatch
        """
        if not dispatch_id or self.get_dispatch_status(dispatch_id) is not None:
            raise ValueError("Dispatch identity must be unique and nonempty")
        if self._modules.get(module.module_id) != module:
            raise ValueError("Module must match its registered definition")
        if not isinstance(input_data, dict):
            raise ValueError("Dispatch input must be a mapping")
        record = DispatchRecord(
            dispatch_id=dispatch_id,
            server_from="BRAINK_SERVER",
            server_to=target_server,
            module=module,
            state=DispatchState.ASSIGNED,
            input_data=input_data,
        )
        self._dispatch_queue.append(record)
        return record

    def execute_dispatch(self, dispatch_id: str) -> Optional[DispatchRecord]:
        """Execute a dispatched work module.

        Args:
            dispatch_id: ID of dispatch to execute

        Returns:
            Updated DispatchRecord or None if not found
        """
        for record in self._dispatch_queue:
            if record.dispatch_id == dispatch_id:
                record.state = DispatchState.EXECUTING
                try:
                    executor = self._executors.get(record.module.executor)
                    if executor is None:
                        raise ValueError("No configured executor for this module")
                    missing = [dependency for dependency in record.module.dependencies
                               if not any(done.module.module_id == dependency for done in self._completed)]
                    if missing:
                        raise ValueError("Uncompleted module dependencies")
                    output = executor(record.input_data)
                    if not isinstance(output, dict):
                        raise ValueError("Executor output must be a mapping")
                    record.output_data = output
                    record.state = DispatchState.COMPLETED
                    self._completed.append(record)
                except Exception:
                    # Do not expose credentials or arbitrary executor exception text.
                    record.state = DispatchState.FAILED
                    record.error = "Executor unavailable, dependency unmet, or execution failed"
                    self._failed.append(record)
                self._dispatch_queue.remove(record)
                return record
        return None

    def get_dispatch_status(self, dispatch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a dispatch.

        Args:
            dispatch_id: ID of dispatch to check

        Returns:
            Dispatch status or None if not found
        """
        for record in self._dispatch_queue + self._completed + self._failed:
            if record.dispatch_id == dispatch_id:
                return asdict(record)
        return None
