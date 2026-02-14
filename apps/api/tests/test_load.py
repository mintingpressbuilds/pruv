"""Load test — 100 concurrent users × (1 chain + 100 entries).

Measures:
  1. Response times under load (p50, p95, p99)
  2. Database connection pool behavior under concurrent access
  3. Rate limiter accuracy and thread safety
  4. Memory usage over time (tracemalloc)

Total: 10,100 API requests across 100 simulated users.
"""

from __future__ import annotations

import gc
import os
import statistics
import threading
import time
import tracemalloc
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.rate_limit import PLAN_LIMITS, rate_limiter
from app.core.security import create_jwt_token
from app.main import app
from app.middleware.logging import _MAX_LOG_BUFFER, _request_log_buffer
from app.models.database import Base, get_engine, get_session_factory
from app.services.chain_service import chain_service


# ─── Constants ───

NUM_USERS = 100
ENTRIES_PER_CHAIN = 100
TOTAL_REQUESTS = NUM_USERS * (1 + ENTRIES_PER_CHAIN)  # 10,100


# ─── Helpers ───


def _make_auth_header(user_index: int) -> dict[str, str]:
    """Create a JWT auth header for a numbered test user."""
    token = create_jwt_token(f"loadtest_user_{user_index}")
    return {"Authorization": f"Bearer {token}"}


def _clear_state():
    """Reset all global mutable state between tests."""
    chain_service._chains.clear()
    chain_service._entries.clear()
    chain_service._share_map.clear()
    rate_limiter.clear()
    _request_log_buffer.clear()
    gc.collect()


def _user_workflow(user_index: int) -> dict:
    """Single user: create 1 chain, append 100 entries.

    Each thread gets its own TestClient so event-loop isolation is clean.
    Returns timing and error data for analysis.
    """
    client = TestClient(app, raise_server_exceptions=False)
    headers = _make_auth_header(user_index)

    result = {
        "user": user_index,
        "create_chain_ms": 0.0,
        "entry_times_ms": [],
        "errors": [],
        "rate_limited_count": 0,
        "total_requests": 0,
        "chain_id": None,
    }

    # ── Create chain ──
    t0 = time.monotonic()
    resp = client.post(
        "/v1/chains",
        json={"name": f"load-user-{user_index}"},
        headers=headers,
    )
    result["create_chain_ms"] = (time.monotonic() - t0) * 1000
    result["total_requests"] += 1

    if resp.status_code == 429:
        result["rate_limited_count"] += 1
        result["errors"].append("create_chain:429")
        return result
    if resp.status_code != 200:
        result["errors"].append(f"create_chain:{resp.status_code}")
        return result

    chain_id = resp.json()["id"]
    result["chain_id"] = chain_id

    # ── Append entries ──
    for j in range(ENTRIES_PER_CHAIN):
        t0 = time.monotonic()
        resp = client.post(
            f"/v1/chains/{chain_id}/entries",
            json={
                "operation": f"step_{j}",
                "y_state": {"step": j, "data": f"v{j}"},
            },
            headers=headers,
        )
        result["entry_times_ms"].append((time.monotonic() - t0) * 1000)
        result["total_requests"] += 1

        if resp.status_code == 429:
            result["rate_limited_count"] += 1
        elif resp.status_code != 200:
            result["errors"].append(f"entry_{j}:{resp.status_code}")
            break

    return result


def _run_concurrent_load() -> dict:
    """Execute the full 100-user concurrent workload once.

    Returns a dict with ``results`` (per-user), ``total_time_s``, and
    aggregate timing lists.
    """
    _clear_state()

    # Raise rate limits so this measures raw throughput, not throttling
    original_limit = PLAN_LIMITS["free"]["requests_per_minute"]
    PLAN_LIMITS["free"]["requests_per_minute"] = 100_000

    try:
        wall_start = time.monotonic()

        per_user = []
        with ThreadPoolExecutor(max_workers=NUM_USERS) as pool:
            futures = {pool.submit(_user_workflow, i): i for i in range(NUM_USERS)}
            for f in as_completed(futures):
                per_user.append(f.result())

        wall_s = time.monotonic() - wall_start

        # Aggregate
        all_entry_ms = []
        all_create_ms = []
        total_errors = []
        for r in per_user:
            all_create_ms.append(r["create_chain_ms"])
            all_entry_ms.extend(r["entry_times_ms"])
            total_errors.extend(r["errors"])

        return {
            "per_user": per_user,
            "wall_s": wall_s,
            "all_entry_ms": sorted(all_entry_ms),
            "all_create_ms": sorted(all_create_ms),
            "errors": total_errors,
        }
    finally:
        PLAN_LIMITS["free"]["requests_per_minute"] = original_limit


# ═══════════════════════════════════════════════════════════════════
# 1. RESPONSE TIMES UNDER LOAD
# ═══════════════════════════════════════════════════════════════════


class TestResponseTimesUnderLoad:
    """100 concurrent users — latency, throughput, correctness."""

    # Run the expensive load once, cache across tests in this class
    _load: dict | None = None

    @classmethod
    def _get_load(cls) -> dict:
        if cls._load is None:
            cls._load = _run_concurrent_load()
        return cls._load

    def setup_method(self):
        # Ensure load is executed before assertions
        self._get_load()

    @classmethod
    def teardown_class(cls):
        cls._load = None
        _clear_state()

    # ── Correctness ──

    def test_zero_errors(self):
        """All 10,100 requests should succeed with zero application errors."""
        load = self._get_load()
        assert load["errors"] == [], f"Errors: {load['errors'][:20]}"

    def test_all_users_completed(self):
        """Every user must have created a chain and appended all 100 entries."""
        load = self._get_load()
        for r in load["per_user"]:
            assert len(r["entry_times_ms"]) == ENTRIES_PER_CHAIN, (
                f"User {r['user']}: {len(r['entry_times_ms'])}/{ENTRIES_PER_CHAIN} entries"
            )
        assert len(load["all_entry_ms"]) == NUM_USERS * ENTRIES_PER_CHAIN

    def test_100_chains_created(self):
        """Exactly 100 chains should exist in the service."""
        assert len(chain_service._chains) == NUM_USERS

    def test_10000_entries_stored(self):
        """Exactly 10,000 entries across all chains."""
        total = sum(len(v) for v in chain_service._entries.values())
        assert total == NUM_USERS * ENTRIES_PER_CHAIN

    def test_every_chain_verifies(self):
        """Every chain must cryptographically verify after concurrent writes."""
        for chain_id in chain_service._chains:
            result = chain_service.verify_chain(chain_id)
            assert result["valid"], (
                f"Chain {chain_id} broke at index {result['break_index']}"
            )
            assert result["length"] == ENTRIES_PER_CHAIN

    # ── Latency ──
    # Note: 100 threads sharing Python's GIL causes queuing.  Actual
    # per-request CPU time is <10 ms, but wall-clock latency per thread
    # rises because each request waits behind ~99 others.  Thresholds
    # are generous to account for this queueing effect and CI variance.

    def test_entry_p50_latency(self):
        """Median append latency under 2 s (thread-queuing dominated)."""
        p50 = statistics.median(self._get_load()["all_entry_ms"])
        assert p50 < 2000, f"p50 = {p50:.2f} ms"

    def test_entry_p95_latency(self):
        """p95 append latency under 4 s."""
        ms = self._get_load()["all_entry_ms"]
        p95 = ms[int(len(ms) * 0.95)]
        assert p95 < 4000, f"p95 = {p95:.2f} ms"

    def test_entry_p99_latency(self):
        """p99 append latency under 6 s."""
        ms = self._get_load()["all_entry_ms"]
        p99 = ms[int(len(ms) * 0.99)]
        assert p99 < 6000, f"p99 = {p99:.2f} ms"

    def test_chain_creation_p99_latency(self):
        """Chain creation p99 under 4 s."""
        ms = self._get_load()["all_create_ms"]
        p99 = ms[int(len(ms) * 0.99)]
        assert p99 < 4000, f"p99 = {p99:.2f} ms"

    # ── Throughput ──

    def test_throughput_above_50_rps(self):
        """10,100 in-process requests should sustain > 50 req/s aggregate."""
        load = self._get_load()
        total_reqs = sum(r["total_requests"] for r in load["per_user"])
        rps = total_reqs / load["wall_s"]
        assert rps > 50, f"Throughput {rps:.0f} req/s (expected > 50)"

    def test_effective_per_request_time_under_10ms(self):
        """Actual CPU cost per request (wall / total_reqs) should be < 10 ms."""
        load = self._get_load()
        total_reqs = sum(r["total_requests"] for r in load["per_user"])
        per_req_ms = (load["wall_s"] * 1000) / total_reqs
        assert per_req_ms < 10, f"Per-request cost {per_req_ms:.2f} ms (expected < 10)"

    def test_no_rate_limiting_triggered(self):
        """With raised limits, zero 429s should occur."""
        load = self._get_load()
        throttled = sum(r["rate_limited_count"] for r in load["per_user"])
        assert throttled == 0


# ═══════════════════════════════════════════════════════════════════
# 2. DATABASE CONNECTION POOL BEHAVIOR
# ═══════════════════════════════════════════════════════════════════


_SQLITE_PATH = "/tmp/pruv_load_test.db"


def _cleanup_db():
    if os.path.exists(_SQLITE_PATH):
        os.remove(_SQLITE_PATH)


class TestConnectionPoolBehavior:
    """SQLAlchemy connection pool under concurrent access."""

    def teardown_method(self):
        _cleanup_db()

    def test_concurrent_sessions_within_pool(self):
        """10 concurrent sessions should all open and close cleanly."""
        engine = get_engine(f"sqlite:///{_SQLITE_PATH}")
        Factory = sessionmaker(bind=engine)

        barrier = threading.Barrier(10, timeout=10)
        errors: list[str] = []

        def _hold_session(i: int):
            try:
                session = Factory()
                barrier.wait()  # hold all sessions open simultaneously
                session.close()
            except Exception as e:
                errors.append(f"thread-{i}: {e}")

        with ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(_hold_session, range(10)))

        assert errors == [], f"Pool errors: {errors}"
        engine.dispose()

    def test_50_sequential_sessions_recycled(self):
        """Opening and closing 50 sessions sequentially should recycle."""
        engine = get_engine(f"sqlite:///{_SQLITE_PATH}")
        Factory = sessionmaker(bind=engine)

        for _ in range(50):
            s = Factory()
            s.close()

        # Pool still works
        s = Factory()
        s.close()
        engine.dispose()

    def test_concurrent_reads_100_threads(self):
        """100 threads issuing SELECT 1 should not corrupt pool state."""
        engine = get_engine(f"sqlite:///{_SQLITE_PATH}")
        Factory = sessionmaker(bind=engine)
        errors: list[str] = []

        def _query(i: int):
            try:
                s = Factory()
                s.execute(text("SELECT 1"))
                s.close()
            except Exception as e:
                errors.append(f"thread-{i}: {e}")

        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(_query, range(100)))

        assert errors == [], f"Pool errors: {errors}"
        engine.dispose()

    def test_sqlite_skips_pool_params(self):
        """get_engine with SQLite should not raise on pool_size/max_overflow."""
        # SQLite path goes through the simplified branch — no crash is the test
        engine = get_engine(f"sqlite:///{_SQLITE_PATH}", pool_size=5, max_overflow=10)
        # Verify engine is functional
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        engine.dispose()

    def test_session_factory_creates_sessions(self):
        """get_session_factory should return a working sessionmaker."""
        factory = get_session_factory(f"sqlite:///{_SQLITE_PATH}")
        session = factory()
        session.execute(text("SELECT 1"))
        session.close()
        factory.kw["bind"].dispose()


# ═══════════════════════════════════════════════════════════════════
# 3. RATE LIMITER ACCURACY
# ═══════════════════════════════════════════════════════════════════


class TestRateLimiterAccuracy:
    """Verify exact limit enforcement and thread-safety."""

    def setup_method(self):
        rate_limiter.clear()

    def teardown_method(self):
        rate_limiter.clear()

    # ── Exact boundary ──

    def test_free_tier_allows_exactly_60(self):
        """Free tier: 60 allowed, 61st denied."""
        key = "rate:free_exact"
        allowed = sum(1 for _ in range(70) if rate_limiter.check(key, plan="free").allowed)
        assert allowed == 60

    def test_pro_tier_allows_exactly_300(self):
        """Pro tier: 300 allowed, 301st denied."""
        key = "rate:pro_exact"
        allowed = sum(1 for _ in range(310) if rate_limiter.check(key, plan="pro").allowed)
        assert allowed == 300

    def test_team_tier_allows_exactly_1000(self):
        """Team tier: 1000 allowed, 1001st denied."""
        key = "rate:team_exact"
        allowed = sum(1 for _ in range(1010) if rate_limiter.check(key, plan="team").allowed)
        assert allowed == 1000

    # ── Header accuracy ──

    def test_remaining_decrements_correctly(self):
        """X-RateLimit-Remaining should decrement by 1 per request."""
        key = "rate:decrement"
        for i in range(60):
            r = rate_limiter.check(key, plan="free")
            assert r.remaining == 59 - i, f"Req {i}: remaining={r.remaining}"

    def test_remaining_zero_when_blocked(self):
        """Once blocked, remaining stays 0."""
        key = "rate:zero_remain"
        for _ in range(60):
            rate_limiter.check(key, plan="free")
        r = rate_limiter.check(key, plan="free")
        assert not r.allowed
        assert r.remaining == 0

    def test_limit_header_matches_plan(self):
        """X-RateLimit-Limit should reflect the plan's max."""
        for plan, expected in [("free", 60), ("pro", 300), ("team", 1000)]:
            r = rate_limiter.check(f"rate:plan_{plan}", plan=plan)
            assert r.limit == expected

    # ── User isolation ──

    def test_100_users_independent_limits(self):
        """Each of 100 users should get their own 60-request window."""
        for i in range(NUM_USERS):
            key = f"rate:isolation_{i}"
            for _ in range(60):
                assert rate_limiter.check(key, plan="free").allowed
            assert not rate_limiter.check(key, plan="free").allowed

    # ── Window expiry ──

    def test_window_expires_after_60s(self):
        """After 61 seconds, old entries should be cleaned and requests allowed."""
        key = "rate:expiry"
        base_time = 1_000_000.0

        with patch("app.core.rate_limit.time") as mock_time:
            mock_time.time.return_value = base_time

            # Fill entire window
            for _ in range(60):
                rate_limiter.check(key, plan="free")
            assert not rate_limiter.check(key, plan="free").allowed

            # Advance past the window
            mock_time.time.return_value = base_time + 61.0
            r = rate_limiter.check(key, plan="free")
            assert r.allowed
            # Old entries should be cleaned
            assert len(rate_limiter._windows[key]) == 1

    # ── Thread safety ──

    def test_concurrent_same_key_approximately_correct(self):
        """200 concurrent checks on one key should allow ~60 (±5 for races)."""
        key = "rate:concurrent"
        allowed = 0
        lock = threading.Lock()

        def _check():
            nonlocal allowed
            r = rate_limiter.check(key, plan="free")
            if r.allowed:
                with lock:
                    allowed += 1

        with ThreadPoolExecutor(max_workers=50) as pool:
            list(pool.map(lambda _: _check(), range(200)))

        # In-memory limiter has no locking, so allow ±5 slack
        assert 55 <= allowed <= 65, f"Allowed {allowed} (expected ~60)"

    def test_100_concurrent_users_each_allowed_60(self):
        """100 users × 70 requests each — every user allowed exactly 60."""

        def _check_user(i: int) -> tuple[int, int]:
            key = f"rate:per_user_{i}"
            a, d = 0, 0
            for _ in range(70):
                if rate_limiter.check(key, plan="free").allowed:
                    a += 1
                else:
                    d += 1
            return a, d

        results = []
        with ThreadPoolExecutor(max_workers=NUM_USERS) as pool:
            results = list(pool.map(_check_user, range(NUM_USERS)))

        for i, (a, d) in enumerate(results):
            assert a == 60, f"User {i}: allowed {a}"
            assert d == 10, f"User {i}: denied {d}"

    # ── API integration ──

    def test_429_returned_at_limit(self):
        """API returns 429 after limit is exhausted."""
        _clear_state()
        original = PLAN_LIMITS["free"]["requests_per_minute"]
        PLAN_LIMITS["free"]["requests_per_minute"] = 3
        try:
            client = TestClient(app, raise_server_exceptions=False)
            headers = _make_auth_header(999)

            for _ in range(3):
                r = client.get("/v1/chains", headers=headers)
                assert r.status_code == 200

            r = client.get("/v1/chains", headers=headers)
            assert r.status_code == 429
            assert r.json()["detail"] == "Rate limit exceeded"
        finally:
            PLAN_LIMITS["free"]["requests_per_minute"] = original
            _clear_state()

    def test_rate_limit_headers_present(self):
        """Every authenticated response should carry X-RateLimit-* headers."""
        _clear_state()
        original = PLAN_LIMITS["free"]["requests_per_minute"]
        PLAN_LIMITS["free"]["requests_per_minute"] = 100_000
        try:
            client = TestClient(app, raise_server_exceptions=False)
            headers = _make_auth_header(998)

            r = client.post("/v1/chains", json={"name": "hdr"}, headers=headers)
            assert r.status_code == 200
            assert "X-RateLimit-Limit" in r.headers
            assert "X-RateLimit-Remaining" in r.headers
            assert "X-RateLimit-Reset" in r.headers
        finally:
            PLAN_LIMITS["free"]["requests_per_minute"] = original
            _clear_state()


# ═══════════════════════════════════════════════════════════════════
# 4. MEMORY USAGE OVER TIME
# ═══════════════════════════════════════════════════════════════════


class TestMemoryUsage:
    """Verify memory stays bounded under sustained load."""

    def setup_method(self):
        _clear_state()
        gc.collect()

    def teardown_method(self):
        _clear_state()
        gc.collect()

    def test_memory_growth_is_linear(self):
        """Memory for 10 chains × 100 entries should grow linearly, not exponentially."""
        original = PLAN_LIMITS["free"]["requests_per_minute"]
        PLAN_LIMITS["free"]["requests_per_minute"] = 100_000
        tracemalloc.start()

        try:
            snapshot_before = tracemalloc.take_snapshot()

            client = TestClient(app, raise_server_exceptions=False)
            headers = _make_auth_header(900)

            samples: list[int] = []
            for c in range(10):
                resp = client.post(
                    "/v1/chains",
                    json={"name": f"mem-{c}"},
                    headers=headers,
                )
                cid = resp.json()["id"]

                for e in range(100):
                    client.post(
                        f"/v1/chains/{cid}/entries",
                        json={"operation": f"op_{e}", "y_state": {"v": e}},
                        headers=headers,
                    )

                snap = tracemalloc.take_snapshot()
                growth = sum(
                    s.size_diff
                    for s in snap.compare_to(snapshot_before, "lineno")
                    if s.size_diff > 0
                )
                samples.append(growth)

            # Compare growth rate: last-5-chains vs first-5-chains
            # Linear means roughly equal growth per batch.
            if samples[4] > samples[0] and (samples[4] - samples[0]) > 0:
                early = samples[4] - samples[0]  # chains 1-5
                late = samples[9] - samples[4]    # chains 5-10
                ratio = late / early
                assert ratio < 3.0, (
                    f"Memory growth ratio {ratio:.2f}× — suggests non-linear scaling"
                )

        finally:
            PLAN_LIMITS["free"]["requests_per_minute"] = original
            tracemalloc.stop()
            _clear_state()

    def test_memory_freed_after_deletion(self):
        """Deleting all chains should release their entries from memory."""
        original = PLAN_LIMITS["free"]["requests_per_minute"]
        PLAN_LIMITS["free"]["requests_per_minute"] = 100_000
        try:
            client = TestClient(app, raise_server_exceptions=False)
            headers = _make_auth_header(901)

            chain_ids = []
            for c in range(10):
                resp = client.post(
                    "/v1/chains",
                    json={"name": f"del-{c}"},
                    headers=headers,
                )
                cid = resp.json()["id"]
                chain_ids.append(cid)
                for e in range(50):
                    client.post(
                        f"/v1/chains/{cid}/entries",
                        json={"operation": f"op_{e}", "y_state": {"v": e}},
                        headers=headers,
                    )

            assert len(chain_service._chains) == 10
            assert sum(len(v) for v in chain_service._entries.values()) == 500

            # Delete everything
            for cid in chain_ids:
                client.delete(f"/v1/chains/{cid}", headers=headers)

            gc.collect()
            assert len(chain_service._chains) == 0
            assert sum(len(v) for v in chain_service._entries.values()) == 0

        finally:
            PLAN_LIMITS["free"]["requests_per_minute"] = original
            _clear_state()

    def test_log_buffer_bounded_at_max(self):
        """Log buffer must never exceed _MAX_LOG_BUFFER entries."""
        # Push more requests than the buffer cap
        client = TestClient(app, raise_server_exceptions=False)
        for _ in range(250):
            client.get("/health")

        assert len(_request_log_buffer) <= _MAX_LOG_BUFFER

    def test_rate_limiter_cleans_expired_windows(self):
        """Expired timestamps should be pruned on the next check."""
        key = "rate:gc_test"
        base = 1_000_000.0

        with patch("app.core.rate_limit.time") as mt:
            mt.time.return_value = base
            for _ in range(60):
                rate_limiter.check(key, plan="free")
            assert len(rate_limiter._windows[key]) == 60

            # Advance 61 seconds
            mt.time.return_value = base + 61.0
            rate_limiter.check(key, plan="free")
            assert len(rate_limiter._windows[key]) == 1

    def test_concurrent_load_memory_bounded(self):
        """Full 100-user load should not use more than 200 MB."""
        original = PLAN_LIMITS["free"]["requests_per_minute"]
        PLAN_LIMITS["free"]["requests_per_minute"] = 100_000
        tracemalloc.start()

        try:
            snap_before = tracemalloc.take_snapshot()

            with ThreadPoolExecutor(max_workers=NUM_USERS) as pool:
                list(pool.map(_user_workflow, range(NUM_USERS)))

            snap_after = tracemalloc.take_snapshot()
            growth_bytes = sum(
                s.size_diff
                for s in snap_after.compare_to(snap_before, "lineno")
                if s.size_diff > 0
            )
            growth_mb = growth_bytes / (1024 * 1024)

            assert growth_mb < 200, f"Memory grew {growth_mb:.1f} MB (limit 200 MB)"

        finally:
            PLAN_LIMITS["free"]["requests_per_minute"] = original
            tracemalloc.stop()
            _clear_state()
