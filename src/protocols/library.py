"""
Protocol Library

Core protocol management functionality.
"""

from typing import Optional, List
from datetime import datetime
import uuid

from .models import Protocol, ProtocolCategory, ProtocolStatus
from .storage import ProtocolStorage, get_protocol_storage
from .templates import create_from_template, list_templates


class ProtocolLibrary:
    """
    Protocol library manager.

    Handles protocol creation, organization, search, and lifecycle.
    """

    def __init__(self, storage: Optional[ProtocolStorage] = None):
        self.storage = storage or get_protocol_storage()

    # Protocol CRUD
    def create_protocol(
        self,
        title: str,
        description: str,
        category: ProtocolCategory,
        user_id: str,
        content: str = "",
        tags: Optional[List[str]] = None,
        organization_id: Optional[str] = None,
        clinic_id: Optional[str] = None,
        is_clinic_wide: bool = False,
    ) -> Protocol:
        """Create a new protocol."""
        protocol = Protocol(
            title=title,
            description=description,
            category=category,
            tags=tags or [],
            content=content,
            created_by=user_id,
            organization_id=organization_id,
            clinic_id=clinic_id,
            status=ProtocolStatus.DRAFT,
            is_clinic_wide=is_clinic_wide,
            version_number="1.0",
        )

        self.storage.create_protocol(protocol)
        return protocol

    def create_from_template(
        self,
        template_id: str,
        user_id: str,
        title: Optional[str] = None,
        organization_id: Optional[str] = None,
        clinic_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[Protocol]:
        """Create a protocol from a template."""
        protocol = create_from_template(
            template_id,
            user_id,
            title=title,
            organization_id=organization_id,
            clinic_id=clinic_id,
            **kwargs,
        )

        if protocol:
            self.storage.create_protocol(protocol)

        return protocol

    def get_protocol(self, protocol_id: str) -> Optional[Protocol]:
        """Get a protocol by ID."""
        return self.storage.get_protocol(protocol_id)

    def update_protocol(
        self,
        protocol_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[ProtocolCategory] = None,
        evidence_grade: Optional[str] = None,
    ) -> Optional[Protocol]:
        """Update a protocol."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        if title:
            protocol.title = title
        if description:
            protocol.description = description
        if content:
            protocol.content = content
        if tags is not None:
            protocol.tags = tags
        if category:
            protocol.category = category
        if evidence_grade:
            protocol.evidence_grade = evidence_grade

        protocol.updated_at = datetime.utcnow()
        self.storage.update_protocol(protocol)
        return protocol

    def delete_protocol(self, protocol_id: str) -> bool:
        """Delete a protocol."""
        return self.storage.delete_protocol(protocol_id)

    # Search and filter
    def search_protocols(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        category: Optional[ProtocolCategory] = None,
        status: Optional[ProtocolStatus] = None,
        search_term: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Protocol]:
        """Search and filter protocols."""
        protocols = self.storage.list_protocols(
            user_id=user_id,
            organization_id=organization_id,
            category=category,
            status=status,
            is_template=is_template,
            search=search_term,
            offset=offset,
            limit=limit,
        )

        # Filter by tags if specified
        if tags:
            protocols = [
                p for p in protocols
                if any(tag in p.tags for tag in tags)
            ]

        return protocols

    def get_templates(self, category: Optional[ProtocolCategory] = None) -> List[Protocol]:
        """Get available templates."""
        return list_templates(category)

    # Lifecycle management
    def publish_protocol(
        self,
        protocol_id: str,
        user_id: str,
    ) -> Optional[Protocol]:
        """Publish a protocol."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        protocol.status = ProtocolStatus.PUBLISHED
        protocol.published_at = datetime.utcnow()
        protocol.reviewed_by = user_id
        protocol.reviewed_at = datetime.utcnow()

        self.storage.update_protocol(protocol)
        return protocol

    def archive_protocol(self, protocol_id: str) -> Optional[Protocol]:
        """Archive a protocol."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        protocol.status = ProtocolStatus.ARCHIVED
        self.storage.update_protocol(protocol)
        return protocol

    def submit_for_review(self, protocol_id: str) -> Optional[Protocol]:
        """Submit a protocol for review."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        protocol.status = ProtocolStatus.REVIEW
        self.storage.update_protocol(protocol)
        return protocol

    # Usage tracking
    def record_usage(
        self,
        protocol_id: str,
        user_id: str,
        patient_id: Optional[str] = None,
        encounter_id: Optional[str] = None,
    ) -> bool:
        """Record protocol usage."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return False

        protocol.usage_count += 1
        protocol.last_used_at = datetime.utcnow()
        self.storage.update_protocol(protocol)

        return True

    # Import/Export
    def export_protocol(
        self,
        protocol_id: str,
        format: str = "markdown",
    ) -> Optional[str]:
        """
        Export protocol to various formats.

        Formats: markdown, pdf, json
        """
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        if format == "markdown":
            return protocol.content

        elif format == "json":
            import json
            return json.dumps(protocol.to_dict(), indent=2)

        elif format == "pdf":
            # PDF export using reportlab
            from io import BytesIO
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
                from reportlab.platypus import Table, TableStyle
            except ImportError:
                # Fallback to markdown if reportlab not available
                return protocol.content

            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#2C3E50'),
                spaceAfter=12,
            )
            story.append(Paragraph(protocol.title, title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Metadata table
            metadata = [
                ['Category:', protocol.category.value.title()],
                ['Status:', protocol.status.value.title()],
                ['Version:', protocol.version_number],
                ['Created:', protocol.created_at.strftime('%Y-%m-%d')],
                ['Last Updated:', protocol.updated_at.strftime('%Y-%m-%d')],
            ]

            if protocol.evidence_grade:
                metadata.append(['Evidence Grade:', protocol.evidence_grade])

            t = Table(metadata, colWidths=[2*inch, 4*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * inch))

            # Description
            story.append(Paragraph('<b>Description:</b>', styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(protocol.description, styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

            # Tags
            if protocol.tags:
                story.append(Paragraph('<b>Tags:</b>', styles['Heading2']))
                story.append(Spacer(1, 0.1 * inch))
                tags_text = ', '.join(protocol.tags)
                story.append(Paragraph(tags_text, styles['Normal']))
                story.append(Spacer(1, 0.2 * inch))

            # Content
            story.append(Paragraph('<b>Protocol Content:</b>', styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))

            # Split content by lines and add as paragraphs
            for line in protocol.content.split('\n'):
                if line.strip():
                    # Handle markdown-style headers
                    if line.startswith('# '):
                        story.append(Paragraph(line[2:], styles['Heading2']))
                    elif line.startswith('## '):
                        story.append(Paragraph(line[3:], styles['Heading3']))
                    elif line.startswith('### '):
                        story.append(Paragraph(line[4:], styles['Heading4']))
                    else:
                        story.append(Paragraph(line, styles['Normal']))
                else:
                    story.append(Spacer(1, 0.1 * inch))

            # Build PDF
            doc.build(story)

            # Return PDF bytes as base64 string for storage/transmission
            import base64
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return base64.b64encode(pdf_bytes).decode('utf-8')

        return None

    def import_protocol(
        self,
        content: str,
        user_id: str,
        format: str = "markdown",
        title: Optional[str] = None,
        category: ProtocolCategory = ProtocolCategory.GENERAL,
        **kwargs,
    ) -> Optional[Protocol]:
        """
        Import protocol from various formats.

        Formats: markdown, json
        """
        if format == "markdown":
            protocol = Protocol(
                title=title or "Imported Protocol",
                description="",
                category=category,
                content=content,
                created_by=user_id,
                status=ProtocolStatus.DRAFT,
                **kwargs,
            )

        elif format == "json":
            import json
            try:
                data = json.loads(content)
                protocol = Protocol(
                    title=data.get("title", "Imported Protocol"),
                    description=data.get("description", ""),
                    category=ProtocolCategory(data.get("category", "general")),
                    content=data.get("content", ""),
                    tags=data.get("tags", []),
                    created_by=user_id,
                    status=ProtocolStatus.DRAFT,
                    **kwargs,
                )
            except (json.JSONDecodeError, KeyError):
                return None
        else:
            return None

        self.storage.create_protocol(protocol)
        return protocol

    # Statistics
    def get_usage_stats(
        self,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        """Get protocol usage statistics."""
        protocols = self.storage.list_protocols(
            organization_id=organization_id,
            user_id=user_id,
            limit=1000,
        )

        total_protocols = len(protocols)
        published = len([p for p in protocols if p.status == ProtocolStatus.PUBLISHED])
        drafts = len([p for p in protocols if p.status == ProtocolStatus.DRAFT])

        # Calculate total usage
        total_usage = sum(p.usage_count for p in protocols)

        # Most used protocols
        most_used = sorted(protocols, key=lambda p: p.usage_count, reverse=True)[:5]

        # Category breakdown
        category_counts = {}
        for protocol in protocols:
            cat = protocol.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_protocols": total_protocols,
            "published": published,
            "drafts": drafts,
            "total_usage": total_usage,
            "most_used": [
                {
                    "id": p.id,
                    "title": p.title,
                    "usage_count": p.usage_count,
                }
                for p in most_used
            ],
            "by_category": category_counts,
        }


# Default instance
_library: Optional[ProtocolLibrary] = None


def get_protocol_library() -> ProtocolLibrary:
    """Get default protocol library instance."""
    global _library
    if _library is None:
        _library = ProtocolLibrary()
    return _library
