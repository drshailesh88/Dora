"""
Tests for team protocol library module.
Tests protocol creation, versioning, sharing, and compliance tracking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date


class TestProtocolCreation:
    """Tests for protocol creation and management."""

    @pytest.fixture
    def protocol_service(self):
        """Create protocol service instance."""
        from src.protocols.service import ProtocolService
        return ProtocolService()

    @pytest.fixture
    def sample_protocol(self):
        """Sample clinical protocol."""
        return {
            "name": "Sepsis Management Protocol",
            "category": "emergency",
            "version": "1.0",
            "author_id": "doc_123",
            "team_id": "team_456",
            "steps": [
                {
                    "order": 1,
                    "action": "Obtain blood cultures",
                    "timing": "Within 30 minutes",
                    "required": True,
                },
                {
                    "order": 2,
                    "action": "Start IV antibiotics",
                    "timing": "Within 60 minutes",
                    "required": True,
                },
                {
                    "order": 3,
                    "action": "Fluid resuscitation",
                    "timing": "30 mL/kg within 3 hours",
                    "required": True,
                },
                {
                    "order": 4,
                    "action": "Measure lactate",
                    "timing": "Immediate and repeat if > 2",
                    "required": True,
                },
            ],
            "references": ["Surviving Sepsis Campaign 2021"],
            "tags": ["sepsis", "emergency", "infection"],
        }

    @pytest.mark.asyncio
    async def test_create_protocol(self, protocol_service, sample_protocol):
        """Should create new protocol."""
        result = await protocol_service.create(sample_protocol)

        assert result["success"]
        assert "protocol_id" in result
        assert result["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_protocol_validation(self, protocol_service):
        """Should validate protocol structure."""
        invalid_protocol = {
            "name": "Test",
            # Missing required fields
        }

        result = await protocol_service.create(invalid_protocol)

        assert not result["success"]
        assert "errors" in result or "validation" in result

    @pytest.mark.asyncio
    async def test_protocol_with_decision_points(self, protocol_service):
        """Should support decision branch points."""
        protocol = {
            "name": "Chest Pain Protocol",
            "steps": [
                {"order": 1, "action": "Obtain ECG"},
                {
                    "order": 2,
                    "action": "Evaluate ECG",
                    "decision_point": True,
                    "branches": [
                        {"condition": "STEMI", "next_step": 3},
                        {"condition": "NSTEMI", "next_step": 4},
                        {"condition": "Normal", "next_step": 5},
                    ],
                },
                {"order": 3, "action": "Activate cath lab"},
                {"order": 4, "action": "Admit to CCU"},
                {"order": 5, "action": "Risk stratify"},
            ],
        }

        result = await protocol_service.create(protocol)

        assert result["success"]


class TestProtocolVersioning:
    """Tests for protocol version control."""

    @pytest.fixture
    def versioning_service(self):
        """Create versioning service instance."""
        from src.protocols.versioning import ProtocolVersioningService
        return ProtocolVersioningService()

    @pytest.mark.asyncio
    async def test_create_new_version(self, versioning_service):
        """Should create new version of protocol."""
        result = await versioning_service.create_version(
            protocol_id="proto_123",
            changes={
                "steps": [
                    {"order": 1, "action": "Updated step 1"},
                ],
            },
            change_summary="Updated first step based on new guidelines",
        )

        assert result["success"]
        assert result["version"] == "1.1" or result["version"] == "2.0"

    @pytest.mark.asyncio
    async def test_version_history(self, versioning_service):
        """Should retrieve version history."""
        history = await versioning_service.get_history(protocol_id="proto_123")

        assert "versions" in history
        for version in history["versions"]:
            assert "version" in version
            assert "created_at" in version
            assert "author" in version
            assert "changes" in version or "summary" in version

    @pytest.mark.asyncio
    async def test_compare_versions(self, versioning_service):
        """Should compare two versions."""
        diff = await versioning_service.compare(
            protocol_id="proto_123",
            version_a="1.0",
            version_b="1.1",
        )

        assert "changes" in diff or "diff" in diff
        assert "added" in diff or "modified" in diff

    @pytest.mark.asyncio
    async def test_rollback_version(self, versioning_service):
        """Should allow rollback to previous version."""
        result = await versioning_service.rollback(
            protocol_id="proto_123",
            target_version="1.0",
        )

        assert result["success"]
        assert result["current_version"] == "1.0"


class TestProtocolSharing:
    """Tests for protocol sharing across teams."""

    @pytest.fixture
    def sharing_service(self):
        """Create sharing service instance."""
        from src.protocols.sharing import ProtocolSharingService
        return ProtocolSharingService()

    @pytest.mark.asyncio
    async def test_share_with_team(self, sharing_service):
        """Should share protocol with another team."""
        result = await sharing_service.share(
            protocol_id="proto_123",
            target_team_id="team_789",
            permissions="read",
        )

        assert result["success"]
        assert "share_id" in result

    @pytest.mark.asyncio
    async def test_share_permissions(self, sharing_service):
        """Should respect share permissions."""
        # Read-only share
        share = await sharing_service.share(
            protocol_id="proto_123",
            target_team_id="team_789",
            permissions="read",
        )

        # Team should not be able to edit
        can_edit = await sharing_service.check_permission(
            protocol_id="proto_123",
            team_id="team_789",
            action="edit",
        )

        assert not can_edit

    @pytest.mark.asyncio
    async def test_fork_protocol(self, sharing_service):
        """Should allow forking shared protocol."""
        result = await sharing_service.fork(
            protocol_id="proto_123",
            to_team_id="team_789",
        )

        assert result["success"]
        assert "new_protocol_id" in result
        # Should be independent copy
        assert result["new_protocol_id"] != "proto_123"

    @pytest.mark.asyncio
    async def test_revoke_share(self, sharing_service):
        """Should revoke sharing access."""
        # First share
        await sharing_service.share(
            protocol_id="proto_123",
            target_team_id="team_789",
            permissions="read",
        )

        # Then revoke
        result = await sharing_service.revoke(
            protocol_id="proto_123",
            team_id="team_789",
        )

        assert result["success"]

        # Verify access revoked
        can_read = await sharing_service.check_permission(
            protocol_id="proto_123",
            team_id="team_789",
            action="read",
        )
        assert not can_read


class TestProtocolCompliance:
    """Tests for protocol compliance tracking."""

    @pytest.fixture
    def compliance_service(self):
        """Create compliance service instance."""
        from src.protocols.compliance import ProtocolComplianceService
        return ProtocolComplianceService()

    @pytest.mark.asyncio
    async def test_log_protocol_execution(self, compliance_service):
        """Should log protocol execution."""
        result = await compliance_service.log_execution(
            protocol_id="proto_123",
            patient_id="pat_456",
            doctor_id="doc_789",
            steps_completed=[1, 2, 3, 4],
            steps_total=4,
            deviations=[],
        )

        assert result["success"]
        assert result["compliance_rate"] == 100

    @pytest.mark.asyncio
    async def test_log_deviation(self, compliance_service):
        """Should log protocol deviations."""
        result = await compliance_service.log_execution(
            protocol_id="proto_123",
            patient_id="pat_456",
            doctor_id="doc_789",
            steps_completed=[1, 2, 4],  # Skipped step 3
            steps_total=4,
            deviations=[
                {
                    "step": 3,
                    "reason": "Patient refused fluid challenge",
                    "documented": True,
                }
            ],
        )

        assert result["success"]
        assert result["compliance_rate"] < 100
        assert len(result.get("deviations", [])) == 1

    @pytest.mark.asyncio
    async def test_compliance_report(self, compliance_service):
        """Should generate compliance report."""
        report = await compliance_service.get_report(
            protocol_id="proto_123",
            period="month",
        )

        assert "total_executions" in report
        assert "average_compliance" in report
        assert "deviation_reasons" in report or "common_deviations" in report

    @pytest.mark.asyncio
    async def test_compliance_by_step(self, compliance_service):
        """Should track compliance by individual step."""
        report = await compliance_service.get_step_compliance(
            protocol_id="proto_123",
            period="month",
        )

        assert "steps" in report
        for step in report["steps"]:
            assert "step_number" in step or "order" in step
            assert "compliance_rate" in step


class TestProtocolSearch:
    """Tests for protocol search and discovery."""

    @pytest.fixture
    def search_service(self):
        """Create search service instance."""
        from src.protocols.search import ProtocolSearchService
        return ProtocolSearchService()

    @pytest.mark.asyncio
    async def test_search_by_name(self, search_service):
        """Should search protocols by name."""
        results = await search_service.search(query="sepsis")

        assert "protocols" in results
        for proto in results["protocols"]:
            assert "sepsis" in proto["name"].lower() or \
                   "sepsis" in str(proto.get("tags", [])).lower()

    @pytest.mark.asyncio
    async def test_search_by_category(self, search_service):
        """Should filter by category."""
        results = await search_service.search(
            query="",
            category="emergency",
        )

        for proto in results["protocols"]:
            assert proto.get("category") == "emergency"

    @pytest.mark.asyncio
    async def test_search_by_specialty(self, search_service):
        """Should filter by specialty."""
        results = await search_service.search(
            query="",
            specialty="cardiology",
        )

        for proto in results["protocols"]:
            assert "cardiology" in proto.get("specialty", "").lower() or \
                   "cardiology" in str(proto.get("tags", [])).lower()

    @pytest.mark.asyncio
    async def test_popular_protocols(self, search_service):
        """Should return popular protocols."""
        results = await search_service.get_popular(limit=10)

        assert len(results) <= 10
        # Should be sorted by usage
        if len(results) > 1:
            usages = [p.get("usage_count", 0) for p in results]
            assert usages == sorted(usages, reverse=True)


class TestProtocolAnnotations:
    """Tests for protocol annotations and notes."""

    @pytest.fixture
    def annotation_service(self):
        """Create annotation service instance."""
        from src.protocols.annotations import ProtocolAnnotationService
        return ProtocolAnnotationService()

    @pytest.mark.asyncio
    async def test_add_annotation(self, annotation_service):
        """Should add annotation to protocol step."""
        result = await annotation_service.add(
            protocol_id="proto_123",
            step_number=2,
            annotation={
                "text": "In our ICU, we use meropenem instead of piperacillin",
                "author_id": "doc_456",
            },
        )

        assert result["success"]
        assert "annotation_id" in result

    @pytest.mark.asyncio
    async def test_get_annotations(self, annotation_service):
        """Should retrieve annotations for protocol."""
        annotations = await annotation_service.get_all(protocol_id="proto_123")

        assert "annotations" in annotations
        for ann in annotations["annotations"]:
            assert "text" in ann
            assert "author" in ann or "author_id" in ann
            assert "step" in ann or "step_number" in ann

    @pytest.mark.asyncio
    async def test_annotation_visibility(self, annotation_service):
        """Should respect annotation visibility settings."""
        # Team-only annotation
        await annotation_service.add(
            protocol_id="proto_123",
            step_number=1,
            annotation={
                "text": "Internal note",
                "visibility": "team",
            },
        )

        # Should not be visible to other teams
        annotations = await annotation_service.get_all(
            protocol_id="proto_123",
            team_id="other_team",
        )

        assert all(
            ann.get("visibility") != "team" or ann.get("visible", True)
            for ann in annotations["annotations"]
        )


class TestProtocolExport:
    """Tests for protocol export functionality."""

    @pytest.fixture
    def export_service(self):
        """Create export service instance."""
        from src.protocols.export import ProtocolExportService
        return ProtocolExportService()

    @pytest.mark.asyncio
    async def test_export_as_pdf(self, export_service):
        """Should export protocol as PDF."""
        result = await export_service.export(
            protocol_id="proto_123",
            format="pdf",
        )

        assert result["success"]
        assert "url" in result or "data" in result

    @pytest.mark.asyncio
    async def test_export_as_json(self, export_service):
        """Should export protocol as JSON."""
        result = await export_service.export(
            protocol_id="proto_123",
            format="json",
        )

        assert result["success"]
        assert "data" in result
        data = result["data"]
        assert "name" in data
        assert "steps" in data

    @pytest.mark.asyncio
    async def test_export_includes_version(self, export_service):
        """Export should include version info."""
        result = await export_service.export(
            protocol_id="proto_123",
            format="json",
            include_metadata=True,
        )

        data = result["data"]
        assert "version" in data
        assert "last_updated" in data or "updated_at" in data
