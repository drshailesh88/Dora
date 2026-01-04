"""
Morning Briefing Generator

Generates personalized daily briefings for doctors.
Includes patient previews, clinical pearls, trending queries, and alerts.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from src.engagement.models import (
    DailyBriefing,
    BriefingItemType,
    NotificationPreference,
)


class BriefingGenerator:
    """Generates personalized morning briefings."""

    def __init__(self):
        """Initialize briefing generator."""
        self.greetings = [
            "Good morning, Dr. {name}!",
            "Hello, Dr. {name}!",
            "Good day, Dr. {name}!",
        ]

    def generate_briefing(
        self,
        user_id: str,
        user_profile: dict[str, Any],
        preferences: NotificationPreference,
        emr_data: Optional[dict[str, Any]] = None,
        alerts: list[dict[str, Any]] = None,
        trending: list[dict[str, Any]] = None,
        pearl: Optional[dict[str, Any]] = None,
    ) -> DailyBriefing:
        """
        Generate daily briefing for a user.

        Args:
            user_id: User ID
            user_profile: Doctor profile with specialty, etc.
            preferences: User notification preferences
            emr_data: Optional EMR data (patients scheduled today)
            alerts: List of pending alerts
            trending: List of trending queries
            pearl: Clinical pearl for today

        Returns:
            DailyBriefing object
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        specialty = user_profile.get("specialty", "medicine")
        name = user_profile.get("name", "Doctor")

        # Generate greeting
        greeting = self._generate_greeting(name)

        # Build items list
        items = []
        patient_count = 0

        # 1. Patient preview (from EMR)
        if emr_data and emr_data.get("patients_today"):
            patient_item = self._create_patient_preview(emr_data)
            items.append(patient_item)
            patient_count = len(emr_data["patients_today"])

        # 2. Clinical pearl
        if pearl and preferences.include_pearls:
            pearl_item = self._create_pearl_item(pearl)
            items.append(pearl_item)

        # 3. Critical alerts (high/critical severity only in briefing)
        if alerts:
            critical_alerts = [
                a for a in alerts
                if a.get("severity") in ["high", "critical"]
            ]
            for alert in critical_alerts[:2]:  # Max 2 critical in briefing
                alert_item = self._create_alert_item(alert)
                items.append(alert_item)

        # 4. Trending queries
        if trending and preferences.include_trending:
            trending_item = self._create_trending_item(trending[:3], specialty)
            items.append(trending_item)

        # 5. Research highlights
        if alerts:
            research_alerts = [
                a for a in alerts
                if a.get("type") == "research_paper"
            ]
            if research_alerts:
                research_item = self._create_research_item(research_alerts[:2])
                items.append(research_item)

        # Limit items to user preference
        items = items[:preferences.max_briefing_items]

        # Generate summary line
        summary_line = self._generate_summary(
            patient_count=patient_count,
            alert_count=len([a for a in (alerts or []) if a.get("severity") in ["high", "critical"]]),
            research_count=len([a for a in (alerts or []) if a.get("type") == "research_paper"]),
            specialty=specialty,
        )

        return DailyBriefing(
            user_id=user_id,
            date=today,
            greeting=greeting,
            summary_line=summary_line,
            items=items,
            specialty=specialty,
            patient_count_today=patient_count,
        )

    def _generate_greeting(self, name: str) -> str:
        """Generate personalized greeting."""
        import random
        template = random.choice(self.greetings)
        return template.format(name=name)

    def _generate_summary(
        self,
        patient_count: int,
        alert_count: int,
        research_count: int,
        specialty: str,
    ) -> str:
        """
        Generate one-line summary of the day.

        Args:
            patient_count: Number of patients today
            alert_count: Number of critical alerts
            research_count: Number of new research papers
            specialty: User's specialty

        Returns:
            Summary string
        """
        parts = []

        if patient_count > 0:
            parts.append(f"{patient_count} patient{'s' if patient_count != 1 else ''} scheduled")

        if alert_count > 0:
            parts.append(f"{alert_count} important alert{'s' if alert_count != 1 else ''}")

        if research_count > 0:
            parts.append(f"{research_count} new {specialty} paper{'s' if research_count != 1 else ''}")

        if not parts:
            return "Ready to help you today!"

        if len(parts) == 1:
            return parts[0].capitalize() + " today."
        elif len(parts) == 2:
            return f"{parts[0].capitalize()}, plus {parts[1]}."
        else:
            return f"{parts[0].capitalize()}, {parts[1]}, and {parts[2]}."

    def _create_patient_preview(self, emr_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create patient preview item.

        Args:
            emr_data: EMR data with patient list

        Returns:
            Briefing item dict
        """
        patients = emr_data.get("patients_today", [])
        patient_count = len(patients)

        # Summarize patient conditions
        conditions = []
        for patient in patients:
            if patient.get("reason"):
                conditions.append(patient["reason"])

        # Find notable conditions
        notable = []
        keywords = ["follow-up", "heart failure", "diabetes", "hypertension", "cancer", "surgery"]
        for kw in keywords:
            count = sum(1 for c in conditions if kw.lower() in c.lower())
            if count > 0:
                notable.append(f"{count} {kw}")

        content = f"You have {patient_count} patient{'s' if patient_count != 1 else ''} scheduled today"
        if notable:
            content += f", including {', '.join(notable[:2])}"

        return {
            "id": "patient_preview",
            "type": BriefingItemType.PATIENT_PREVIEW.value,
            "title": f"{patient_count} Patient{'s' if patient_count != 1 else ''} Today",
            "content": content,
            "icon": "👥",
            "priority": 1,
            "actionable": True,
            "action_url": "/app/emr/appointments",
            "metadata": {
                "patient_count": patient_count,
                "patients": patients[:5],  # Include first 5
            }
        }

    def _create_pearl_item(self, pearl: dict[str, Any]) -> dict[str, Any]:
        """
        Create clinical pearl item.

        Args:
            pearl: Clinical pearl data

        Returns:
            Briefing item dict
        """
        return {
            "id": pearl.get("id", "pearl"),
            "type": BriefingItemType.CLINICAL_PEARL.value,
            "title": "💡 Clinical Pearl",
            "content": pearl.get("content", ""),
            "icon": "💡",
            "priority": 2,
            "actionable": True,
            "action_url": f"/app/pearls/{pearl.get('id')}",
            "metadata": {
                "full_pearl": pearl,
                "specialty": pearl.get("specialty"),
                "category": pearl.get("category"),
            }
        }

    def _create_alert_item(self, alert: dict[str, Any]) -> dict[str, Any]:
        """
        Create alert item.

        Args:
            alert: Alert data

        Returns:
            Briefing item dict
        """
        alert_type = alert.get("type", "alert")
        severity = alert.get("severity", "medium")

        # Choose icon based on severity
        icon_map = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
            "info": "ℹ️",
        }
        icon = icon_map.get(severity, "⚠️")

        # Priority based on severity
        priority_map = {
            "critical": 0,
            "high": 1,
            "medium": 3,
            "low": 4,
            "info": 5,
        }
        priority = priority_map.get(severity, 3)

        return {
            "id": alert.get("id", "alert"),
            "type": self._map_alert_type(alert_type),
            "title": f"{icon} {alert.get('title', 'Alert')}",
            "content": alert.get("summary", alert.get("description", ""))[:200],
            "icon": icon,
            "priority": priority,
            "severity": severity,
            "actionable": True,
            "action_url": f"/app/alerts/{alert.get('id')}",
            "metadata": alert,
        }

    def _map_alert_type(self, alert_type: str) -> str:
        """Map alert type to briefing item type."""
        mapping = {
            "guideline_update": BriefingItemType.GUIDELINE_UPDATE.value,
            "drug_recall": BriefingItemType.DRUG_ALERT.value,
            "drug_safety": BriefingItemType.DRUG_ALERT.value,
            "research_paper": BriefingItemType.RESEARCH_ALERT.value,
        }
        return mapping.get(alert_type, BriefingItemType.SYSTEM_MESSAGE.value)

    def _create_trending_item(
        self,
        trending: list[dict[str, Any]],
        specialty: str,
    ) -> dict[str, Any]:
        """
        Create trending queries item.

        Args:
            trending: List of trending queries
            specialty: User's specialty

        Returns:
            Briefing item dict
        """
        if not trending:
            return None

        # Format trending list
        trending_list = []
        for i, item in enumerate(trending[:3], 1):
            query = item.get("query_text", "")
            count = item.get("query_count", 0)
            trending_list.append(f"{i}. {query} ({count} queries)")

        content = f"Top queries in {specialty} this week:\n" + "\n".join(trending_list)

        return {
            "id": "trending",
            "type": BriefingItemType.TRENDING_QUERY.value,
            "title": f"🔥 Trending in {specialty.title()}",
            "content": content,
            "icon": "🔥",
            "priority": 4,
            "actionable": True,
            "action_url": "/app/trending",
            "metadata": {
                "trending_queries": trending,
                "specialty": specialty,
            }
        }

    def _create_research_item(
        self,
        research_alerts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Create research highlights item.

        Args:
            research_alerts: List of research paper alerts

        Returns:
            Briefing item dict
        """
        if not research_alerts:
            return None

        count = len(research_alerts)
        first_paper = research_alerts[0]

        content = f"{count} new research paper{'s' if count != 1 else ''}\n\n"
        content += f"📄 {first_paper.get('title', 'New research')}\n"
        content += f"   {first_paper.get('journal', 'Journal')}"

        if count > 1:
            content += f"\n\n+ {count - 1} more paper{'s' if count > 2 else ''}"

        return {
            "id": "research",
            "type": BriefingItemType.RESEARCH_ALERT.value,
            "title": f"📚 New Research ({count})",
            "content": content,
            "icon": "📚",
            "priority": 3,
            "actionable": True,
            "action_url": "/app/research",
            "metadata": {
                "papers": research_alerts,
                "count": count,
            }
        }

    def should_send_briefing(
        self,
        user_id: str,
        preferences: NotificationPreference,
    ) -> bool:
        """
        Check if briefing should be sent today.

        Args:
            user_id: User ID
            preferences: User notification preferences

        Returns:
            True if briefing should be sent
        """
        if not preferences.briefing_enabled:
            return False

        # Check day of week
        today_weekday = datetime.utcnow().weekday()
        if today_weekday not in preferences.briefing_days:
            return False

        # Check if already sent today
        # (This would query database in real implementation)
        # For now, assume we need to send
        return True

    def get_optimal_send_time(
        self,
        preferences: NotificationPreference,
    ) -> datetime:
        """
        Get optimal time to send briefing.

        Args:
            preferences: User notification preferences

        Returns:
            Datetime when briefing should be sent
        """
        # Parse preferred time
        time_parts = preferences.briefing_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        # If learn_from_behavior is enabled and we have detected hours, use those
        if preferences.learn_from_behavior and preferences.detected_active_hours:
            # Find earliest active hour after 6am
            active_hours = sorted(preferences.detected_active_hours)
            for h in active_hours:
                if 6 <= h <= 10:  # Morning window
                    hour = h
                    minute = 0
                    break

        # Create datetime for today at preferred time
        today = datetime.utcnow().date()
        send_time = datetime.combine(today, datetime.min.time())
        send_time = send_time.replace(hour=hour, minute=minute)

        # If time has passed, schedule for tomorrow
        if send_time < datetime.utcnow():
            send_time += timedelta(days=1)

        return send_time
