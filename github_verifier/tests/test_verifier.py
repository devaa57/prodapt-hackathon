"""Tests for verifier.py — claim verification logic (no API calls)."""
import pytest

from github_verifier.models import (
    EvidenceType,
    TechEvidence,
    VerificationStatus,
)
from github_verifier.verifier import (
    calculate_confidence,
    determine_status,
    extract_technologies_from_claim,
    verify_claim,
)


# ═══════════════════════════════════════════════════════════════
# Technology extraction from claim text
# ═══════════════════════════════════════════════════════════════

class TestExtractTechnologies:
    def test_nodejs_express_postgres_redis(self):
        techs = extract_technologies_from_claim(
            "Built an e-commerce backend using Node.js, Express, PostgreSQL and Redis."
        )
        assert "Node.js" in techs
        assert "Express.js" in techs
        assert "PostgreSQL" in techs
        assert "Redis" in techs

    def test_python_fastapi(self):
        techs = extract_technologies_from_claim(
            "Developed a Python REST API using FastAPI and PostgreSQL."
        )
        assert "Python" in techs
        assert "FastAPI" in techs
        assert "PostgreSQL" in techs

    def test_docker_kubernetes(self):
        techs = extract_technologies_from_claim(
            "Deployed microservices using Docker and Kubernetes."
        )
        assert "Docker" in techs
        assert "Kubernetes" in techs

    def test_react_typescript(self):
        techs = extract_technologies_from_claim(
            "Built a React frontend with TypeScript."
        )
        assert "React" in techs
        assert "TypeScript" in techs

    def test_machine_learning(self):
        techs = extract_technologies_from_claim(
            "Experience in machine learning with TensorFlow."
        )
        assert "Machine Learning" in techs
        assert "TensorFlow" in techs

    def test_no_tech_found(self):
        techs = extract_technologies_from_claim(
            "Led a team of five engineers."
        )
        assert techs == []

    def test_case_insensitive(self):
        techs = extract_technologies_from_claim("Used POSTGRESQL and DOCKER")
        assert "PostgreSQL" in techs
        assert "Docker" in techs


# ═══════════════════════════════════════════════════════════════
# Confidence calculation
# ═══════════════════════════════════════════════════════════════

def _ev(tech: str, et: EvidenceType, conf: float) -> TechEvidence:
    return TechEvidence(
        technology=tech, evidence_type=et, source="test",
        source_url="https://example.com", details="test",
        confidence=conf,
    )


class TestCalculateConfidence:
    def test_empty(self):
        assert calculate_confidence([]) == 0.0

    def test_single_evidence(self):
        result = calculate_confidence([_ev("X", EvidenceType.DEPENDENCY, 0.90)])
        assert result == pytest.approx(0.90, abs=0.01)

    def test_multiple_evidence_increases(self):
        single = calculate_confidence([_ev("X", EvidenceType.DEPENDENCY, 0.90)])
        double = calculate_confidence([
            _ev("X", EvidenceType.DEPENDENCY, 0.90),
            _ev("X", EvidenceType.README, 0.60),
        ])
        assert double > single

    def test_never_exceeds_one(self):
        many = [_ev("X", EvidenceType.SOURCE_CODE, 0.95) for _ in range(10)]
        assert calculate_confidence(many) <= 1.0

    def test_diminishing_returns(self):
        two = calculate_confidence([
            _ev("X", EvidenceType.DEPENDENCY, 0.90),
            _ev("X", EvidenceType.README, 0.60),
        ])
        three = calculate_confidence([
            _ev("X", EvidenceType.DEPENDENCY, 0.90),
            _ev("X", EvidenceType.README, 0.60),
            _ev("X", EvidenceType.TOPIC, 0.50),
        ])
        # Third piece adds less than second
        assert three > two
        assert (three - two) < (two - 0.90)


# ═══════════════════════════════════════════════════════════════
# Status determination
# ═══════════════════════════════════════════════════════════════

class TestDetermineStatus:
    def test_no_evidence_is_inconclusive(self):
        assert determine_status(0.0, [], False) == VerificationStatus.INCONCLUSIVE

    def test_high_confidence_no_strong_is_supported(self):
        ev = [_ev("X", EvidenceType.README, 0.60)]
        assert determine_status(0.90, ev, has_strong=False) == VerificationStatus.SUPPORTED

    def test_high_confidence_with_strong_is_verified(self):
        ev = [_ev("X", EvidenceType.DEPENDENCY, 0.90)]
        assert determine_status(0.90, ev, has_strong=True) == VerificationStatus.VERIFIED

    def test_low_confidence_is_inconclusive(self):
        ev = [_ev("X", EvidenceType.TOPIC, 0.30)]
        assert determine_status(0.30, ev, has_strong=False) == VerificationStatus.INCONCLUSIVE

    def test_threshold_boundary_supported(self):
        ev = [_ev("X", EvidenceType.README, 0.50)]
        assert determine_status(0.50, ev, has_strong=False) == VerificationStatus.SUPPORTED


# ═══════════════════════════════════════════════════════════════
# Full claim verification
# ═══════════════════════════════════════════════════════════════

class TestVerifyClaim:
    def test_strong_match(self):
        """Claim with multiple strong evidence → VERIFIED or SUPPORTED."""
        evidence = [
            _ev("PostgreSQL", EvidenceType.DEPENDENCY, 0.90),
            _ev("PostgreSQL", EvidenceType.SOURCE_CODE, 0.95),
            _ev("Redis", EvidenceType.DEPENDENCY, 0.90),
            _ev("Express.js", EvidenceType.DEPENDENCY, 0.90),
            _ev("Node.js", EvidenceType.DEPENDENCY, 0.90),
        ]
        result = verify_claim(
            "Built an e-commerce backend using Node.js, Express, PostgreSQL and Redis.",
            evidence,
        )
        assert result.status in (VerificationStatus.VERIFIED, VerificationStatus.SUPPORTED)
        assert result.confidence > 0.7
        assert "PostgreSQL" in result.technologies_found
        assert "Redis" in result.technologies_found

    def test_no_evidence_is_inconclusive(self):
        """Missing evidence must NOT yield CONTRADICTED."""
        result = verify_claim(
            "Built a service with PostgreSQL and Redis.",
            [],  # no evidence at all
        )
        assert result.status == VerificationStatus.INCONCLUSIVE
        assert result.confidence == 0.0
        assert "PostgreSQL" in result.technologies_not_found
        assert "Redis" in result.technologies_not_found

    def test_partial_evidence(self):
        """Some techs found, others not → status reflects average."""
        evidence = [
            _ev("PostgreSQL", EvidenceType.DEPENDENCY, 0.90),
        ]
        result = verify_claim(
            "Built a backend using PostgreSQL and Redis.",
            evidence,
        )
        assert "PostgreSQL" in result.technologies_found
        assert "Redis" in result.technologies_not_found
        # Average of ~0.90 and 0.0 → ~0.45 → INCONCLUSIVE
        assert result.status == VerificationStatus.INCONCLUSIVE

    def test_no_recognisable_tech(self):
        result = verify_claim("Led sprint planning meetings.", [])
        assert result.status == VerificationStatus.INCONCLUSIVE
        assert result.confidence == 0.0
        assert "No recognisable" in result.reasoning

    def test_reasoning_mentions_found_techs(self):
        evidence = [_ev("Docker", EvidenceType.SOURCE_CODE, 0.95)]
        result = verify_claim("Deployed using Docker.", evidence)
        assert "Docker" in result.reasoning
        assert "SOURCE_CODE" in result.reasoning

    def test_reasoning_mentions_not_found(self):
        result = verify_claim("Used Kubernetes for orchestration.", [])
        assert "INCONCLUSIVE" in result.reasoning
        assert "private repos" in result.reasoning
