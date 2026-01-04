"""
Protocol API Endpoints

REST API for protocol management, collaboration, and compliance tracking.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..auth import User, get_current_user_required
from ..protocols import (
    ProtocolService,
    get_protocol_service,
    ProtocolCategory,
    ProtocolStatus,
    AccessLevel,
    ChecklistStatus,
)


router = APIRouter(prefix="/api/v1/protocols", tags=["Protocols"])


# Request/Response Models
class ProtocolCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = ""
    category: str
    content: str = ""
    tags: List[str] = []
    is_clinic_wide: bool = False


class ProtocolUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    evidence_grade: Optional[str] = None


class ProtocolFromTemplateRequest(BaseModel):
    template_id: str
    title: Optional[str] = None


class QuickReferenceRequest(BaseModel):
    title: str
    content: str
    card_type: str
    protocol_id: Optional[str] = None
    layout: str = "card"
    is_printable: bool = True


class ChecklistItemRequest(BaseModel):
    text: str
    required: bool = True
    order: int
    section: Optional[str] = None
    notes: Optional[str] = None


class ChecklistCreateRequest(BaseModel):
    title: str
    description: str
    items: List[ChecklistItemRequest]
    protocol_id: Optional[str] = None


class ChecklistItemStatusUpdate(BaseModel):
    item_id: str
    status: str
    notes: Optional[str] = None


class VersionCreateRequest(BaseModel):
    change_summary: str
    changed_sections: Optional[List[str]] = None


class ShareRequest(BaseModel):
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    organization_id: Optional[str] = None
    access_level: str = "view"
    expires_days: Optional[int] = None


class AnnotationRequest(BaseModel):
    content: str
    section: Optional[str] = None
    line_number: Optional[int] = None
    parent_id: Optional[str] = None


class ComplianceRecordRequest(BaseModel):
    followed: bool = True
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None
    deviation_reason: Optional[str] = None
    deviation_sections: Optional[List[str]] = None
    outcome_notes: Optional[str] = None


# Protocol CRUD Endpoints
@router.post("/")
async def create_protocol(
    request: ProtocolCreateRequest,
    user: User = Depends(get_current_user_required),
):
    """Create a new protocol."""
    service = get_protocol_service()

    try:
        category = ProtocolCategory(request.category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {request.category}")

    protocol = service.create_protocol(
        title=request.title,
        description=request.description,
        category=category,
        user_id=user.id,
        content=request.content,
        tags=request.tags,
        organization_id=user.organization_id,
        is_clinic_wide=request.is_clinic_wide,
    )

    return protocol.to_dict()


@router.get("/{protocol_id}")
async def get_protocol(
    protocol_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get a protocol by ID."""
    service = get_protocol_service()

    protocol = service.get_protocol(protocol_id, user_id=user.id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or access denied")

    return protocol.to_dict()


@router.put("/{protocol_id}")
async def update_protocol(
    protocol_id: str,
    request: ProtocolUpdateRequest,
    user: User = Depends(get_current_user_required),
):
    """Update a protocol."""
    service = get_protocol_service()

    # Check access
    protocol = service.get_protocol(protocol_id, user_id=user.id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or access denied")

    if protocol.created_by != user.id:
        raise HTTPException(status_code=403, detail="Only the creator can update this protocol")

    category = None
    if request.category:
        try:
            category = ProtocolCategory(request.category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {request.category}")

    updated = service.update_protocol(
        protocol_id=protocol_id,
        title=request.title,
        description=request.description,
        content=request.content,
        tags=request.tags,
        category=category,
        evidence_grade=request.evidence_grade,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Protocol not found")

    return updated.to_dict()


@router.delete("/{protocol_id}")
async def delete_protocol(
    protocol_id: str,
    user: User = Depends(get_current_user_required),
):
    """Delete a protocol."""
    service = get_protocol_service()

    protocol = service.get_protocol(protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    if protocol.created_by != user.id:
        raise HTTPException(status_code=403, detail="Only the creator can delete this protocol")

    success = service.delete_protocol(protocol_id)
    return {"success": success}


@router.get("/")
async def list_protocols(
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated
    is_template: Optional[bool] = None,
    offset: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user_required),
):
    """List protocols with filters."""
    service = get_protocol_service()

    cat = None
    if category:
        try:
            cat = ProtocolCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    stat = None
    if status:
        try:
            stat = ProtocolStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(',')]

    protocols = service.search_protocols(
        user_id=user.id,
        organization_id=user.organization_id,
        category=cat,
        status=stat,
        search_term=search,
        tags=tag_list,
        is_template=is_template,
        offset=offset,
        limit=limit,
    )

    return {
        "protocols": [p.to_dict() for p in protocols],
        "offset": offset,
        "limit": limit,
        "total": len(protocols),
    }


# Template Endpoints
@router.get("/templates/")
async def list_templates(
    category: Optional[str] = None,
    user: User = Depends(get_current_user_required),
):
    """List available protocol templates."""
    service = get_protocol_service()

    cat = None
    if category:
        try:
            cat = ProtocolCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    templates = service.get_templates(cat)
    return {"templates": [t.to_dict() for t in templates]}


@router.post("/templates/{template_id}/create")
async def create_from_template(
    template_id: str,
    request: ProtocolFromTemplateRequest,
    user: User = Depends(get_current_user_required),
):
    """Create a protocol from a template."""
    service = get_protocol_service()

    protocol = service.create_from_template(
        template_id=template_id,
        user_id=user.id,
        title=request.title,
        organization_id=user.organization_id,
    )

    if not protocol:
        raise HTTPException(status_code=404, detail="Template not found")

    return protocol.to_dict()


# Versioning Endpoints
@router.post("/{protocol_id}/versions")
async def create_version(
    protocol_id: str,
    request: VersionCreateRequest,
    user: User = Depends(get_current_user_required),
):
    """Create a new version of a protocol."""
    service = get_protocol_service()

    version = service.create_version(
        protocol_id=protocol_id,
        user_id=user.id,
        change_summary=request.change_summary,
        changed_sections=request.changed_sections,
    )

    if not version:
        raise HTTPException(status_code=404, detail="Protocol not found")

    return version.to_dict()


@router.get("/{protocol_id}/versions")
async def get_version_history(
    protocol_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get version history for a protocol."""
    service = get_protocol_service()

    # Check access
    protocol = service.get_protocol(protocol_id, user_id=user.id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or access denied")

    versions = service.get_version_history(protocol_id)
    return {"versions": [v.to_dict() for v in versions]}


@router.post("/{protocol_id}/publish")
async def publish_protocol(
    protocol_id: str,
    user: User = Depends(get_current_user_required),
):
    """Publish a protocol."""
    service = get_protocol_service()

    protocol = service.publish_protocol(protocol_id, user.id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    return protocol.to_dict()


# Sharing Endpoints
@router.post("/{protocol_id}/share")
async def share_protocol(
    protocol_id: str,
    request: ShareRequest,
    user: User = Depends(get_current_user_required),
):
    """Share a protocol with a user or team."""
    service = get_protocol_service()

    # Check ownership
    protocol = service.get_protocol(protocol_id)
    if not protocol or protocol.created_by != user.id:
        raise HTTPException(status_code=403, detail="Only the creator can share this protocol")

    try:
        access_level = AccessLevel(request.access_level)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid access level: {request.access_level}")

    share = service.share_protocol(
        protocol_id=protocol_id,
        shared_by=user.id,
        access_level=access_level,
        user_id=request.user_id,
        team_id=request.team_id,
        organization_id=request.organization_id,
        expires_days=request.expires_days,
    )

    return share.to_dict()


@router.get("/{protocol_id}/shares")
async def get_protocol_shares(
    protocol_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get all shares for a protocol."""
    service = get_protocol_service()

    # Check ownership
    protocol = service.get_protocol(protocol_id)
    if not protocol or protocol.created_by != user.id:
        raise HTTPException(status_code=403, detail="Only the creator can view shares")

    shares = service.get_protocol_shares(protocol_id)
    return {"shares": [s.to_dict() for s in shares]}


@router.post("/{protocol_id}/annotations")
async def add_annotation(
    protocol_id: str,
    request: AnnotationRequest,
    user: User = Depends(get_current_user_required),
):
    """Add a comment/annotation to a protocol."""
    service = get_protocol_service()

    # Check access
    protocol = service.get_protocol(protocol_id, user_id=user.id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or access denied")

    annotation = service.add_annotation(
        protocol_id=protocol_id,
        user_id=user.id,
        user_name=user.name,
        content=request.content,
        section=request.section,
        line_number=request.line_number,
        parent_id=request.parent_id,
    )

    return annotation.to_dict()


@router.get("/{protocol_id}/annotations")
async def get_annotations(
    protocol_id: str,
    include_resolved: bool = False,
    user: User = Depends(get_current_user_required),
):
    """Get annotations for a protocol."""
    service = get_protocol_service()

    # Check access
    protocol = service.get_protocol(protocol_id, user_id=user.id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or access denied")

    annotations = service.get_annotations(protocol_id, include_resolved=include_resolved)
    return {"annotations": [a.to_dict() for a in annotations]}


# Quick References
@router.get("/references/")
async def list_quick_references(
    protocol_id: Optional[str] = None,
    user: User = Depends(get_current_user_required),
):
    """List quick references."""
    service = get_protocol_service()

    refs = service.get_quick_references(
        protocol_id=protocol_id,
        organization_id=user.organization_id,
    )

    # Include default references
    default_refs = service.get_default_references()

    return {
        "references": [r.to_dict() for r in refs],
        "default_references": default_refs,
    }


@router.post("/references/")
async def create_quick_reference(
    request: QuickReferenceRequest,
    user: User = Depends(get_current_user_required),
):
    """Create a quick reference card."""
    service = get_protocol_service()

    ref = service.create_quick_reference(
        title=request.title,
        content=request.content,
        card_type=request.card_type,
        user_id=user.id,
        protocol_id=request.protocol_id,
        organization_id=user.organization_id,
        layout=request.layout,
        is_printable=request.is_printable,
    )

    return ref.to_dict()


# Checklists
@router.get("/checklists/")
async def list_checklists(
    protocol_id: Optional[str] = None,
    user: User = Depends(get_current_user_required),
):
    """List checklists."""
    service = get_protocol_service()

    checklists = service.list_checklists(
        protocol_id=protocol_id,
        organization_id=user.organization_id,
    )

    # Include default checklists
    default_checklists = service.get_default_checklists()

    return {
        "checklists": [c.to_dict() for c in checklists],
        "default_checklists": [c.to_dict() for c in default_checklists],
    }


@router.post("/checklists/")
async def create_checklist(
    request: ChecklistCreateRequest,
    user: User = Depends(get_current_user_required),
):
    """Create a checklist."""
    service = get_protocol_service()

    from ..protocols.models import ChecklistItem

    items = [
        ChecklistItem(
            text=item.text,
            required=item.required,
            order=item.order,
            section=item.section,
            notes=item.notes,
        )
        for item in request.items
    ]

    checklist = service.create_checklist(
        title=request.title,
        description=request.description,
        items=items,
        user_id=user.id,
        protocol_id=request.protocol_id,
        organization_id=user.organization_id,
    )

    return checklist.to_dict()


@router.post("/checklists/{checklist_id}/start")
async def start_checklist(
    checklist_id: str,
    patient_id: Optional[str] = None,
    encounter_id: Optional[str] = None,
    user: User = Depends(get_current_user_required),
):
    """Start a checklist execution."""
    service = get_protocol_service()

    execution = service.start_checklist_execution(
        checklist_id=checklist_id,
        user_id=user.id,
        patient_id=patient_id,
        encounter_id=encounter_id,
    )

    return execution.to_dict()


@router.put("/checklists/executions/{execution_id}/items")
async def update_checklist_item(
    execution_id: str,
    request: ChecklistItemStatusUpdate,
    user: User = Depends(get_current_user_required),
):
    """Update checklist item status."""
    service = get_protocol_service()

    try:
        status = ChecklistStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")

    execution = service.update_checklist_item(
        execution_id=execution_id,
        item_id=request.item_id,
        status=status,
        notes=request.notes,
    )

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution.to_dict()


# Flowcharts
@router.get("/flowcharts/")
async def list_flowcharts(
    user: User = Depends(get_current_user_required),
):
    """List flowcharts."""
    service = get_protocol_service()

    flowcharts = service.get_default_flowcharts()
    return {"flowcharts": flowcharts}


# Compliance & Tracking
@router.post("/{protocol_id}/use")
async def record_usage(
    protocol_id: str,
    request: ComplianceRecordRequest,
    user: User = Depends(get_current_user_required),
):
    """Record protocol usage for compliance tracking."""
    service = get_protocol_service()

    record = service.record_usage(
        protocol_id=protocol_id,
        user_id=user.id,
        followed=request.followed,
        patient_id=request.patient_id,
        encounter_id=request.encounter_id,
        deviation_reason=request.deviation_reason,
        deviation_sections=request.deviation_sections,
        outcome_notes=request.outcome_notes,
    )

    return record.to_dict()


@router.get("/{protocol_id}/compliance")
async def get_protocol_compliance(
    protocol_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: User = Depends(get_current_user_required),
):
    """Get compliance report for a protocol."""
    service = get_protocol_service()

    # Check access
    protocol = service.get_protocol(protocol_id, user_id=user.id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or access denied")

    kwargs = {}
    if start_date:
        kwargs["start_date"] = datetime.fromisoformat(start_date)
    if end_date:
        kwargs["end_date"] = datetime.fromisoformat(end_date)

    report = service.generate_compliance_report(protocol_id, **kwargs)
    if not report:
        raise HTTPException(status_code=404, detail="Protocol not found")

    return report.to_dict()


@router.get("/compliance/organization")
async def get_organization_compliance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: User = Depends(get_current_user_required),
):
    """Get organization-wide compliance report."""
    service = get_protocol_service()

    if not user.organization_id:
        raise HTTPException(status_code=400, detail="User not part of an organization")

    kwargs = {}
    if start_date:
        kwargs["start_date"] = datetime.fromisoformat(start_date)
    if end_date:
        kwargs["end_date"] = datetime.fromisoformat(end_date)

    report = service.generate_organization_report(user.organization_id, **kwargs)
    return report


@router.get("/compliance/user")
async def get_user_compliance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: User = Depends(get_current_user_required),
):
    """Get user's compliance report."""
    service = get_protocol_service()

    kwargs = {}
    if start_date:
        kwargs["start_date"] = datetime.fromisoformat(start_date)
    if end_date:
        kwargs["end_date"] = datetime.fromisoformat(end_date)

    report = service.generate_user_report(user.id, **kwargs)
    return report


@router.get("/dashboard")
async def get_dashboard(
    user: User = Depends(get_current_user_required),
):
    """Get protocol dashboard statistics."""
    service = get_protocol_service()

    stats = service.get_dashboard_stats(
        organization_id=user.organization_id,
        user_id=user.id,
    )

    return stats
