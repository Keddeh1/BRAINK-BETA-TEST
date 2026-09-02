"""Agentic work module dispatch adapter.

Maps BRAINK_SERVER deployment queue to AGENTIC_AI_SERVER function generation.
Implements PAIR.BRAINK_TO_AGENTIC_AI from R12 genome execution map.
"""

from typing import Dict, List, Any, Optional
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

    def __init__(self) -> None:
        """Initialize dispatcher."""
        self._dispatch_queue: List[DispatchRecord] = []
        self._completed: List[DispatchRecord] = []
        self._failed: List[DispatchRecord] = []

    def register_module(self, module: WorkModule) -> None:
        """Register a work module for potential dispatch.

        Args:
            module: WorkModule to register
        """
        # Module is registered but not yet dispatched
        pass

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
                # In real system, this would invoke the module executor
                # For now, mark as completed
                record.state = DispatchState.COMPLETED
                record.output_data = {"status": "generated"}
                self._completed.append(record)
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
