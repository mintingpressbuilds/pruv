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


@dataclass
class WrappedResult:
    """Result from a wrapped operation."""

    output: Any
    chain: XYChain
    receipt: XYReceipt
    graph_before: Graph | None = None
    graph_after: Graph | None = None

    @property
    def diff(self) -> GraphDiff | None:
        if self.graph_before and self.graph_after:
            return self.graph_before.diff(self.graph_after)
        return None

    @property
    def verified(self) -> bool:
        valid, _ = self.chain.verify()
        return valid


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

        return WrappedResult(
            output=output,
            chain=chain,
            receipt=receipt,
            graph_before=graph_before,
            graph_after=graph_after,
        )

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

        return WrappedResult(
            output=output,
            chain=chain,
            receipt=receipt,
            graph_before=graph_before,
            graph_after=graph_after,
        )


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
