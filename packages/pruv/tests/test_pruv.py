"""Tests for the pruv SDK."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from xycore import XYChain
from pruv import (
    scan, Graph, GraphDiff,
    xy_wrap, WrappedResult,
    Checkpoint, CheckpointManager,
    ApprovalGate,
)
from pruv.approval.gate import ApprovalRequest, ApprovalResponse


class TestScanner:
    def test_scan_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            (Path(tmpdir) / "app.py").write_text("import os\nprint('hello')\n")
            (Path(tmpdir) / "config.json").write_text('{"key": "value"}\n')
            (Path(tmpdir) / "readme.md").write_text("# Test\n")

            graph = scan(tmpdir)
            assert isinstance(graph, Graph)
            assert len(graph.files) == 3
            assert isinstance(graph.hash, str)
            assert len(graph.hash) == 64

    def test_scan_detects_imports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "app.py").write_text(
                "import flask\nfrom django import conf\nimport os\n"
            )
            graph = scan(tmpdir)
            module_names = {i["module"] for i in graph.imports}
            assert "flask" in module_names
            assert "django" in module_names

    def test_scan_detects_frameworks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "app.py").write_text("from fastapi import FastAPI\n")
            graph = scan(tmpdir)
            fw_names = {f["name"] for f in graph.frameworks}
            assert "fastapi" in fw_names

    def test_scan_detects_env_vars(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "config.py").write_text(
                "import os\nkey = os.environ['DATABASE_URL']\n"
            )
            graph = scan(tmpdir)
            env_names = {e["name"] for e in graph.env_vars}
            assert "DATABASE_URL" in env_names

    def test_scan_ignores_node_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nm = Path(tmpdir) / "node_modules" / "pkg"
            nm.mkdir(parents=True)
            (nm / "index.js").write_text("module.exports = {}")
            (Path(tmpdir) / "app.py").write_text("print('hi')")
            graph = scan(tmpdir)
            paths = {f["path"] for f in graph.files}
            assert all("node_modules" not in p for p in paths)

    def test_scan_hash_deterministic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.py").write_text("x = 1")
            (Path(tmpdir) / "b.py").write_text("y = 2")
            g1 = scan(tmpdir)
            g2 = scan(tmpdir)
            assert g1.hash == g2.hash


class TestGraph:
    def test_graph_diff(self):
        g1 = Graph(files=[
            {"path": "a.py", "language": "python", "size": 100, "lines": 10},
            {"path": "b.py", "language": "python", "size": 200, "lines": 20},
        ])
        g2 = Graph(files=[
            {"path": "a.py", "language": "python", "size": 100, "lines": 10},
            {"path": "c.py", "language": "python", "size": 300, "lines": 30},
        ])
        diff = g1.diff(g2)
        assert len(diff.added) == 1  # c.py added
        assert len(diff.removed) == 1  # b.py removed
        assert diff.added[0].path == "c.py"
        assert diff.removed[0].path == "b.py"

    def test_graph_to_dict(self):
        g = Graph(files=[{"path": "a.py", "language": "python", "size": 100, "lines": 10}])
        d = g.to_dict()
        assert "hash" in d
        assert d["file_count"] == 1


class TestXYWrap:
    def test_wrap_sync_function(self):
        def my_func(task):
            return f"done: {task}"

        wrapped = xy_wrap(my_func)
        result = asyncio.run(wrapped.run("test task"))
        assert isinstance(result, WrappedResult)
        assert result.output == "done: test task"
        assert result.verified
        assert result.receipt.all_verified

    def test_wrap_async_function(self):
        async def my_func(task):
            return f"async done: {task}"

        wrapped = xy_wrap(my_func)
        result = asyncio.run(wrapped.run("test task"))
        assert result.output == "async done: test task"
        assert result.verified

    def test_wrap_with_error(self):
        def bad_func(task):
            raise ValueError("something broke")

        wrapped = xy_wrap(bad_func)
        result = asyncio.run(wrapped.run("fail"))
        assert result.output is None
        assert result.receipt.entry_count == 2  # start + complete(failed)

    def test_wrap_as_decorator(self):
        @xy_wrap
        async def my_workflow(task):
            return f"workflow: {task}"

        result = asyncio.run(my_workflow("test"))
        assert isinstance(result, WrappedResult)
        assert result.output == "workflow: test"

    def test_wrap_produces_receipt(self):
        def noop(task):
            return task

        wrapped = xy_wrap(noop)
        result = asyncio.run(wrapped.run("receipt test"))
        receipt = result.receipt
        assert receipt.task == "receipt test"
        assert receipt.entry_count > 0
        assert len(receipt.hash) == 64


class TestCheckpointManager:
    def test_create_and_restore(self):
        chain = XYChain(name="test")
        chain.append("op1", y_state={"v": 1})
        chain.append("op2", y_state={"v": 2})

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(chain, storage_dir=tmpdir)
            cp = manager.create("before-change")

            # Add more entries
            chain.append("op3", y_state={"v": 3})
            chain.append("op4", y_state={"v": 4})
            assert chain.length == 4

            # Restore
            manager.restore(cp.id)
            assert chain.length == 2

    def test_quick_undo(self):
        chain = XYChain(name="test")
        chain.append("op1", y_state={"v": 1})

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(chain, storage_dir=tmpdir)
            manager.create("cp1")
            chain.append("op2", y_state={"v": 2})
            assert chain.length == 2

            manager.quick_undo()
            assert chain.length == 1

    def test_list_checkpoints(self):
        chain = XYChain(name="test")
        chain.append("op1", y_state={"v": 1})

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(chain, storage_dir=tmpdir)
            manager.create("cp1")
            manager.create("cp2")
            cps = manager.list_checkpoints()
            assert len(cps) == 2

    def test_preview_restore(self):
        chain = XYChain(name="test")
        chain.append("op1", y_state={"v": 1})

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager(chain, storage_dir=tmpdir)
            cp = manager.create("cp1")
            chain.append("op2", y_state={"v": 2})
            chain.append("op3", y_state={"v": 3})

            preview = manager.preview_restore(cp.id)
            assert preview.entries_to_rollback == 2
            assert preview.target_entry_index == 0


class TestApprovalGate:
    def test_requires_approval(self):
        gate = ApprovalGate(
            webhook_url="https://example.com/approve",
            operations={"file.write", "deploy"},
        )
        assert gate.requires_approval("file.write")
        assert gate.requires_approval("deploy")
        assert not gate.requires_approval("read")

    def test_approval_request_dict(self):
        req = ApprovalRequest(
            chain_id="c1", entry_index=5, operation="deploy",
            x_state={"v": 1}, proposed_y_state={"v": 2},
        )
        d = req.to_dict()
        assert d["chain_id"] == "c1"
        assert d["operation"] == "deploy"

    def test_approval_response(self):
        resp = ApprovalResponse(status="approved", approved_by="user@test.com")
        assert resp.is_approved
        denied = ApprovalResponse(status="denied")
        assert not denied.is_approved

    def test_gate_skips_non_matching(self):
        gate = ApprovalGate(
            webhook_url="https://example.com/approve",
            operations={"deploy"},
        )
        result = asyncio.run(gate.gate("c1", 0, "read"))
        assert result.is_approved
        assert result.reason == "no-approval-required"


class TestCLI:
    def test_scan_command(self):
        from click.testing import CliRunner
        from pruv.cli.commands import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("test.py").write_text("x = 1\n")
            result = runner.invoke(cli, ["scan", "."])
            assert result.exit_code == 0
            assert "Files:" in result.output

    def test_scan_json(self):
        from click.testing import CliRunner
        from pruv.cli.commands import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("test.py").write_text("x = 1\n")
            result = runner.invoke(cli, ["scan", ".", "--json-output"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "hash" in data

    def test_verify_command(self):
        from click.testing import CliRunner
        from pruv.cli.commands import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            chain = XYChain(name="test")
            chain.append("op1", y_state={"v": 1})
            chain.append("op2", y_state={"v": 2})
            Path("chain.json").write_text(json.dumps(chain.to_dict()))
            result = runner.invoke(cli, ["verify", "chain.json"])
            assert result.exit_code == 0
            assert "verified" in result.output

    def test_export_csv(self):
        from click.testing import CliRunner
        from pruv.cli.commands import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            chain = XYChain(name="test")
            chain.append("op1", y_state={"v": 1})
            Path("chain.json").write_text(json.dumps(chain.to_dict()))
            result = runner.invoke(cli, ["export", "chain.json", "-f", "csv"])
            assert result.exit_code == 0
            assert "index,timestamp" in result.output
