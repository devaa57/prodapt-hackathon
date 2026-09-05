"""
Deterministic evidence extraction from GitHub data.

This module converts raw GitHub API data (profiles, repos, files, commits)
into structured TechEvidence objects.  It is *entirely* deterministic — no
LLM calls.  A downstream LangGraph agent can consume this structured output
for semantic reasoning.

Confidence scores use the base weights from models.EVIDENCE_WEIGHTS.
"""
from __future__ import annotations

import logging

from .contents import parse_dependencies
from .models import (
    CommitInfo,
    EvidenceType,
    EVIDENCE_WEIGHTS,
    FileContent,
    GitHubProfile,
    Repository,
    TechEvidence,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Technology fingerprint mappings
# ═══════════════════════════════════════════════════════════════

# dependency / package name → canonical technology name
DEPENDENCY_TO_TECH: dict[str, str] = {
    # ── JavaScript / Node.js ──────────────────────────────────
    "express": "Express.js", "koa": "Koa.js", "fastify": "Fastify",
    "hapi": "Hapi.js", "@nestjs/core": "NestJS",
    "pg": "PostgreSQL", "pg-pool": "PostgreSQL", "pg-promise": "PostgreSQL",
    "sequelize": "Sequelize", "typeorm": "TypeORM", "prisma": "Prisma",
    "@prisma/client": "Prisma", "zod": "Zod", "bcryptjs": "Bcrypt",
    "knex": "Knex.js",
    "mongoose": "MongoDB", "mongodb": "MongoDB",
    "redis": "Redis", "ioredis": "Redis", "bull": "Redis", "bullmq": "Redis",
    "react": "React", "react-dom": "React", "react-router-dom": "React Router",
    "axios": "Axios",
    "next": "Next.js", "vue": "Vue.js", "nuxt": "Nuxt.js",
    "@angular/core": "Angular", "svelte": "Svelte",
    "typescript": "TypeScript",
    "graphql": "GraphQL", "apollo-server": "GraphQL",
    "socket.io": "WebSocket", "tailwindcss": "Tailwind CSS",
    "webpack": "Webpack", "vite": "Vite",
    "jest": "Jest", "mocha": "Mocha", "cypress": "Cypress",
    "passport": "Passport.js", "jsonwebtoken": "JWT",
    "aws-sdk": "AWS", "@aws-sdk/client-s3": "AWS S3", "stripe": "Stripe",
    # ── Python ────────────────────────────────────────────────
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "starlette": "Starlette", "uvicorn": "Uvicorn",
    "psycopg2": "PostgreSQL", "psycopg2-binary": "PostgreSQL",
    "psycopg": "PostgreSQL", "asyncpg": "PostgreSQL",
    "sqlalchemy": "SQLAlchemy", "alembic": "Alembic",
    "pymongo": "MongoDB", "motor": "MongoDB",
    "celery": "Celery",
    "langchain": "LangChain", "langchain-core": "LangChain",
    "langgraph": "LangGraph", "openai": "OpenAI", "anthropic": "Anthropic",
    "tensorflow": "TensorFlow", "torch": "PyTorch", "pytorch": "PyTorch",
    "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "pandas": "Pandas", "numpy": "NumPy", "scipy": "SciPy",
    "matplotlib": "Matplotlib",
    "pydantic": "Pydantic", "httpx": "httpx", "requests": "Requests",
    "boto3": "AWS", "pytest": "pytest", "gunicorn": "Gunicorn",
    # ── Java / JVM ────────────────────────────────────────────
    "spring-boot-starter-web": "Spring Boot",
    "spring-boot-starter": "Spring Boot",
    "hibernate-core": "Hibernate",
    "postgresql": "PostgreSQL", "mysql-connector-java": "MySQL",
    "jedis": "Redis", "lettuce-core": "Redis",
    # ── Go ────────────────────────────────────────────────────
    "gin-gonic/gin": "Gin", "lib/pq": "PostgreSQL",
    "pgx": "PostgreSQL", "go-redis": "Redis",
}

# GitHub language → canonical technology name
LANGUAGE_TO_TECH: dict[str, str] = {
    "Python": "Python", "JavaScript": "JavaScript",
    "TypeScript": "TypeScript", "Java": "Java", "Go": "Go",
    "Rust": "Rust", "Ruby": "Ruby", "PHP": "PHP",
    "C#": "C#", "C++": "C++", "C": "C",
    "Swift": "Swift", "Kotlin": "Kotlin", "Dart": "Dart",
    "Scala": "Scala", "Shell": "Shell/Bash",
    "Dockerfile": "Docker", "HCL": "Terraform",
    "HTML": "HTML", "CSS": "CSS", "SCSS": "SCSS", "Vue": "Vue.js",
}

# keyword → canonical technology (for README / topics / descriptions)
TECH_KEYWORDS: dict[str, list[str]] = {
    "PostgreSQL":   ["postgresql", "postgres", "psql"],
    "MySQL":        ["mysql", "mariadb"],
    "MongoDB":      ["mongodb", "mongoose", "mongo"],
    "Redis":        ["redis"],
    "Python":       ["python"],
    "JavaScript":   ["javascript"],
    "TypeScript":   ["typescript"],
    "Node.js":      ["node.js", "nodejs"],
    "React":        ["react", "reactjs"],
    "Vue.js":       ["vue.js", "vuejs"],
    "Angular":      ["angular"],
    "Next.js":      ["next.js", "nextjs"],
    "Django":       ["django"],
    "Flask":        ["flask"],
    "FastAPI":      ["fastapi"],
    "Express.js":   ["express.js", "expressjs", "express"],
    "Spring Boot":  ["spring boot", "spring-boot", "springboot"],
    "Docker":       ["docker", "dockerfile", "docker-compose"],
    "Kubernetes":   ["kubernetes", "k8s"],
    "AWS":          ["aws", "amazon web services"],
    "GCP":          ["gcp", "google cloud", "firebase"],
    "Azure":        ["azure"],
    "GraphQL":      ["graphql"],
    "REST API":     ["rest api", "restful"],
    "Prisma":       ["prisma", "prisma client"],
    "Vite":         ["vite"],
    "Zod":          ["zod"],
    "JWT":          ["jwt", "jsonwebtoken"],
    "Machine Learning": ["machine learning", "deep learning"],
    "TensorFlow":   ["tensorflow"],
    "PyTorch":      ["pytorch"],
    "LangChain":    ["langchain"],
    "CI/CD":        ["ci/cd", "github actions", "jenkins"],
    "Terraform":    ["terraform"],
    "Microservices": ["microservice", "microservices"],
}

# Ecosystem manifest → ecosystem technology (e.g. package.json → Node.js)
_MANIFEST_TECH: dict[str, str] = {
    "package.json": "Node.js",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "pipfile": "Python",
    "go.mod": "Go",
    "cargo.toml": "Rust",
    "pom.xml": "Java",
    "build.gradle": "Java",
}


# ═══════════════════════════════════════════════════════════════
# Extractor
# ═══════════════════════════════════════════════════════════════

class EvidenceExtractor:
    """Collects TechEvidence from various GitHub data sources."""

    def __init__(self) -> None:
        self._evidence: list[TechEvidence] = []

    @property
    def evidence(self) -> list[TechEvidence]:
        return list(self._evidence)

    # ── Profile ───────────────────────────────────────────────

    def extract_from_profile(self, profile: GitHubProfile) -> list[TechEvidence]:
        text = " ".join(filter(None, [profile.bio, profile.company])).lower()
        if not text.strip():
            return []
        found = self._keyword_scan(
            text,
            evidence_type=EvidenceType.PROFILE,
            source="GitHub Profile",
            source_url=profile.profile_url,
            prefix="Profile bio/company",
        )
        self._evidence.extend(found)
        return found

    # ── Repository metadata ───────────────────────────────────

    def extract_from_repository(self, repo: Repository) -> list[TechEvidence]:
        found: list[TechEvidence] = []

        # Primary language
        if repo.primary_language and repo.primary_language in LANGUAGE_TO_TECH:
            found.append(TechEvidence(
                technology=LANGUAGE_TO_TECH[repo.primary_language],
                evidence_type=EvidenceType.LANGUAGE,
                source=f"Repo: {repo.name}",
                source_url=repo.html_url,
                details=f"Primary language: {repo.primary_language}",
                confidence=EVIDENCE_WEIGHTS[EvidenceType.LANGUAGE],
                repository=repo.full_name,
            ))

        # Topics
        for topic in repo.topics:
            tl = topic.lower()
            for tech, kws in TECH_KEYWORDS.items():
                if tl in kws or tl == tech.lower():
                    found.append(TechEvidence(
                        technology=tech,
                        evidence_type=EvidenceType.TOPIC,
                        source=f"Repo: {repo.name}",
                        source_url=repo.html_url,
                        details=f"Topic: '{topic}'",
                        confidence=EVIDENCE_WEIGHTS[EvidenceType.TOPIC],
                        repository=repo.full_name,
                    ))
                    break

        # Description
        if repo.description:
            desc_ev = self._keyword_scan(
                repo.description.lower(),
                evidence_type=EvidenceType.REPOSITORY_METADATA,
                source=f"Repo: {repo.name}",
                source_url=repo.html_url,
                prefix="Description",
                repository=repo.full_name,
            )
            found.extend(desc_ev)

        self._evidence.extend(found)
        return found

    # ── Language breakdown ────────────────────────────────────

    def extract_from_languages(
        self, repo_full_name: str, repo_url: str, languages: dict[str, int],
    ) -> list[TechEvidence]:
        found: list[TechEvidence] = []
        total = sum(languages.values()) or 1

        for lang, byte_count in languages.items():
            if lang not in LANGUAGE_TO_TECH:
                continue
            proportion = byte_count / total
            confidence = round(
                EVIDENCE_WEIGHTS[EvidenceType.LANGUAGE] * min(1.0, proportion * 2),
                3,
            )
            found.append(TechEvidence(
                technology=LANGUAGE_TO_TECH[lang],
                evidence_type=EvidenceType.LANGUAGE,
                source=f"Languages: {repo_full_name}",
                source_url=repo_url,
                details=f"{lang}: {byte_count:,} bytes ({proportion:.0%})",
                confidence=confidence,
                repository=repo_full_name,
            ))

        self._evidence.extend(found)
        return found

    # ── Dependencies ──────────────────────────────────────────

    def extract_from_dependencies(self, file: FileContent) -> list[TechEvidence]:
        found: list[TechEvidence] = []
        deps = parse_dependencies(file)
        file_url = (
            file.download_url
            or f"https://github.com/{file.repository}/blob/HEAD/{file.path}"
        )

        # The manifest itself implies an ecosystem
        manifest_tech = _MANIFEST_TECH.get(file.name.lower())
        if manifest_tech:
            found.append(TechEvidence(
                technology=manifest_tech,
                evidence_type=EvidenceType.DEPENDENCY,
                source=file.name,
                source_url=file_url,
                details=f"{file.name} present → {manifest_tech} project",
                confidence=EVIDENCE_WEIGHTS[EvidenceType.DEPENDENCY],
                repository=file.repository,
            ))

        for dep in deps:
            dep_key = dep.lower().strip()
            tech = DEPENDENCY_TO_TECH.get(dep_key)
            # For Go modules, try last two path segments
            if not tech and "/" in dep_key:
                short = "/".join(dep_key.split("/")[-2:])
                tech = DEPENDENCY_TO_TECH.get(short)
            if tech:
                found.append(TechEvidence(
                    technology=tech,
                    evidence_type=EvidenceType.DEPENDENCY,
                    source=file.name,
                    source_url=file_url,
                    details=f"Dependency '{dep}' in {file.name}",
                    confidence=EVIDENCE_WEIGHTS[EvidenceType.DEPENDENCY],
                    repository=file.repository,
                ))

        self._evidence.extend(found)
        return found

    # ── README ────────────────────────────────────────────────

    def extract_from_readme(self, file: FileContent) -> list[TechEvidence]:
        if not file.content:
            return []
        url = (
            file.download_url
            or f"https://github.com/{file.repository}/blob/HEAD/README.md"
        )
        found = self._keyword_scan(
            file.content.lower(),
            evidence_type=EvidenceType.README,
            source=f"README: {file.repository}",
            source_url=url,
            prefix="README",
            repository=file.repository,
        )
        self._evidence.extend(found)
        return found

    # ── Dockerfile ────────────────────────────────────────────

    def extract_from_dockerfile(self, file: FileContent) -> list[TechEvidence]:
        if not file.content:
            return []
        url = (
            file.download_url
            or f"https://github.com/{file.repository}/blob/HEAD/Dockerfile"
        )
        found: list[TechEvidence] = [
            TechEvidence(
                technology="Docker",
                evidence_type=EvidenceType.SOURCE_CODE,
                source=f"Dockerfile: {file.repository}",
                source_url=url,
                details="Dockerfile present",
                confidence=EVIDENCE_WEIGHTS[EvidenceType.SOURCE_CODE],
                repository=file.repository,
            )
        ]

        _IMAGE_TECH = {
            "python": "Python", "node": "Node.js", "postgres": "PostgreSQL",
            "redis": "Redis", "java": "Java", "openjdk": "Java",
            "golang": "Go", "ruby": "Ruby", "nginx": "Nginx",
            "mongo": "MongoDB", "mysql": "MySQL",
        }
        for line in file.content.splitlines():
            if line.strip().upper().startswith("FROM "):
                image = line.strip()[5:].split()[0].lower()
                for key, tech in _IMAGE_TECH.items():
                    if key in image:
                        found.append(TechEvidence(
                            technology=tech,
                            evidence_type=EvidenceType.SOURCE_CODE,
                            source=f"Dockerfile: {file.repository}",
                            source_url=url,
                            details=f"Base image: {image}",
                            confidence=EVIDENCE_WEIGHTS[EvidenceType.SOURCE_CODE],
                            repository=file.repository,
                        ))
                        break

        self._evidence.extend(found)
        return found

    # ── Commits ───────────────────────────────────────────────

    def extract_from_commits(
        self, commits: list[CommitInfo], username: str,
    ) -> list[TechEvidence]:
        if not commits:
            return []
        messages = " ".join(c.message for c in commits).lower()
        found = self._keyword_scan(
            messages,
            evidence_type=EvidenceType.COMMIT,
            source=f"Commits by {username}",
            source_url=f"https://github.com/{commits[0].repository}/commits",
            prefix="Commits",
            repository=commits[0].repository,
        )
        self._evidence.extend(found)
        return found

    # ── Deduplication ─────────────────────────────────────────

    def deduplicate(self) -> list[TechEvidence]:
        """Keep highest-confidence evidence per (tech, type, repo)."""
        best: dict[tuple, TechEvidence] = {}
        for ev in self._evidence:
            key = (ev.technology, ev.evidence_type, ev.repository)
            if key not in best or ev.confidence > best[key].confidence:
                best[key] = ev
        self._evidence = list(best.values())
        return self._evidence

    # ── Internal helper ───────────────────────────────────────

    @staticmethod
    def _keyword_scan(
        text: str,
        *,
        evidence_type: EvidenceType,
        source: str,
        source_url: str,
        prefix: str,
        repository: str | None = None,
    ) -> list[TechEvidence]:
        found: list[TechEvidence] = []
        for tech, keywords in TECH_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    found.append(TechEvidence(
                        technology=tech,
                        evidence_type=evidence_type,
                        source=source,
                        source_url=source_url,
                        details=f"{prefix} mentions '{kw}'",
                        confidence=EVIDENCE_WEIGHTS[evidence_type],
                        repository=repository,
                    ))
                    break  # one match per tech is enough
        return found
