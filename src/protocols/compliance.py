"""
Protocol Compliance Tracking

Track protocol usage, adherence, and generate compliance reports.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .models import (
    Protocol,
    ProtocolCompliance,
    ComplianceReport,
)
from .storage import ProtocolStorage, get_protocol_storage


class ComplianceTracker:
    """
    Protocol compliance tracking and reporting.

    Tracks usage, measures adherence, and generates quality metrics.
    """

    def __init__(self, storage: Optional[ProtocolStorage] = None):
        self.storage = storage or get_protocol_storage()

    # Usage Tracking
    def record_usage(
        self,
        protocol_id: str,
        user_id: str,
        followed: bool = True,
        patient_id: Optional[str] = None,
        encounter_id: Optional[str] = None,
        deviation_reason: Optional[str] = None,
        deviation_sections: Optional[List[str]] = None,
        outcome_notes: Optional[str] = None,
    ) -> ProtocolCompliance:
        """Record protocol usage for compliance tracking."""
        record = ProtocolCompliance(
            protocol_id=protocol_id,
            user_id=user_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            followed=followed,
            deviation_reason=deviation_reason,
            deviation_sections=deviation_sections or [],
            outcome_notes=outcome_notes,
        )

        self.storage.create_compliance_record(record)

        # Update protocol usage count
        protocol = self.storage.get_protocol(protocol_id)
        if protocol:
            protocol.usage_count += 1
            protocol.last_used_at = datetime.utcnow()
            self.storage.update_protocol(protocol)

        return record

    # Reporting
    def generate_protocol_report(
        self,
        protocol_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[ComplianceReport]:
        """Generate compliance report for a specific protocol."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        # Default to last 30 days if no dates specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Get compliance records
        records = self.storage.get_compliance_records(
            protocol_id=protocol_id,
            start_date=start_date,
            end_date=end_date,
        )

        total_uses = len(records)
        compliant_uses = sum(1 for r in records if r.followed)

        # Calculate compliance rate
        compliance_rate = (compliant_uses / total_uses * 100) if total_uses > 0 else 0

        # Analyze deviations
        deviation_count = total_uses - compliant_uses
        common_deviations = self._analyze_deviations(records)

        report = ComplianceReport(
            protocol_id=protocol_id,
            protocol_title=protocol.title,
            total_uses=total_uses,
            compliant_uses=compliant_uses,
            compliance_rate=compliance_rate,
            deviation_count=deviation_count,
            common_deviations=common_deviations,
            period_start=start_date,
            period_end=end_date,
        )

        return report

    def generate_organization_report(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate compliance report for entire organization."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # Get all protocols for organization
        protocols = self.storage.list_protocols(
            organization_id=organization_id,
            limit=1000,
        )

        # Generate reports for each protocol
        protocol_reports = []
        total_uses = 0
        total_compliant = 0

        for protocol in protocols:
            report = self.generate_protocol_report(
                protocol.id,
                start_date,
                end_date,
            )
            if report and report.total_uses > 0:
                protocol_reports.append(report.to_dict())
                total_uses += report.total_uses
                total_compliant += report.compliant_uses

        overall_compliance = (total_compliant / total_uses * 100) if total_uses > 0 else 0

        # Identify most used protocols
        most_used = sorted(protocol_reports, key=lambda x: x['total_uses'], reverse=True)[:10]

        # Identify protocols with lowest compliance
        lowest_compliance = sorted(
            [r for r in protocol_reports if r['total_uses'] >= 5],
            key=lambda x: x['compliance_rate']
        )[:5]

        return {
            "organization_id": organization_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_protocols": len(protocols),
            "active_protocols": len([r for r in protocol_reports if r['total_uses'] > 0]),
            "total_uses": total_uses,
            "overall_compliance_rate": overall_compliance,
            "most_used_protocols": most_used,
            "protocols_needing_review": lowest_compliance,
            "all_protocols": protocol_reports,
        }

    def generate_user_report(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate compliance report for a specific user."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        records = self.storage.get_compliance_records(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        total_uses = len(records)
        compliant_uses = sum(1 for r in records if r.followed)
        compliance_rate = (compliant_uses / total_uses * 100) if total_uses > 0 else 0

        # Group by protocol
        protocol_usage = defaultdict(int)
        for record in records:
            protocol_usage[record.protocol_id] += 1

        # Most used protocols
        most_used = sorted(
            protocol_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Get protocol titles
        most_used_protocols = []
        for protocol_id, count in most_used:
            protocol = self.storage.get_protocol(protocol_id)
            if protocol:
                most_used_protocols.append({
                    "protocol_id": protocol_id,
                    "title": protocol.title,
                    "usage_count": count,
                })

        return {
            "user_id": user_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_uses": total_uses,
            "compliant_uses": compliant_uses,
            "compliance_rate": compliance_rate,
            "protocols_used": len(protocol_usage),
            "most_used_protocols": most_used_protocols,
        }

    def _analyze_deviations(
        self,
        records: List[ProtocolCompliance],
    ) -> List[Dict[str, Any]]:
        """Analyze common deviation patterns."""
        deviations = [r for r in records if not r.followed]

        # Count deviation reasons
        reason_counts = defaultdict(int)
        section_counts = defaultdict(int)

        for deviation in deviations:
            if deviation.deviation_reason:
                reason_counts[deviation.deviation_reason] += 1

            for section in deviation.deviation_sections:
                section_counts[section] += 1

        # Get top 5 reasons
        common_reasons = sorted(
            reason_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Get top 5 sections
        common_sections = sorted(
            section_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return [
            {
                "type": "reason",
                "value": reason,
                "count": count,
                "percentage": (count / len(deviations) * 100) if deviations else 0,
            }
            for reason, count in common_reasons
        ] + [
            {
                "type": "section",
                "value": section,
                "count": count,
                "percentage": (count / len(deviations) * 100) if deviations else 0,
            }
            for section, count in common_sections
        ]

    # Quality Improvement
    def identify_improvement_opportunities(
        self,
        organization_id: str,
        min_usage: int = 10,
        max_compliance_rate: float = 80.0,
    ) -> List[Dict[str, Any]]:
        """
        Identify protocols that need review or improvement.

        Returns protocols with sufficient usage but low compliance.
        """
        protocols = self.storage.list_protocols(
            organization_id=organization_id,
            limit=1000,
        )

        opportunities = []

        for protocol in protocols:
            if protocol.usage_count < min_usage:
                continue

            report = self.generate_protocol_report(protocol.id)
            if report and report.compliance_rate < max_compliance_rate:
                opportunities.append({
                    "protocol_id": protocol.id,
                    "title": protocol.title,
                    "usage_count": report.total_uses,
                    "compliance_rate": report.compliance_rate,
                    "deviation_count": report.deviation_count,
                    "common_deviations": report.common_deviations[:3],
                    "priority": "high" if report.compliance_rate < 60 else "medium",
                })

        # Sort by compliance rate (lowest first)
        opportunities.sort(key=lambda x: x['compliance_rate'])

        return opportunities

    def get_trending_protocols(
        self,
        organization_id: str,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Get protocols with increasing or decreasing usage."""
        end_date = datetime.utcnow()
        mid_date = end_date - timedelta(days=days)
        start_date = mid_date - timedelta(days=days)

        protocols = self.storage.list_protocols(
            organization_id=organization_id,
            limit=1000,
        )

        trending = []

        for protocol in protocols:
            # Get usage in two periods
            period1 = self.storage.get_compliance_records(
                protocol_id=protocol.id,
                start_date=start_date,
                end_date=mid_date,
            )

            period2 = self.storage.get_compliance_records(
                protocol_id=protocol.id,
                start_date=mid_date,
                end_date=end_date,
            )

            count1 = len(period1)
            count2 = len(period2)

            if count1 == 0:
                continue

            # Calculate percentage change
            change = ((count2 - count1) / count1) * 100

            if abs(change) > 20:  # At least 20% change
                trending.append({
                    "protocol_id": protocol.id,
                    "title": protocol.title,
                    "previous_period_usage": count1,
                    "current_period_usage": count2,
                    "change_percentage": change,
                    "trend": "up" if change > 0 else "down",
                })

        # Sort by absolute change
        trending.sort(key=lambda x: abs(x['change_percentage']), reverse=True)

        return trending


# Default instance
_tracker: Optional[ComplianceTracker] = None


def get_compliance_tracker() -> ComplianceTracker:
    """Get default compliance tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ComplianceTracker()
    return _tracker
