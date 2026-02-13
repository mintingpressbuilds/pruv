"""File scanner with language, import, env var, framework, and service detection."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LANGUAGE_MAP: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".jsx": "javascript", ".rb": "ruby",
    ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin",
    ".swift": "swift", ".cs": "csharp", ".cpp": "cpp", ".c": "c",
    ".h": "c", ".hpp": "cpp", ".php": "php", ".r": "r",
    ".scala": "scala", ".sh": "shell", ".bash": "shell",
    ".yml": "yaml", ".yaml": "yaml", ".json": "json",
    ".toml": "toml", ".xml": "xml", ".html": "html", ".css": "css",
    ".scss": "scss", ".md": "markdown", ".sql": "sql",
}

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".env", "dist", "build", ".next", ".nuxt", "target",
    ".pytest_cache", ".mypy_cache", "eggs", "*.egg-info",
    ".tox", ".cache", "coverage", ".coverage",
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", ".gitkeep",
}

FRAMEWORK_SIGNATURES: dict[str, list[dict[str, Any]]] = {
    "nextjs": [
        {"file": "next.config.js", "confidence": 0.95},
        {"file": "next.config.ts", "confidence": 0.95},
        {"file": "next.config.mjs", "confidence": 0.95},
        {"import": "next", "confidence": 0.9},
    ],
    "react": [
        {"import": "react", "confidence": 0.9},
        {"import": "react-dom", "confidence": 0.9},
    ],
    "django": [
        {"file": "manage.py", "confidence": 0.8},
        {"import": "django", "confidence": 0.95},
        {"file": "settings.py", "confidence": 0.7},
    ],
    "flask": [
        {"import": "flask", "confidence": 0.95},
    ],
    "fastapi": [
        {"import": "fastapi", "confidence": 0.95},
    ],
    "express": [
        {"import": "express", "confidence": 0.9},
    ],
    "langchain": [
        {"import": "langchain", "confidence": 0.95},
    ],
    "crewai": [
        {"import": "crewai", "confidence": 0.95},
    ],
    "autogen": [
        {"import": "autogen", "confidence": 0.95},
        {"import": "pyautogen", "confidence": 0.95},
    ],
    "openai": [
        {"import": "openai", "confidence": 0.9},
    ],
}

SERVICE_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "stripe": [re.compile(r"sk_(?:live|test)_"), re.compile(r"stripe", re.IGNORECASE)],
    "supabase": [re.compile(r"supabase", re.IGNORECASE)],
    "openai": [re.compile(r"sk-[a-zA-Z0-9]{20,}"), re.compile(r"OPENAI_API_KEY")],
    "aws": [re.compile(r"AKIA[A-Z0-9]{16}"), re.compile(r"AWS_ACCESS_KEY")],
    "github": [re.compile(r"ghp_[a-zA-Z0-9]+"), re.compile(r"GITHUB_TOKEN")],
    "redis": [re.compile(r"redis://"), re.compile(r"REDIS_URL")],
    "postgresql": [re.compile(r"postgres(?:ql)?://"), re.compile(r"DATABASE_URL")],
}

ENV_VAR_PATTERN = re.compile(
    r"""(?:os\.environ\[['"]|os\.getenv\(['"]|process\.env\.|"""
    r"""ENV\[['"]|getenv\(['"])([A-Z_][A-Z0-9_]*)""",
)

IMPORT_PATTERNS: dict[str, re.Pattern[str]] = {
    "python": re.compile(r"^(?:from|import)\s+([\w.]+)", re.MULTILINE),
    "javascript": re.compile(
        r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
        re.MULTILINE,
    ),
    "typescript": re.compile(
        r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
        re.MULTILINE,
    ),
}


@dataclass
class FileInfo:
    path: str
    language: str
    size: int
    lines: int

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "language": self.language, "size": self.size, "lines": self.lines}


@dataclass
class ImportInfo:
    module: str
    source_file: str
    language: str

    def to_dict(self) -> dict[str, Any]:
        return {"module": self.module, "source_file": self.source_file, "language": self.language}


@dataclass
class EnvVarInfo:
    name: str
    source_file: str
    line: int

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "source_file": self.source_file, "line": self.line}


@dataclass
class FrameworkInfo:
    name: str
    confidence: float
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "confidence": self.confidence, "evidence": self.evidence}


@dataclass
class ServiceInfo:
    name: str
    evidence: str
    source_file: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "evidence": self.evidence, "source_file": self.source_file}


def _should_ignore(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True
        for pattern in IGNORE_DIRS:
            if "*" in pattern and part.endswith(pattern.replace("*", "")):
                return True
    return path.name in IGNORE_FILES


def _detect_language(path: Path) -> str:
    return LANGUAGE_MAP.get(path.suffix.lower(), "unknown")


def _count_lines(path: Path) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeDecodeError):
        return 0


def _read_file_safe(path: Path, max_size: int = 1_000_000) -> str | None:
    if path.stat().st_size > max_size:
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return None


def _scan_imports(content: str, language: str, file_path: str) -> list[ImportInfo]:
    pattern = IMPORT_PATTERNS.get(language)
    if pattern is None:
        return []
    imports = []
    for match in pattern.finditer(content):
        groups = [g for g in match.groups() if g]
        for module in groups:
            root = module.split(".")[0].split("/")[0]
            if not root.startswith("."):
                imports.append(ImportInfo(module=root, source_file=file_path, language=language))
    return imports


def _scan_env_vars(content: str, file_path: str) -> list[EnvVarInfo]:
    results = []
    for i, line in enumerate(content.splitlines(), 1):
        for match in ENV_VAR_PATTERN.finditer(line):
            results.append(EnvVarInfo(name=match.group(1), source_file=file_path, line=i))
    return results


def _detect_services(content: str, file_path: str) -> list[ServiceInfo]:
    results = []
    seen = set()
    for service, patterns in SERVICE_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(content):
                if service not in seen:
                    seen.add(service)
                    results.append(ServiceInfo(
                        name=service, evidence=pattern.pattern, source_file=file_path,
                    ))
                break
    return results


@dataclass
class ScanResult:
    """Result of scanning a directory."""

    root: str
    files: list[FileInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    env_vars: list[EnvVarInfo] = field(default_factory=list)
    frameworks: list[FrameworkInfo] = field(default_factory=list)
    services: list[ServiceInfo] = field(default_factory=list)
    file_contents: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "files": [f.to_dict() for f in self.files],
            "imports": [i.to_dict() for i in self.imports],
            "env_vars": [e.to_dict() for e in self.env_vars],
            "frameworks": [f.to_dict() for f in self.frameworks],
            "services": [s.to_dict() for s in self.services],
        }


def scan(
    directory: str | Path = ".",
    include_contents: bool = False,
) -> "ScanResult":
    """Scan a directory for files, imports, env vars, frameworks, and services.

    Returns a ScanResult with all detected information.
    """
    from ..graph import Graph

    root = Path(directory).resolve()
    result = ScanResult(root=str(root))

    all_imports: set[str] = set()
    file_names: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            rel_path = str(fpath.relative_to(root))

            if _should_ignore(fpath):
                continue

            language = _detect_language(fpath)
            try:
                size = fpath.stat().st_size
            except OSError:
                continue

            lines = _count_lines(fpath)
            result.files.append(FileInfo(
                path=rel_path, language=language, size=size, lines=lines,
            ))
            file_names.add(fname)

            content = _read_file_safe(fpath)
            if content is None:
                continue

            if include_contents:
                result.file_contents[rel_path] = content

            # Imports
            for imp in _scan_imports(content, language, rel_path):
                if imp.module not in all_imports:
                    all_imports.add(imp.module)
                    result.imports.append(imp)

            # Env vars
            result.env_vars.extend(_scan_env_vars(content, rel_path))

            # Services
            result.services.extend(_detect_services(content, rel_path))

    # Framework detection
    detected_frameworks: dict[str, float] = {}
    framework_evidence: dict[str, str] = {}

    for fw_name, signatures in FRAMEWORK_SIGNATURES.items():
        for sig in signatures:
            if "file" in sig:
                if sig["file"] in file_names:
                    conf = sig["confidence"]
                    if conf > detected_frameworks.get(fw_name, 0):
                        detected_frameworks[fw_name] = conf
                        framework_evidence[fw_name] = f"file: {sig['file']}"
            if "import" in sig:
                if sig["import"] in all_imports:
                    conf = sig["confidence"]
                    if conf > detected_frameworks.get(fw_name, 0):
                        detected_frameworks[fw_name] = conf
                        framework_evidence[fw_name] = f"import: {sig['import']}"

    for fw_name, confidence in detected_frameworks.items():
        if confidence >= 0.7:
            result.frameworks.append(FrameworkInfo(
                name=fw_name, confidence=confidence,
                evidence=framework_evidence[fw_name],
            ))

    # Convert to Graph and return
    graph = Graph.from_scan_result(result)
    return graph
