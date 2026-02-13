"""Extended pattern matching for the scanner."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# Extended language detection for more file types
EXTENDED_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".pyx": "cython",
    ".pyi": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".cs": "csharp",
    ".fs": "fsharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".php": "php",
    ".r": "r",
    ".R": "r",
    ".scala": "scala",
    ".clj": "clojure",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".lua": "lua",
    ".pl": "perl",
    ".pm": "perl",
    ".dart": "dart",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".fish": "shell",
    ".ps1": "powershell",
    ".vim": "vim",
    ".sql": "sql",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".proto": "protobuf",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".md": "markdown",
    ".mdx": "mdx",
    ".rst": "restructuredtext",
    ".tex": "latex",
    ".tf": "terraform",
    ".hcl": "hcl",
    ".dockerfile": "dockerfile",
    ".sol": "solidity",
    ".zig": "zig",
    ".nim": "nim",
    ".v": "vlang",
    ".jl": "julia",
}


@dataclass
class DependencyInfo:
    """Information about a project dependency."""

    name: str
    version: str | None
    source: str  # "pyproject.toml", "package.json", "go.mod", etc.
    dev: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "dev": self.dev,
        }


# Package manager file patterns
DEPENDENCY_FILES: dict[str, str] = {
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "Pipfile": "python",
    "package.json": "javascript",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "kotlin",
    "composer.json": "php",
    "pubspec.yaml": "dart",
    "Package.swift": "swift",
    "mix.exs": "elixir",
    "stack.yaml": "haskell",
    "Makefile": "make",
    "CMakeLists.txt": "cmake",
}


# Docker detection patterns
DOCKER_PATTERNS: list[str] = [
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".dockerignore",
]


# CI/CD detection patterns
CICD_PATTERNS: dict[str, list[str]] = {
    "github_actions": [".github/workflows"],
    "gitlab_ci": [".gitlab-ci.yml"],
    "circleci": [".circleci/config.yml"],
    "travis": [".travis.yml"],
    "jenkins": ["Jenkinsfile"],
    "bitbucket": ["bitbucket-pipelines.yml"],
}


# Extended framework detection
EXTENDED_FRAMEWORK_SIGNATURES: dict[str, list[dict[str, Any]]] = {
    "vue": [
        {"file": "vue.config.js", "confidence": 0.95},
        {"file": "nuxt.config.js", "confidence": 0.95},
        {"file": "nuxt.config.ts", "confidence": 0.95},
        {"import": "vue", "confidence": 0.9},
    ],
    "angular": [
        {"file": "angular.json", "confidence": 0.95},
        {"import": "@angular/core", "confidence": 0.95},
    ],
    "svelte": [
        {"file": "svelte.config.js", "confidence": 0.95},
        {"import": "svelte", "confidence": 0.9},
    ],
    "rails": [
        {"file": "config/routes.rb", "confidence": 0.95},
        {"file": "Gemfile", "confidence": 0.7},
    ],
    "spring": [
        {"file": "pom.xml", "confidence": 0.7},
        {"import": "org.springframework", "confidence": 0.95},
    ],
    "tensorflow": [
        {"import": "tensorflow", "confidence": 0.95},
    ],
    "pytorch": [
        {"import": "torch", "confidence": 0.95},
    ],
    "sklearn": [
        {"import": "sklearn", "confidence": 0.95},
    ],
}


# Extended service detection
EXTENDED_SERVICE_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "stripe": [re.compile(r"sk_(?:live|test)_"), re.compile(r"STRIPE_", re.IGNORECASE)],
    "supabase": [re.compile(r"supabase", re.IGNORECASE), re.compile(r"SUPABASE_URL")],
    "openai": [re.compile(r"sk-[a-zA-Z0-9]{20,}"), re.compile(r"OPENAI_API_KEY")],
    "anthropic": [re.compile(r"ANTHROPIC_API_KEY"), re.compile(r"sk-ant-")],
    "aws": [re.compile(r"AKIA[A-Z0-9]{16}"), re.compile(r"AWS_ACCESS_KEY")],
    "gcp": [re.compile(r"GOOGLE_APPLICATION_CREDENTIALS"), re.compile(r"GCLOUD_")],
    "azure": [re.compile(r"AZURE_"), re.compile(r"DefaultEndpointsProtocol=")],
    "github": [re.compile(r"ghp_[a-zA-Z0-9]+"), re.compile(r"GITHUB_TOKEN")],
    "redis": [re.compile(r"redis://"), re.compile(r"REDIS_URL")],
    "postgresql": [re.compile(r"postgres(?:ql)?://"), re.compile(r"DATABASE_URL")],
    "mongodb": [re.compile(r"mongodb(?:\+srv)?://"), re.compile(r"MONGO_URL")],
    "elasticsearch": [re.compile(r"ELASTICSEARCH_URL"), re.compile(r"elastic\.co")],
    "sendgrid": [re.compile(r"SENDGRID_API_KEY"), re.compile(r"SG\.[a-zA-Z0-9]+")],
    "twilio": [re.compile(r"TWILIO_"), re.compile(r"twilio\.com")],
    "firebase": [re.compile(r"FIREBASE_"), re.compile(r"firebase\.google\.com")],
    "vercel": [re.compile(r"VERCEL_"), re.compile(r"vercel\.com")],
    "netlify": [re.compile(r"NETLIFY_"), re.compile(r"netlify\.com")],
    "sentry": [re.compile(r"SENTRY_DSN"), re.compile(r"sentry\.io")],
    "datadog": [re.compile(r"DD_API_KEY"), re.compile(r"datadoghq\.com")],
    "pruv": [re.compile(r"pv_(?:live|test)_"), re.compile(r"PRUV_API_KEY")],
}


def parse_requirements_txt(content: str) -> list[DependencyInfo]:
    """Parse a requirements.txt file into dependency info."""
    deps = []
    for line in content.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Handle version specifiers
        for sep in ["==", ">=", "<=", "~=", "!=", ">"]:
            if sep in line:
                name, version = line.split(sep, 1)
                deps.append(DependencyInfo(
                    name=name.strip(), version=version.strip(),
                    source="requirements.txt",
                ))
                break
        else:
            deps.append(DependencyInfo(
                name=line, version=None, source="requirements.txt",
            ))
    return deps


def parse_package_json_deps(data: dict) -> list[DependencyInfo]:
    """Parse package.json dependencies."""
    deps = []
    for name, version in data.get("dependencies", {}).items():
        deps.append(DependencyInfo(
            name=name, version=version, source="package.json",
        ))
    for name, version in data.get("devDependencies", {}).items():
        deps.append(DependencyInfo(
            name=name, version=version, source="package.json", dev=True,
        ))
    return deps
