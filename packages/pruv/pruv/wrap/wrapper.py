"""Universal wrapper — one function wraps any AI agent, function, or workflow."""

from __future__ import annotations

import asyncio
import functools
import inspect
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from xycore import XYChain, XYReceipt, hash_state

from ..graph import Graph, GraphDiff
from ..scanner import scan as scan_dir
from .observers import ActionObserver, FileObserver, APIObserver


@dataclass
class WrappedResult:
    """Result from a wrapped operation."""

    output: Any
    chain: XYChain
    receipt: XYReceipt
    graph_before: Graph | None = None
    graph_after: Graph | None = None
    observer: ActionObserver | None = None

    @property
    def diff(self) -> GraphDiff | None:
        if self.graph_before and self.graph_after:
            return self.graph_before.diff(self.graph_after)
        return None

    @property
    def verified(self) -> bool:
        valid, _ = self.chain.verify()
        return valid

    @property
    def actions(self) -> list:
        """All observed actions during execution."""
        if self.observer:
            return self.observer.actions
        return []


class WrappedAgent:
    """A wrapped agent/function that produces XY chains."""

    def __init__(
        self,
        target: Any,
        *,
        chain_name: str | None = None,
        api_key: str | None = None,
        sign: bool = False,
        private_key: bytes | None = None,
        signer_id: str | None = None,
        scan_dir_path: str | None = None,
        approval_webhook: str | None = None,
        approval_operations: list[str] | None = None,
        approval_timeout: int = 300,
        auto_redact: bool = True,
    ) -> None:
        self.target = target
        self.chain_name = chain_name or getattr(target, "__name__", "wrapped")
        self.api_key = api_key
        self.sign = sign
        self.private_key = private_key
        self.signer_id = signer_id
        self.scan_dir_path = scan_dir_path
        self.approval_webhook = approval_webhook
        self.approval_operations = approval_operations or []
        self.approval_timeout = approval_timeout
        self.auto_redact = auto_redact

        # Approval gate (created lazily when webhook is provided)
        self._approval_gate = None
        if self.approval_webhook:
            from ..approval.gate import ApprovalGate
            self._approval_gate = ApprovalGate(
                webhook_url=self.approval_webhook,
                timeout=self.approval_timeout,
                operations=set(self.approval_operations) if self.approval_operations else None,
            )

    def _create_observer(self, chain: XYChain) -> ActionObserver:
        """Create an observer that records intermediate actions into the chain."""
        return ActionObserver(chain)

    def _create_file_observer(self, chain: XYChain) -> FileObserver:
        """Create a file observer for tracking file operations."""
        return FileObserver(chain)

    def _create_api_observer(self, chain: XYChain) -> APIObserver:
        """Create an API observer for tracking HTTP calls."""
        return APIObserver(chain)

    def run_sync(self, args: tuple, kwargs: dict) -> WrappedResult:
        """Execute the wrapped target synchronously and produce an XY chain."""
        task = str(args[0]) if args else "unknown"
        chain = XYChain(
            name=self.chain_name,
            auto_redact=self.auto_redact,
        )
        started = time.time()

        # Capture before state
        graph_before = None
        if self.scan_dir_path:
            graph_before = scan_dir(self.scan_dir_path)

        before_state: dict[str, Any] = {"task": task, "timestamp": started}
        if graph_before:
            before_state["graph_hash"] = graph_before.hash

        chain.append(
            operation="start",
            x_state=None,
            y_state=before_state,
            metadata={"task": task},
        )

        # Create observers — inject into kwargs so wrapped function can use them
        observer = self._create_observer(chain)
        file_observer = self._create_file_observer(chain)
        api_observer = self._create_api_observer(chain)

        # Inject observers into kwargs if the function accepts them
        sig = inspect.signature(self.target)
        params = sig.parameters
        if "observer" in params:
            kwargs["observer"] = observer
        if "file_observer" in params:
            kwargs["file_observer"] = file_observer
        if "api_observer" in params:
            kwargs["api_observer"] = api_observer
        if "approval_gate" in params and self._approval_gate:
            kwargs["approval_gate"] = self._approval_gate
        if "chain" in params:
            kwargs["chain"] = chain

        output = None
        status = "success"
        error_msg = None

        try:
            output = self.target(*args, **kwargs)
        except Exception as e:
            status = "failed"
            error_msg = str(e)
            output = None

        completed = time.time()

        graph_after = None
        if self.scan_dir_path:
            graph_after = scan_dir(self.scan_dir_path)

        after_state: dict[str, Any] = {
            "task": task,
            "status": status,
            "timestamp": completed,
        }
        if graph_after:
            after_state["graph_hash"] = graph_after.hash
        if error_msg:
            after_state["error"] = error_msg
        if observer.count > 0:
            after_state["actions_summary"] = observer.summary()
        if file_observer.count > 0:
            after_state["file_summary"] = file_observer.summary()
        if api_observer.count > 0:
            after_state["api_summary"] = api_observer.summary()

        chain.append(
            operation="complete",
            y_state=after_state,
            status=status,
            metadata={"duration": completed - started},
            private_key=self.private_key if self.sign else None,
            signer_id=self.signer_id,
        )

        valid, _ = chain.verify()

        receipt = XYReceipt(
            id=uuid.uuid4().hex[:12],
            task=task,
            started=started,
            completed=completed,
            duration=completed - started,
            chain_id=chain.id,
            entry_count=chain.length,
            first_x=chain.entries[0].x,
            final_y=chain.entries[-1].y,
            root_xy=chain.root or "",
            head_xy=chain.entries[-1].xy,
            all_verified=valid,
        )

        # Pick the most specific observer to return
        result_observer = observer
        if file_observer.count > 0:
            result_observer = file_observer
        if api_observer.count > 0:
            result_observer = api_observer

        result = WrappedResult(
            output=output,
            chain=chain,
            receipt=receipt,
            graph_before=graph_before,
            graph_after=graph_after,
            observer=result_observer,
        )

        # Cloud sync if api_key provided (non-fatal)
        if self.api_key:
            try:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Can't block here; schedule as a background task
                        asyncio.ensure_future(self._cloud_sync(chain, receipt))
                    else:
                        loop.run_until_complete(self._cloud_sync(chain, receipt))
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    try:
                        loop.run_until_complete(self._cloud_sync(chain, receipt))
                    finally:
                        loop.close()
            except Exception:
                pass  # Cloud sync failures are non-fatal

        return result

    async def run(self, args: tuple, kwargs: dict) -> WrappedResult:
        """Execute the wrapped target asynchronously and produce an XY chain."""
        task = str(args[0]) if args else "unknown"
        chain = XYChain(
            name=self.chain_name,
            auto_redact=self.auto_redact,
        )
        started = time.time()

        graph_before = None
        if self.scan_dir_path:
            graph_before = scan_dir(self.scan_dir_path)

        before_state: dict[str, Any] = {"task": task, "timestamp": started}
        if graph_before:
            before_state["graph_hash"] = graph_before.hash

        chain.append(
            operation="start",
            x_state=None,
            y_state=before_state,
            metadata={"task": task},
        )

        # Create observers — inject into kwargs so wrapped function can use them
        observer = self._create_observer(chain)
        file_observer = self._create_file_observer(chain)
        api_observer = self._create_api_observer(chain)

        sig = inspect.signature(self.target)
        params = sig.parameters
        if "observer" in params:
            kwargs["observer"] = observer
        if "file_observer" in params:
            kwargs["file_observer"] = file_observer
        if "api_observer" in params:
            kwargs["api_observer"] = api_observer
        if "approval_gate" in params and self._approval_gate:
            kwargs["approval_gate"] = self._approval_gate
        if "chain" in params:
            kwargs["chain"] = chain

        output = None
        status = "success"
        error_msg = None

        try:
            if inspect.iscoroutinefunction(self.target):
                output = await self.target(*args, **kwargs)
            elif callable(self.target):
                output = self.target(*args, **kwargs)
            else:
                raise TypeError(f"Cannot wrap {type(self.target)}: not callable")
        except Exception as e:
            status = "failed"
            error_msg = str(e)
            output = None

        completed = time.time()

        graph_after = None
        if self.scan_dir_path:
            graph_after = scan_dir(self.scan_dir_path)

        after_state: dict[str, Any] = {
            "task": task,
            "status": status,
            "timestamp": completed,
        }
        if graph_after:
            after_state["graph_hash"] = graph_after.hash
        if error_msg:
            after_state["error"] = error_msg
        if observer.count > 0:
            after_state["actions_summary"] = observer.summary()
        if file_observer.count > 0:
            after_state["file_summary"] = file_observer.summary()
        if api_observer.count > 0:
            after_state["api_summary"] = api_observer.summary()

        chain.append(
            operation="complete",
            y_state=after_state,
            status=status,
            metadata={"duration": completed - started},
            private_key=self.private_key if self.sign else None,
            signer_id=self.signer_id,
        )

        valid, _ = chain.verify()

        receipt = XYReceipt(
            id=uuid.uuid4().hex[:12],
            task=task,
            started=started,
            completed=completed,
            duration=completed - started,
            chain_id=chain.id,
            entry_count=chain.length,
            first_x=chain.entries[0].x,
            final_y=chain.entries[-1].y,
            root_xy=chain.root or "",
            head_xy=chain.entries[-1].xy,
            all_verified=valid,
        )

        result_observer = observer
        if file_observer.count > 0:
            result_observer = file_observer
        if api_observer.count > 0:
            result_observer = api_observer

        result = WrappedResult(
            output=output,
            chain=chain,
            receipt=receipt,
            graph_before=graph_before,
            graph_after=graph_after,
            observer=result_observer,
        )

        # Cloud sync if api_key provided
        if self.api_key:
            await self._cloud_sync(chain, receipt)

        return result

    async def _cloud_sync(self, chain: XYChain, receipt: XYReceipt) -> None:
        """Sync chain and receipt to the cloud."""
        try:
            from ..cloud.client import CloudClient
            client = CloudClient(api_key=self.api_key)
            await client.upload_chain(chain)
        except Exception:
            pass  # Sync failures are non-fatal


def xy_wrap(
    target: Any = None,
    *,
    chain_name: str | None = None,
    api_key: str | None = None,
    sign: bool = False,
    private_key: bytes | None = None,
    signer_id: str | None = None,
    scan_dir: str | None = None,
    approval_webhook: str | None = None,
    approval_operations: list[str] | None = None,
    approval_timeout: int = 300,
    auto_redact: bool = True,
) -> Any:
    """Universal wrapper — wraps any agent, function, or workflow.

    Can be used as:
    - Function call: ``wrapped = xy_wrap(my_agent)``
    - Decorator: ``@xy_wrap``
    - Decorator with args: ``@xy_wrap(sign=True)``

    Wrapped functions can accept these optional keyword arguments:
    - ``observer``: ActionObserver for recording arbitrary actions
    - ``file_observer``: FileObserver for recording file operations
    - ``api_observer``: APIObserver for recording API calls
    - ``approval_gate``: ApprovalGate for requesting human approval
    - ``chain``: The XYChain being built (for direct access)
    """
    def _make_wrapper(t: Any) -> WrappedAgent:
        return WrappedAgent(
            t,
            chain_name=chain_name,
            api_key=api_key,
            sign=sign,
            private_key=private_key,
            signer_id=signer_id,
            scan_dir_path=scan_dir,
            approval_webhook=approval_webhook,
            approval_operations=approval_operations,
            approval_timeout=approval_timeout,
            auto_redact=auto_redact,
        )

    def _wrap_callable(t: Any) -> Any:
        agent = _make_wrapper(t)

        if inspect.iscoroutinefunction(t):
            @functools.wraps(t)
            async def async_decorated(*args: Any, **kwargs: Any) -> WrappedResult:
                return await agent.run(args, kwargs)
            async_decorated._agent = agent  # type: ignore[attr-defined]
            return async_decorated
        else:
            @functools.wraps(t)
            def sync_decorated(*args: Any, **kwargs: Any) -> WrappedResult:
                return agent.run_sync(args, kwargs)
            sync_decorated._agent = agent  # type: ignore[attr-defined]
            return sync_decorated

    if target is not None:
        # Direct call: xy_wrap(my_agent) or @xy_wrap
        if callable(target) and not isinstance(target, type):
            return _wrap_callable(target)
        else:
            return _make_wrapper(target)

    # Called with arguments: @xy_wrap(sign=True)
    def decorator(t: Any) -> Any:
        if callable(t) and not isinstance(t, type):
            return _wrap_callable(t)
        else:
            return _make_wrapper(t)

    return decorator
