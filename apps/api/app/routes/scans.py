"""Scan routes — verify chain integrity from chain ID, uploaded file, ZIP, GitHub URL, or any URL."""

from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import sessionmaker

from ..core.dependencies import check_rate_limit, get_current_user
from ..core.rate_limit import RateLimitResult
from ..models.database import ScanResult as ScanResultModel, get_engine
from ..services.chain_service import chain_service

logger = logging.getLogger("pruv.api.scans")

router = APIRouter(prefix="/v1/scans", tags=["scans"])


# ──── Constants ────

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".env", "dist", "build", ".next", ".nuxt", "target",
    ".pytest_cache", ".mypy_cache", ".tox", ".cache",
}

IGNORE_FILES = {".DS_Store", "Thumbs.db", ".gitkeep"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

LANGUAGE_MAP: dict[str, str] = {
    ".py": "py", ".js": "js", ".ts": "ts", ".tsx": "tsx", ".jsx": "jsx",
    ".rb": "rb", ".go": "go", ".rs": "rs", ".java": "java", ".kt": "kt",
    ".swift": "swift", ".cs": "cs", ".cpp": "cpp", ".c": "c", ".h": "h",
    ".php": "php", ".sh": "sh", ".yml": "yaml", ".yaml": "yaml",
    ".json": "json", ".toml": "toml", ".xml": "xml", ".html": "html",
    ".css": "css", ".scss": "scss", ".md": "md", ".sql": "sql",
    ".txt": "txt", ".env": "env", ".cfg": "cfg", ".ini": "ini",
    ".lock": "lock", ".dockerfile": "docker",
}


# ──── Schemas ────


class ScanEntryResponse(BaseModel):
    path: str
    hash: str
    index: int
    verified: bool
    file_type: str = ""
    size: int = 0


class ScanFindingResponse(BaseModel):
    severity: str
    type: str
    message: str
    entry_index: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ScanResponse(BaseModel):
    id: str
    status: str
    chain_id: str | None = None
    source: str | None = None
    started_at: str
    completed_at: str | None = None
    findings: list[ScanFindingResponse] = Field(default_factory=list)
    entries: list[ScanEntryResponse] = Field(default_factory=list)
    summary: str | None = None
    receipt_id: str | None = None


class GitHubScanRequest(BaseModel):
    url: str
    branch: str = "main"


class URLScanRequest(BaseModel):
    url: str


# ──── Database session ────

_session_factory: sessionmaker | None = None


def _get_session():
    global _session_factory
    if _session_factory is None:
        from ..core.config import settings
        if settings.database_url:
            engine = get_engine(settings.database_url)
            _session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )
    if _session_factory is None:
        raise RuntimeError("Database not initialized for scans")
    return _session_factory()


# ──── Helpers ────

def _should_ignore_path(path: str) -> bool:
    """Check if a file path should be ignored."""
    parts = Path(path).parts
    for part in parts:
        if part in IGNORE_DIRS:
            return True
    name = Path(path).name
    if name in IGNORE_FILES:
        return True
    if name.startswith(".env"):
        return True
    return False


def _get_file_type(path: str) -> str:
    """Get file type label from extension."""
    ext = Path(path).suffix.lower()
    return LANGUAGE_MAP.get(ext, ext.lstrip(".") if ext else "")


def _hash_bytes(data: bytes) -> str:
    """SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def _build_chain_from_files(
    files: list[tuple[str, bytes]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build a chain of entries from a list of (path, content) pairs.

    Returns (entries, findings).
    Each file becomes an entry. Chain rule: entry[N].x == entry[N-1].y
    """
    from xycore.crypto import compute_xy

    entries: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    prev_y = "GENESIS"

    for i, (path, content) in enumerate(files):
        x = prev_y
        y = _hash_bytes(content)
        ts = time.time()
        operation = path
        xy = compute_xy(x, operation, y, ts)

        entry = {
            "index": i,
            "timestamp": ts,
            "operation": operation,
            "x": x,
            "y": y,
            "xy": xy,
            "path": path,
            "file_type": _get_file_type(path),
            "size": len(content),
            "verified": True,
        }
        entries.append(entry)

        # Verify chain rule
        if i == 0 and x != "GENESIS":
            entry["verified"] = False
            findings.append({
                "severity": "critical",
                "type": "chain_rule_violation",
                "message": f"First entry x is '{x}', expected 'GENESIS'",
                "entry_index": i,
            })

        # Recompute and verify xy
        expected_xy = compute_xy(x, operation, y, ts)
        if xy != expected_xy:
            entry["verified"] = False
            findings.append({
                "severity": "critical",
                "type": "proof_mismatch",
                "message": f"Entry #{i} ({path}) xy proof mismatch",
                "entry_index": i,
            })

        prev_y = y

    return entries, findings


def _extract_zip_files(zip_bytes: bytes) -> list[tuple[str, bytes]]:
    """Extract files from a ZIP, returning (path, content) pairs."""
    files: list[tuple[str, bytes]] = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in sorted(zf.infolist(), key=lambda x: x.filename):
            # Skip directories
            if info.is_dir():
                continue

            path = info.filename
            # GitHub zipball: strip the top-level directory (owner-repo-sha/)
            parts = path.split("/", 1)
            if len(parts) > 1:
                path = parts[1]
            if not path:
                continue

            # Skip ignored paths
            if _should_ignore_path(path):
                continue

            # Skip large files
            if info.file_size > MAX_FILE_SIZE:
                continue

            try:
                content = zf.read(info)
                files.append((path, content))
            except Exception:
                continue

    return files


def _entries_to_response(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert internal entries to response format."""
    return [
        {
            "path": e.get("path", e.get("operation", f"entry-{e['index']}")),
            "hash": e["y"],
            "index": e["index"],
            "verified": e.get("verified", True),
            "file_type": e.get("file_type", ""),
            "size": e.get("size", 0),
        }
        for e in entries
    ]


def _make_summary(entries: list[dict[str, Any]], findings: list[dict[str, Any]]) -> str:
    """Generate human-readable summary."""
    total = len(entries)
    broken = len([f for f in findings if f["severity"] == "critical"])
    if broken == 0:
        return f"{total} files scanned · all verified"
    return f"{total} files scanned · {broken} integrity failure{'s' if broken != 1 else ''}"


def _verify_entries(
    entries: list[dict[str, Any]],
    deep_verify: bool = True,
    check_signatures: bool = False,
) -> list[dict[str, Any]]:
    """Walk entries and produce findings."""
    from xycore.crypto import compute_xy

    findings: list[dict[str, Any]] = []

    for i, entry in enumerate(entries):
        x = entry.get("x", "")
        y = entry.get("y", "")
        xy = entry.get("xy", entry.get("xy_proof", ""))
        operation = entry.get("operation", entry.get("action", ""))
        timestamp = entry.get("timestamp", 0)

        # Chain rule
        if i == 0:
            if x != "GENESIS":
                findings.append({
                    "severity": "critical",
                    "type": "chain_rule_violation",
                    "message": f"First entry x is '{x}', expected 'GENESIS'",
                    "entry_index": i,
                })
        else:
            prev_y = entries[i - 1].get("y", "")
            if x != prev_y:
                findings.append({
                    "severity": "critical",
                    "type": "chain_break",
                    "message": f"Entry #{i} x does not match previous entry y — chain is broken",
                    "entry_index": i,
                })

        # Proof verification
        if deep_verify and xy and operation:
            expected_xy = compute_xy(x, operation, y, timestamp)
            if xy != expected_xy:
                findings.append({
                    "severity": "critical",
                    "type": "proof_mismatch",
                    "message": f"Entry #{i} xy proof does not match recomputed hash",
                    "entry_index": i,
                })

        # Signature verification
        if check_signatures:
            sig = entry.get("signature")
            pub_key = entry.get("public_key")

            if sig and pub_key:
                try:
                    from xycore import XYEntry as XYE
                    from xycore.signature import verify_signature

                    xy_entry = XYE(
                        index=entry.get("index", i),
                        timestamp=timestamp,
                        operation=operation,
                        x=x,
                        y=y,
                        xy=xy,
                        status=entry.get("status", "success"),
                    )
                    xy_entry.signature = sig
                    xy_entry.public_key = pub_key
                    xy_entry.signer_id = entry.get("signer_id")

                    if not verify_signature(xy_entry):
                        findings.append({
                            "severity": "critical",
                            "type": "signature_invalid",
                            "message": f"Entry #{i} has an invalid Ed25519 signature",
                            "entry_index": i,
                        })
                except ImportError:
                    findings.append({
                        "severity": "warning",
                        "type": "signature_check_unavailable",
                        "message": f"Entry #{i} has a signature but Ed25519 library is not installed",
                        "entry_index": i,
                    })
            elif sig and not pub_key:
                findings.append({
                    "severity": "warning",
                    "type": "signature_missing_key",
                    "message": f"Entry #{i} has a signature but no public key",
                    "entry_index": i,
                })

    return findings


def _make_result(
    scan_id: str,
    chain_id: str | None,
    findings: list[dict[str, Any]],
    started_at: float,
    receipt_id: str | None = None,
    user_id: str | None = None,
    entries: list[dict[str, Any]] | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    completed_at = time.time()
    started_dt = datetime.fromtimestamp(started_at, tz=timezone.utc)
    completed_dt = datetime.fromtimestamp(completed_at, tz=timezone.utc)

    entry_responses = _entries_to_response(entries) if entries else []
    summary = _make_summary(entries or [], findings) if entries else None

    result = {
        "id": scan_id,
        "status": "completed",
        "chain_id": chain_id,
        "source": source,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at)),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(completed_at)),
        "findings": findings,
        "entries": entry_responses,
        "summary": summary,
        "receipt_id": receipt_id,
    }

    # Persist to database
    try:
        with _get_session() as session:
            scan_row = ScanResultModel(
                id=scan_id,
                user_id=user_id,
                status="completed",
                chain_id=chain_id,
                started_at=started_dt,
                completed_at=completed_dt,
                findings=findings,
                receipt_id=receipt_id,
            )
            session.add(scan_row)
            session.commit()
    except Exception:
        logger.exception("Failed to persist scan result %s", scan_id)

    return result


def _parse_github_url(url: str) -> tuple[str, str, str]:
    """Parse a GitHub URL into (owner, repo, branch).

    Accepts:
    - https://github.com/user/repo
    - https://github.com/user/repo.git
    - github.com/user/repo
    - https://github.com/user/repo/tree/main
    """
    url = url.strip().rstrip("/")
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^github\.com/", "", url)

    parts = url.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: cannot extract owner/repo from '{url}'")

    owner = parts[0]
    repo = parts[1]
    branch = "main"

    # Check for /tree/branch pattern
    if len(parts) >= 4 and parts[2] == "tree":
        branch = parts[3]

    return owner, repo, branch


# ──── Routes ────


@router.post("", response_model=ScanResponse)
async def trigger_scan(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Trigger a scan by chain ID or uploaded JSON file."""
    scan_id = uuid.uuid4().hex[:12]
    started_at = time.time()
    content_type = request.headers.get("content-type", "")

    # ── FormData path (file upload) ──
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        chain_id_field = form.get("chain_id")
        options_field = form.get("options")

        deep_verify = True
        check_signatures = True
        generate_receipt = True
        if options_field:
            try:
                opts = json.loads(str(options_field))
                deep_verify = opts.get("deep_verify", True)
                check_signatures = opts.get("check_signatures", True)
                generate_receipt = opts.get("generate_receipt", True)
            except (json.JSONDecodeError, TypeError):
                pass

        if file:
            content = await file.read()
            try:
                file_data = json.loads(content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise HTTPException(status_code=400, detail="Invalid JSON file")

            chain_id = file_data.get("chain_id", file_data.get("id", "uploaded"))
            entries = file_data.get("entries", [])

            if not entries:
                findings = [{
                    "severity": "info",
                    "type": "empty_chain",
                    "message": "No entries found in uploaded file",
                }]
                return _make_result(scan_id, chain_id, findings, started_at,
                                    user_id=user["id"], source="json_upload")
            else:
                findings = _verify_entries(
                    entries,
                    deep_verify=deep_verify,
                    check_signatures=check_signatures,
                )

            return _make_result(scan_id, chain_id, findings, started_at,
                                user_id=user["id"], entries=entries, source="json_upload")

        # FormData with chain_id but no file
        if chain_id_field:
            chain_id = str(chain_id_field)
            chain = chain_service.get_chain(chain_id, user["id"])
            if not chain:
                raise HTTPException(status_code=404, detail="Chain not found")

            entries = chain_service.list_entries(chain_id, offset=0, limit=10000)
            findings = _verify_entries(
                entries,
                deep_verify=deep_verify,
                check_signatures=check_signatures,
            )

            receipt_id = None
            if generate_receipt and len(entries) > 0:
                try:
                    from ..services.receipt_service import receipt_service
                    receipt = receipt_service.create_receipt(
                        chain_id=chain_id, user_id=user["id"], task="scan-verification",
                    )
                    receipt_id = receipt.get("id")
                except Exception:
                    pass

            return _make_result(scan_id, chain_id, findings, started_at, receipt_id,
                                user_id=user["id"], source="chain_id")

        raise HTTPException(status_code=400, detail="Provide chain_id or upload a file")

    # ── JSON body path ──
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    chain_id = body.get("chain_id")
    if not chain_id:
        raise HTTPException(status_code=400, detail="Provide chain_id or upload a file")

    opts = body.get("options", {})
    deep_verify = opts.get("deep_verify", True)
    check_signatures = opts.get("check_signatures", True)
    generate_receipt = opts.get("generate_receipt", True)

    chain = chain_service.get_chain(chain_id, user["id"])
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")

    entries = chain_service.list_entries(chain_id, offset=0, limit=10000)
    findings = _verify_entries(
        entries,
        deep_verify=deep_verify,
        check_signatures=check_signatures,
    )

    receipt_id = None
    if generate_receipt and len(entries) > 0:
        try:
            from ..services.receipt_service import receipt_service
            receipt = receipt_service.create_receipt(
                chain_id=chain_id, user_id=user["id"], task="scan-verification",
            )
            receipt_id = receipt.get("id")
        except Exception:
            pass

    return _make_result(scan_id, chain_id, findings, started_at, receipt_id,
                        user_id=user["id"], source="chain_id")


@router.post("/upload", response_model=ScanResponse)
async def scan_zip_upload(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Scan a ZIP file: extract, hash every file, build chain, verify."""
    scan_id = uuid.uuid4().hex[:12]
    started_at = time.time()

    form = await request.form()
    file = form.get("file")
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    content = await file.read()

    # Verify it's actually a ZIP
    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid ZIP")

    files = _extract_zip_files(content)
    if not files:
        findings = [{"severity": "info", "type": "empty_archive", "message": "No scannable files found in ZIP"}]
        return _make_result(scan_id, None, findings, started_at, user_id=user["id"], source="zip_upload")

    entries, findings = _build_chain_from_files(files)
    return _make_result(scan_id, None, findings, started_at,
                        user_id=user["id"], entries=entries, source="zip_upload")


@router.post("/github", response_model=ScanResponse)
async def scan_github_repo(
    body: GitHubScanRequest,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Scan a public GitHub repo: download zipball, extract, hash, build chain, verify."""
    import httpx

    scan_id = uuid.uuid4().hex[:12]
    started_at = time.time()

    try:
        owner, repo, branch = _parse_github_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if body.branch != "main":
        branch = body.branch

    zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            resp = await client.get(zip_url, headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "pruv-scanner/1.0",
            })
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Repository {owner}/{repo} not found or not public")
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"GitHub returned status {resp.status_code}")
            zip_bytes = resp.content
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout downloading repository from GitHub")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to download repository: {str(e)}")

    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise HTTPException(status_code=502, detail="GitHub did not return a valid ZIP file")

    files = _extract_zip_files(zip_bytes)
    if not files:
        findings = [{"severity": "info", "type": "empty_repo", "message": "No scannable files found in repository"}]
        return _make_result(scan_id, None, findings, started_at,
                            user_id=user["id"], source=f"github:{owner}/{repo}@{branch}")

    entries, findings = _build_chain_from_files(files)
    return _make_result(scan_id, None, findings, started_at,
                        user_id=user["id"], entries=entries,
                        source=f"github:{owner}/{repo}@{branch}")


@router.post("/url", response_model=ScanResponse)
async def scan_url(
    body: URLScanRequest,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Scan any URL: fetch content, hash it, create a single-entry chain."""
    import httpx

    scan_id = uuid.uuid4().hex[:12]
    started_at = time.time()

    url = body.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Redirect GitHub URLs to the github flow
    github_match = re.match(r"^(?:https?://)?github\.com/[\w.-]+/[\w.-]+", url)
    if github_match:
        try:
            owner, repo, branch = _parse_github_url(url)
        except ValueError:
            pass
        else:
            # Re-route through the github endpoint logic
            import httpx as _httpx
            zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
            try:
                async with _httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                    resp = await client.get(zip_url, headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "pruv-scanner/1.0",
                    })
                    if resp.status_code == 200 and zipfile.is_zipfile(io.BytesIO(resp.content)):
                        files = _extract_zip_files(resp.content)
                        if files:
                            entries, findings = _build_chain_from_files(files)
                            return _make_result(
                                scan_id, None, findings, started_at,
                                user_id=user["id"], entries=entries,
                                source=f"github:{owner}/{repo}@{branch}",
                            )
            except Exception:
                pass  # Fall through to generic URL fetch

    # Generic URL fetch
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(url, headers={
                "User-Agent": "pruv-scanner/1.0",
            })
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"URL returned status {resp.status_code}",
                )
            content = resp.content
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout fetching URL")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {str(e)}")

    # Build single-entry chain
    from xycore.crypto import compute_xy

    x = "GENESIS"
    y = _hash_bytes(content)
    ts = time.time()
    xy = compute_xy(x, url, y, ts)

    entry = {
        "index": 0,
        "timestamp": ts,
        "operation": url,
        "x": x,
        "y": y,
        "xy": xy,
        "path": url,
        "file_type": "url",
        "size": len(content),
        "verified": True,
    }

    return _make_result(
        scan_id, None, [], started_at,
        user_id=user["id"], entries=[entry],
        source=f"url:{url}",
    )


@router.get("/{scan_id}/receipt")
async def get_scan_receipt(
    scan_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Generate a self-contained HTML receipt for a scan.

    The receipt includes embedded verification JavaScript that works offline.
    """
    from fastapi.responses import HTMLResponse
    from ..services.receipt_html import generate_receipt_html

    try:
        with _get_session() as session:
            scan = session.query(ScanResultModel).filter(ScanResultModel.id == scan_id).first()
            if not scan:
                raise HTTPException(status_code=404, detail="Scan not found")

            html_content = generate_receipt_html(
                scan_id=scan.id,
                source=None,
                started_at=scan.started_at.strftime("%Y-%m-%dT%H:%M:%SZ") if scan.started_at else "",
                completed_at=scan.completed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if scan.completed_at else None,
                entries=[],  # DB scans don't store entry data — receipt will show findings only
                findings=scan.findings or [],
                summary=None,
            )
            return HTMLResponse(content=html_content, media_type="text/html")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Scan not found")


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan_status(
    scan_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    _rl: RateLimitResult = Depends(check_rate_limit),
):
    """Get the status and results of a scan."""
    try:
        with _get_session() as session:
            scan = session.query(ScanResultModel).filter(ScanResultModel.id == scan_id).first()
            if not scan:
                raise HTTPException(status_code=404, detail="Scan not found")
            return {
                "id": scan.id,
                "status": scan.status,
                "chain_id": scan.chain_id,
                "source": None,
                "started_at": scan.started_at.strftime("%Y-%m-%dT%H:%M:%SZ") if scan.started_at else None,
                "completed_at": scan.completed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if scan.completed_at else None,
                "findings": scan.findings or [],
                "entries": [],
                "summary": None,
                "receipt_id": scan.receipt_id,
            }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Scan not found")
