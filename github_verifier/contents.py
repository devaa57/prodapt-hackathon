"""
Repository file content retrieval and dependency-file parsing.

Supported manifest formats:
  • package.json          (JavaScript / Node.js)
  • requirements.txt      (Python / pip)
  • pyproject.toml        (Python — PEP 621 + Poetry)
  • setup.py              (Python — legacy)
  • Pipfile               (Python — pipenv)
  • go.mod                (Go)
  • Cargo.toml            (Rust)
  • pom.xml               (Java / Maven)
  • build.gradle          (Java / Gradle)
  • Dockerfile            (container hints)
  • README.md             (keyword scan — handled in evidence.py)
  • docker-compose.yml    (service images)
"""
from __future__ import annotations

import base64
import json
import logging
import re

from .client import GitHubClient
from .config import GitHubConfig, settings
from .models import FileContent

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Which files to look for in each repository
# ═══════════════════════════════════════════════════════════════

EVIDENCE_FILES: list[str] = [
    # Documentation & Manifests
    "README.md",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "Pipfile",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    # Container / infra
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
]


# ═══════════════════════════════════════════════════════════════
# File retrieval
# ═══════════════════════════════════════════════════════════════

async def fetch_file_content(
    client: GitHubClient,
    repo_full_name: str,
    file_path: str,
    config: GitHubConfig | None = None,
) -> FileContent | None:
    """Fetch a single file via GET /repos/{owner}/{repo}/contents/{path}."""
    cfg = config or settings
    data = await client.get(f"/repos/{repo_full_name}/contents/{file_path}")

    if data is None or isinstance(data, list):
        return None  # not found or is a directory

    size = data.get("size", 0)
    if size > cfg.max_file_size_bytes:
        logger.info("Skipping %s/%s — too large (%d bytes)", repo_full_name, file_path, size)
        return None

    content = ""
    if data.get("encoding") == "base64" and data.get("content"):
        try:
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            logger.warning("Failed to decode %s/%s", repo_full_name, file_path)
            return None

    return FileContent(
        path=data.get("path", file_path),
        name=data.get("name", file_path.split("/")[-1]),
        content=content,
        size=size,
        download_url=data.get("download_url"),
        repository=repo_full_name,
    )


async def fetch_evidence_files(
    client: GitHubClient,
    repo_full_name: str,
    config: GitHubConfig | None = None,
) -> list[FileContent]:
    """
    Fetch all evidence-relevant files from a repo.
    Uses directory discovery first (single API call) to avoid wasteful 404s,
    and inspects common subdirectories (backend, frontend, etc.) for monorepos.
    """
    cfg = config or settings
    files: list[FileContent] = []

    # 1. Inspect root contents list (1 API call discovers all root files + subdirs)
    root_items = await client.get(f"/repos/{repo_full_name}/contents")
    if isinstance(root_items, list):
        root_files: dict[str, dict] = {}
        candidate_subdirs: list[str] = []

        for item in root_items:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            itype = item.get("type", "")
            if itype == "file":
                root_files[name.lower()] = item
            elif itype == "dir" and name.lower() in (
                "backend", "frontend", "server", "client", "api", "app", "web", "src", "services"
            ):
                candidate_subdirs.append(item.get("path", name))

        # Fetch matching evidence files at root
        for target in EVIDENCE_FILES:
            target_lower = target.lower()
            if target_lower in root_files:
                fc = await fetch_file_content(client, repo_full_name, root_files[target_lower]["path"], cfg)
                if fc:
                    files.append(fc)
                if len(files) >= cfg.max_files_per_repo:
                    return files

        # Fetch manifests inside key monorepo subdirectories
        manifest_names = {
            "package.json", "requirements.txt", "pyproject.toml",
            "go.mod", "cargo.toml", "pom.xml", "build.gradle", "dockerfile",
        }
        for subdir in candidate_subdirs[:3]:  # inspect top 3 subdirs max
            sub_items = await client.get(f"/repos/{repo_full_name}/contents/{subdir}")
            if isinstance(sub_items, list):
                for sub_item in sub_items:
                    if not isinstance(sub_item, dict):
                        continue
                    if sub_item.get("type") == "file":
                        sname = sub_item.get("name", "").lower()
                        if sname in manifest_names:
                            fc = await fetch_file_content(client, repo_full_name, sub_item.get("path", ""), cfg)
                            if fc:
                                files.append(fc)
                            if len(files) >= cfg.max_files_per_repo:
                                return files

        return files

    # Fallback: probe known files if contents listing wasn't a list
    for path in EVIDENCE_FILES:
        if len(files) >= cfg.max_files_per_repo:
            break
        fc = await fetch_file_content(client, repo_full_name, path, cfg)
        if fc is not None:
            files.append(fc)

    return files


# ═══════════════════════════════════════════════════════════════
# Dependency parsers
# ═══════════════════════════════════════════════════════════════

def parse_package_json(content: str) -> list[str]:
    """Extract dependency names from package.json."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    deps: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        section = data.get(key)
        if isinstance(section, dict):
            deps.update(section.keys())
    return sorted(deps)


def parse_requirements_txt(content: str) -> list[str]:
    """Extract package names from requirements.txt / constraints.txt."""
    deps: list[str] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        name = re.split(r"[=<>!~;\[@]", line)[0].strip()
        if name:
            deps.append(name.lower())
    return deps


def parse_pyproject_toml(content: str) -> list[str]:
    """Extract dependency names from pyproject.toml (PEP 621 + Poetry)."""
    try:
        import tomllib  # Python 3.11+
        data = tomllib.loads(content)
    except Exception:
        return _parse_pyproject_regex(content)

    deps: set[str] = set()

    # PEP 621
    for dep in data.get("project", {}).get("dependencies", []):
        name = re.split(r"[=<>!~;\[@]", dep)[0].strip()
        if name:
            deps.add(name.lower())
    for group in data.get("project", {}).get("optional-dependencies", {}).values():
        for dep in group:
            name = re.split(r"[=<>!~;\[@]", dep)[0].strip()
            if name:
                deps.add(name.lower())

    # Poetry
    poetry = data.get("tool", {}).get("poetry", {})
    for section in ("dependencies", "dev-dependencies"):
        grp = poetry.get(section, {})
        if isinstance(grp, dict):
            deps.update(k.lower() for k in grp if k.lower() != "python")

    return sorted(deps)


def _parse_pyproject_regex(content: str) -> list[str]:
    """Fallback regex parser for pyproject.toml."""
    deps: set[str] = set()
    in_deps = False
    for line in content.splitlines():
        s = line.strip()
        if re.match(r"(dependencies|dev-dependencies)\s*=", s):
            in_deps = True
            continue
        if in_deps:
            if s.startswith("]"):
                in_deps = False
                continue
            m = re.match(r"""[\"']([a-zA-Z0-9_-]+)""", s)
            if m:
                deps.add(m.group(1).lower())
    return sorted(deps)


def parse_setup_py(content: str) -> list[str]:
    """Extract install_requires from setup.py (best-effort regex)."""
    m = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if not m:
        return []
    return [
        d.lower()
        for d in re.findall(r"[\"']([a-zA-Z0-9_-]+)", m.group(1))
    ]


def parse_pipfile(content: str) -> list[str]:
    """Extract package names from Pipfile."""
    deps: list[str] = []
    in_pkg = False
    for line in content.splitlines():
        s = line.strip()
        if s in ("[packages]", "[dev-packages]"):
            in_pkg = True
            continue
        if s.startswith("["):
            in_pkg = False
            continue
        if in_pkg and "=" in s:
            name = s.split("=")[0].strip().strip("\"'")
            if name:
                deps.append(name.lower())
    return deps


def parse_go_mod(content: str) -> list[str]:
    """Extract module paths from go.mod require block."""
    deps: list[str] = []
    in_require = False
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("require ("):
            in_require = True
            continue
        if in_require:
            if s == ")":
                in_require = False
                continue
            parts = s.split()
            if parts:
                deps.append(parts[0])
        elif s.startswith("require ") and "(" not in s:
            parts = s.split()
            if len(parts) >= 2:
                deps.append(parts[1])
    return deps


def parse_cargo_toml(content: str) -> list[str]:
    """Extract crate names from Cargo.toml [dependencies]."""
    deps: list[str] = []
    in_deps = False
    for line in content.splitlines():
        s = line.strip()
        if s == "[dependencies]":
            in_deps = True
            continue
        if s.startswith("[") and in_deps:
            break
        if in_deps and "=" in s:
            name = s.split("=")[0].strip()
            if name:
                deps.append(name)
    return deps


def parse_pom_xml(content: str) -> list[str]:
    """Extract artifactIds from pom.xml (best-effort regex)."""
    return re.findall(r"<artifactId>([^<]+)</artifactId>", content)


def parse_build_gradle(content: str) -> list[str]:
    """Extract dependency artifact names from build.gradle."""
    deps: list[str] = []
    for m in re.finditer(r"['\"]([^'\"]+:[^'\"]+:[^'\"]+)['\"]", content):
        parts = m.group(1).split(":")
        if len(parts) >= 2:
            deps.append(parts[1])
    return deps


def parse_dockerfile(content: str) -> list[str]:
    """Extract technology hints from a Dockerfile."""
    hints: list[str] = []
    for line in content.splitlines():
        s = line.strip()
        if s.upper().startswith("FROM "):
            image = s[5:].strip().split()[0]
            hints.append(f"docker-image:{image}")
    return hints


# ═══════════════════════════════════════════════════════════════
# Unified dispatcher
# ═══════════════════════════════════════════════════════════════

def parse_dependencies(file: FileContent) -> list[str]:
    """Route a FileContent to the correct parser and return dep names."""
    name = file.name.lower()
    dispatch = {
        "package.json": parse_package_json,
        "requirements.txt": parse_requirements_txt,
        "pyproject.toml": parse_pyproject_toml,
        "setup.py": parse_setup_py,
        "pipfile": parse_pipfile,
        "go.mod": parse_go_mod,
        "cargo.toml": parse_cargo_toml,
        "pom.xml": parse_pom_xml,
        "build.gradle": parse_build_gradle,
        "dockerfile": parse_dockerfile,
    }
    parser = dispatch.get(name)
    return parser(file.content) if parser else []
