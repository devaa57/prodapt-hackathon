"""Tests for evidence.py — deterministic extraction with mock data (no API)."""
import pytest

from github_verifier.evidence import EvidenceExtractor
from github_verifier.models import (
    EvidenceType,
    FileContent,
    GitHubProfile,
    Repository,
    CommitInfo,
)
from datetime import datetime, timezone

_NOW = datetime.now(timezone.utc)


def _profile(**overrides) -> GitHubProfile:
    defaults = dict(
        username="testuser", name="Test User", bio=None, company=None,
        location=None, public_repos=5, followers=10, following=5,
        created_at=_NOW, profile_url="https://github.com/testuser",
    )
    defaults.update(overrides)
    return GitHubProfile(**defaults)


def _repo(**overrides) -> Repository:
    defaults = dict(
        name="my-repo", full_name="testuser/my-repo", description=None,
        url="https://api.github.com/repos/testuser/my-repo",
        html_url="https://github.com/testuser/my-repo",
        owner="testuser", primary_language=None, topics=[], stars=0,
        forks=0, created_at=_NOW, updated_at=_NOW, default_branch="main",
        is_fork=False, is_archived=False, size_kb=100,
    )
    defaults.update(overrides)
    return Repository(**defaults)


def _file(name: str, content: str, repo: str = "testuser/my-repo") -> FileContent:
    return FileContent(
        path=name, name=name, content=content, size=len(content),
        download_url=f"https://raw.githubusercontent.com/{repo}/HEAD/{name}",
        repository=repo,
    )


# ═══════════════════════════════════════════════════════════════
# Profile extraction
# ═══════════════════════════════════════════════════════════════

class TestProfileExtraction:
    def test_bio_with_tech_keywords(self):
        ext = EvidenceExtractor()
        profile = _profile(bio="Python developer working with PostgreSQL and Docker")
        ev = ext.extract_from_profile(profile)
        techs = {e.technology for e in ev}
        assert "Python" in techs
        assert "PostgreSQL" in techs
        assert "Docker" in techs

    def test_empty_bio(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_profile(_profile(bio=None))
        assert ev == []

    def test_evidence_type_is_profile(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_profile(_profile(bio="I love Python"))
        assert all(e.evidence_type == EvidenceType.PROFILE for e in ev)


# ═══════════════════════════════════════════════════════════════
# Repository metadata extraction
# ═══════════════════════════════════════════════════════════════

class TestRepoExtraction:
    def test_primary_language(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_repository(_repo(primary_language="Python"))
        techs = {e.technology for e in ev}
        assert "Python" in techs

    def test_topics(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_repository(_repo(topics=["docker", "postgresql"]))
        techs = {e.technology for e in ev}
        assert "Docker" in techs
        assert "PostgreSQL" in techs

    def test_description(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_repository(
            _repo(description="A FastAPI REST API for managing tasks")
        )
        techs = {e.technology for e in ev}
        assert "FastAPI" in techs
        assert "REST API" in techs


# ═══════════════════════════════════════════════════════════════
# Dependency extraction
# ═══════════════════════════════════════════════════════════════

class TestDependencyExtraction:
    def test_package_json(self):
        ext = EvidenceExtractor()
        content = '{"dependencies":{"express":"^4.18","pg":"^8.11","redis":"^4.6"}}'
        ev = ext.extract_from_dependencies(_file("package.json", content))
        techs = {e.technology for e in ev}
        assert "Express.js" in techs
        assert "PostgreSQL" in techs
        assert "Redis" in techs
        assert "Node.js" in techs  # manifest implies ecosystem

    def test_requirements_txt(self):
        ext = EvidenceExtractor()
        content = "django==4.2\npsycopg2-binary>=2.9\ncelery\n# comment\n"
        ev = ext.extract_from_dependencies(_file("requirements.txt", content))
        techs = {e.technology for e in ev}
        assert "Django" in techs
        assert "PostgreSQL" in techs
        assert "Celery" in techs
        assert "Python" in techs

    def test_empty_package_json(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_dependencies(_file("package.json", "{}"))
        # Should still have Node.js from manifest detection
        techs = {e.technology for e in ev}
        assert "Node.js" in techs

    def test_confidence_is_dependency_weight(self):
        ext = EvidenceExtractor()
        content = '{"dependencies":{"express":"^4"}}'
        ev = ext.extract_from_dependencies(_file("package.json", content))
        dep_ev = [e for e in ev if e.evidence_type == EvidenceType.DEPENDENCY]
        assert all(e.confidence == 0.90 for e in dep_ev)


# ═══════════════════════════════════════════════════════════════
# README extraction
# ═══════════════════════════════════════════════════════════════

class TestReadmeExtraction:
    def test_readme_keyword_scan(self):
        ext = EvidenceExtractor()
        content = "# My App\nBuilt with Django and PostgreSQL.\nDeployed on Docker."
        ev = ext.extract_from_readme(_file("README.md", content))
        techs = {e.technology for e in ev}
        assert "Django" in techs
        assert "PostgreSQL" in techs
        assert "Docker" in techs

    def test_evidence_type_is_readme(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_readme(_file("README.md", "Uses Redis for caching"))
        assert all(e.evidence_type == EvidenceType.README for e in ev)


# ═══════════════════════════════════════════════════════════════
# Dockerfile extraction
# ═══════════════════════════════════════════════════════════════

class TestDockerfileExtraction:
    def test_docker_present(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_dockerfile(_file("Dockerfile", "FROM python:3.11\nRUN pip install fastapi"))
        techs = {e.technology for e in ev}
        assert "Docker" in techs
        assert "Python" in techs

    def test_node_base_image(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_dockerfile(_file("Dockerfile", "FROM node:18-alpine"))
        techs = {e.technology for e in ev}
        assert "Node.js" in techs

    def test_postgres_base_image(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_dockerfile(_file("Dockerfile", "FROM postgres:16"))
        techs = {e.technology for e in ev}
        assert "PostgreSQL" in techs


# ═══════════════════════════════════════════════════════════════
# Commit extraction
# ═══════════════════════════════════════════════════════════════

class TestCommitExtraction:
    def test_commit_message_keywords(self):
        ext = EvidenceExtractor()
        commits = [
            CommitInfo(sha="abc", date=_NOW, message="Add PostgreSQL migration",
                       repository="testuser/my-repo"),
            CommitInfo(sha="def", date=_NOW, message="Fix Redis cache timeout",
                       repository="testuser/my-repo"),
        ]
        ev = ext.extract_from_commits(commits, "testuser")
        techs = {e.technology for e in ev}
        assert "PostgreSQL" in techs
        assert "Redis" in techs

    def test_empty_commits(self):
        ext = EvidenceExtractor()
        ev = ext.extract_from_commits([], "testuser")
        assert ev == []


# ═══════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════

class TestDeduplication:
    def test_keeps_highest_confidence(self):
        ext = EvidenceExtractor()
        # Add same tech twice from different sources
        ext.extract_from_readme(_file("README.md", "Uses PostgreSQL"))
        ext.extract_from_dependencies(
            _file("requirements.txt", "psycopg2-binary\n")
        )
        deduped = ext.deduplicate()
        pg_ev = [e for e in deduped if e.technology == "PostgreSQL"]
        # DEPENDENCY (0.90) > README (0.60), so DEPENDENCY survives per type
        dep_ev = [e for e in pg_ev if e.evidence_type == EvidenceType.DEPENDENCY]
        readme_ev = [e for e in pg_ev if e.evidence_type == EvidenceType.README]
        # Both types should survive (dedup is per tech+type+repo)
        assert len(dep_ev) >= 1
        assert len(readme_ev) >= 1
