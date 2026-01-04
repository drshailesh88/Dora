"""
Message Templates

Pre-formatted message templates for WhatsApp responses.
"""

from typing import Optional
from src.core.models import MedicalAnswer, Citation, ConfidenceLevel
from src.drugs.interactions import DrugInteraction


class MessageTemplates:
    """WhatsApp message templates"""

    @staticmethod
    def get_welcome_message() -> str:
        """Welcome message for new users"""
        return """👋 *Welcome to Dora!*

I'm your AI medical knowledge assistant, powered by evidence-based medical literature.

*What I can do:*
• Answer medical questions
• Check drug interactions
• Medical calculators
• Voice queries (send voice notes!)
• Share answers with patients

*Privacy First:*
All conversations are private and HIPAA-compliant.

How can I help you today?"""

    @staticmethod
    def get_help_message() -> str:
        """Help message"""
        return """📚 *How to Use Dora*

*Ask Questions:*
Just send your medical question as text or voice note.

Example: "What's the dose of amoxicillin for a child?"

*Drug Interactions:*
Send: "Check [drug1] and [drug2]"

Example: "Check clopidogrel and omeprazole"

*Medical Calculators:*
Reply "calculator" to see available options

*Link Your Account:*
Reply "link" to connect with your Dora account for premium features

*Commands:*
• help - Show this message
• link - Link your account
• settings - Update preferences

Questions? Contact support@docassist.in"""

    @staticmethod
    def format_query_response(
        answer: MedicalAnswer,
        format_type: str = "concise",
    ) -> str:
        """
        Format medical answer for WhatsApp.

        Args:
            answer: MedicalAnswer object
            format_type: concise, detailed, or patient_friendly

        Returns:
            Formatted text
        """
        if format_type == "patient_friendly":
            return MessageTemplates._format_patient_friendly(answer)
        elif format_type == "detailed":
            return MessageTemplates._format_detailed(answer)
        else:
            return MessageTemplates._format_concise(answer)

    @staticmethod
    def _format_concise(answer: MedicalAnswer) -> str:
        """Concise format for quick reference"""
        lines = []

        # Confidence indicator
        confidence_emoji = {
            ConfidenceLevel.HIGH: "✅",
            ConfidenceLevel.MEDIUM: "⚠️",
            ConfidenceLevel.LOW: "❓",
        }
        emoji = confidence_emoji.get(answer.confidence, "")

        # Answer
        lines.append(f"{emoji} *Answer:*\n{answer.answer}")

        # Warnings (if any)
        if answer.warnings:
            lines.append("\n⚠️ *Important:*")
            for warning in answer.warnings:
                lines.append(f"• {warning}")

        # Top citation
        if answer.citations:
            top_citation = answer.citations[0]
            lines.append(f"\n📖 Source: {top_citation.source}")

        # Related queries
        if answer.related_queries:
            lines.append("\n💡 Related:")
            for q in answer.related_queries[:2]:
                lines.append(f"• {q}")

        return "\n".join(lines)

    @staticmethod
    def _format_detailed(answer: MedicalAnswer) -> str:
        """Detailed format with full citations"""
        lines = []

        # Confidence
        lines.append(f"*Confidence:* {answer.confidence.value.upper()}")
        lines.append("")

        # Answer
        lines.append("*Answer:*")
        lines.append(answer.answer)
        lines.append("")

        # Warnings
        if answer.warnings:
            lines.append("⚠️ *Warnings:*")
            for warning in answer.warnings:
                lines.append(f"• {warning}")
            lines.append("")

        # Citations
        if answer.citations:
            lines.append("📚 *Sources:*")
            for i, cite in enumerate(answer.citations[:5], 1):
                lines.append(f"[{i}] {cite.source}")
                if cite.section:
                    lines.append(f"    {cite.section}")
            lines.append("")

        # Related queries
        if answer.related_queries:
            lines.append("💡 *Related Questions:*")
            for q in answer.related_queries[:3]:
                lines.append(f"• {q}")

        return "\n".join(lines)

    @staticmethod
    def _format_patient_friendly(answer: MedicalAnswer) -> str:
        """Patient-friendly format (simplified language)"""
        lines = []

        lines.append("*For Your Patient:*")
        lines.append("")

        # Simplified answer (would ideally use LLM to simplify)
        lines.append(answer.answer)
        lines.append("")

        # Important notes
        if answer.warnings:
            lines.append("*Important:*")
            for warning in answer.warnings:
                lines.append(f"• {warning}")
            lines.append("")

        lines.append("_This information is from medical literature. Always consult your doctor._")

        return "\n".join(lines)

    @staticmethod
    def format_drug_interaction_response(
        drugs: list[str],
        interactions: list[DrugInteraction],
    ) -> str:
        """Format drug interaction check results"""
        lines = []

        # Header
        drugs_text = " & ".join(drugs)
        lines.append(f"💊 *Drug Interaction Check*")
        lines.append(f"Drugs: {drugs_text}")
        lines.append("")

        if not interactions:
            lines.append("✅ *No known interactions found*")
            lines.append("")
            lines.append("However, always verify with current drug databases and consider patient-specific factors.")
        else:
            lines.append(f"⚠️ *{len(interactions)} Interaction(s) Found*")
            lines.append("")

            for i, interaction in enumerate(interactions, 1):
                # Severity emoji
                severity_emoji = {
                    "major": "🔴",
                    "moderate": "🟡",
                    "minor": "🟢",
                }
                emoji = severity_emoji.get(interaction.severity.value, "⚠️")

                lines.append(f"{emoji} *{i}. {interaction.drug1} ↔ {interaction.drug2}*")
                lines.append(f"Severity: {interaction.severity.value.upper()}")
                lines.append("")
                lines.append(f"_{interaction.description}_")
                lines.append("")

                if interaction.management:
                    lines.append(f"*Management:* {interaction.management}")
                    lines.append("")

        lines.append("_Always check current databases and clinical guidelines._")

        return "\n".join(lines)

    @staticmethod
    def format_calculator_result(
        calculator_name: str,
        result: dict,
    ) -> str:
        """Format medical calculator results"""
        lines = []

        lines.append(f"📊 *{calculator_name}*")
        lines.append("")

        # Format result based on calculator type
        if "score" in result:
            lines.append(f"*Score:* {result['score']}")

        if "interpretation" in result:
            lines.append(f"*Interpretation:* {result['interpretation']}")

        if "risk" in result:
            lines.append(f"*Risk:* {result['risk']}")

        if "recommendation" in result:
            lines.append("")
            lines.append(f"*Recommendation:*")
            lines.append(result['recommendation'])

        return "\n".join(lines)

    @staticmethod
    def get_error_message() -> str:
        """Generic error message"""
        return """Sorry, I encountered an error processing your request.

Please try again or contact support if the issue persists.

Support: support@docassist.in"""

    @staticmethod
    def get_linking_instructions(link_code: str) -> str:
        """Account linking instructions"""
        return f"""🔗 *Link Your Account*

Your link code is: *{link_code}*

This code expires in 15 minutes.

*Steps to link:*
1. Open Dora web app or mobile app
2. Go to Settings → WhatsApp
3. Enter this code

*Benefits of linking:*
• Access your query history
• Sync with EMR
• Premium features
• Personalized recommendations"""

    @staticmethod
    def get_linked_confirmation() -> str:
        """Account linked confirmation"""
        return """✅ *Account Linked Successfully!*

You now have access to:
• Query history
• EMR integration
• Premium features
• Personalized recommendations

Start asking medical questions!"""

    @staticmethod
    def get_unlinked_confirmation() -> str:
        """Account unlinked confirmation"""
        return """🔓 *Account Unlinked*

Your WhatsApp is no longer linked to your Dora account.

You can still use basic features. Reply "link" to reconnect."""

    @staticmethod
    def format_daily_briefing(stats: dict) -> str:
        """Format daily briefing"""
        lines = []

        lines.append("📊 *Daily Briefing*")
        lines.append("")

        lines.append(f"• Queries today: {stats.get('queries_today', 0)}")
        lines.append(f"• Total queries: {stats.get('total_queries', 0)}")
        lines.append(f"• Active users: {stats.get('active_users', 0)}")

        if stats.get("trending_topics"):
            lines.append("")
            lines.append("*Trending Topics:*")
            for topic in stats["trending_topics"][:3]:
                lines.append(f"• {topic}")

        return "\n".join(lines)

    @staticmethod
    def format_research_alert(alert: dict) -> str:
        """Format research update alert"""
        lines = []

        lines.append("🔬 *New Research Alert*")
        lines.append("")

        lines.append(f"*{alert.get('title')}*")
        lines.append("")

        if alert.get("summary"):
            lines.append(alert["summary"])
            lines.append("")

        if alert.get("journal"):
            lines.append(f"Published in: {alert['journal']}")

        if alert.get("url"):
            lines.append(f"Read more: {alert['url']}")

        return "\n".join(lines)

    @staticmethod
    def format_notification(notification_type: str, data: dict) -> str:
        """Format various notification types"""
        if notification_type == "payment_due":
            return f"""💳 *Payment Reminder*

Your subscription payment of ₹{data.get('amount')} is due on {data.get('due_date')}.

Pay now to continue using premium features."""

        elif notification_type == "license_expiring":
            return f"""⏰ *License Expiring Soon*

Your Dora license expires in {data.get('days_remaining')} days.

Renew now to avoid interruption."""

        elif notification_type == "new_feature":
            return f"""✨ *New Feature Available*

{data.get('feature_name')}

{data.get('description')}

Try it now!"""

        else:
            return f"Notification: {data.get('message', 'No details available')}"
