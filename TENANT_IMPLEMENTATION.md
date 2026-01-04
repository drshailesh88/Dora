# Multi-Tenant / Clinic Mode Implementation

## Overview

This implementation adds comprehensive multi-tenant support to Dora, enabling clinics, hospitals, and healthcare organizations to manage teams, billing, and data isolation.

## Features Implemented

### 1. Tenant Data Models (`src/tenants/models.py`)
- **Tenant**: Organization/clinic entity with plan, branding, and settings
- **TenantMember**: User membership with role-based access control
- **Team**: Departments within organizations
- **TenantInvitation**: Invitation system with expiration
- **TenantAuditLog**: Complete audit trail for compliance
- **TenantPlan**: Subscription plans (Clinic, Hospital, Enterprise)

### 2. Roles and Permissions
- **Owner**: Full control, billing management
- **Admin**: Member management, settings
- **Member**: Regular access to features
- **Viewer**: Read-only access

### 3. Subscription Plans

| Plan | Members | Price/Month | Features |
|------|---------|-------------|----------|
| **Clinic** | 5 | ₹4,999 | Team library, analytics, EMR integration |
| **Hospital** | 25 | ₹14,999 | All + Custom branding, SSO, API access |
| **Enterprise** | Unlimited | Custom | All + On-premise, white-label, SLA |

**Overage Billing:**
- Clinic: ₹999/additional member
- Hospital: ₹599/additional member

### 4. Data Isolation (`src/tenants/isolation.py`)

**HIPAA-Compliant Features:**
- Thread-local tenant context per request
- Automatic tenant_id scoping on all queries
- Cross-tenant access prevention
- Audit logging for all operations
- Row-level security through application logic

**Usage:**
```python
from src.tenants.isolation import set_tenant_context, require_tenant_context

# Set context
set_tenant_context(tenant_id, user_id, member, tenant)

# Require context for operations
@require_tenant_context
def save_query(question, answer):
    # Automatically scoped to tenant
    pass
```

### 5. Storage Layer (`src/tenants/storage.py`)
- SQLite backend with optimized indexes
- Cascade deletes for data integrity
- Efficient queries with tenant_id filtering
- Support for bulk operations

**Database Schema:**
- `tenants` - Organization data
- `tenant_members` - User memberships
- `teams` - Departments
- `tenant_invitations` - Pending invitations
- `tenant_audit_logs` - Complete audit trail

### 6. Billing Service (`src/tenants/billing.py`)
- Razorpay integration for payments
- Per-seat billing with overage
- Invoice generation with GST (18%)
- Usage tracking and analytics
- Plan upgrades/downgrades

### 7. Admin Service (`src/tenants/admin.py`)
- Usage analytics dashboard
- Per-member usage tracking
- Bulk member import (CSV)
- Data export for compliance
- Custom branding management
- Team announcements

### 8. API Endpoints (`src/api/tenants.py`)

**Organization Management:**
- `POST /api/tenants` - Create organization
- `GET /api/tenants/{id}` - Get details
- `PUT /api/tenants/{id}` - Update
- `DELETE /api/tenants/{id}` - Delete

**Member Management:**
- `POST /api/tenants/{id}/members` - Add member
- `GET /api/tenants/{id}/members` - List members
- `DELETE /api/tenants/{id}/members/{member_id}` - Remove
- `PUT /api/tenants/{id}/members/{member_id}/role` - Change role

**Invitations:**
- `POST /api/tenants/{id}/invitations` - Send invitation
- `GET /api/tenants/{id}/invitations` - List invitations
- `POST /api/invitations/{token}/accept` - Accept
- `POST /api/invitations/{token}/decline` - Decline

**Teams:**
- `POST /api/tenants/{id}/teams` - Create team
- `GET /api/tenants/{id}/teams` - List teams
- `DELETE /api/tenants/{id}/teams/{team_id}` - Delete

**Billing & Analytics:**
- `GET /api/tenants/{id}/billing` - Billing info
- `GET /api/tenants/{id}/usage` - Usage analytics
- `GET /api/tenants/{id}/usage/members` - Per-member usage

**Admin Operations:**
- `POST /api/tenants/{id}/members/bulk-invite` - Bulk invite
- `GET /api/tenants/{id}/members/export` - Export CSV
- `PUT /api/tenants/{id}/branding` - Update branding
- `GET /api/tenants/{id}/audit-logs` - View audit logs
- `GET /api/tenants/{id}/export` - Export all data

### 9. Middleware (`src/tenants/middleware.py`)
Automatically extracts tenant context from:
1. JWT token claims (`tenant_id`)
2. `X-Tenant-ID` request header
3. User's default tenant (single membership)

Sets context for entire request lifecycle.

### 10. Web UI (`web/app/clinic/`)

**Pages:**
- `/clinic` - Dashboard with team overview
- `/clinic/members` - Member management
- `/clinic/billing` - Billing and usage
- `/clinic/invite` - Invite members
- `/clinic/settings` - Organization settings
- `/clinic/teams` - Team management

**Components:**
- Real-time usage charts
- Member role management
- Billing alerts for overage
- Invitation tracking

## Setup & Migration

### 1. Install Dependencies

```bash
# Backend
pip install razorpay

# Frontend
cd web
npm install
```

### 2. Environment Variables

```bash
# Razorpay (for payments)
export RAZORPAY_KEY_ID="your_key_id"
export RAZORPAY_KEY_SECRET="your_key_secret"

# JWT (if not already set)
export DORA_JWT_SECRET="your_jwt_secret"
```

### 3. Run Migration

For existing databases:

```bash
python migrations/001_add_tenant_support.py
```

This will:
- Add `tenant_id` columns to existing tables
- Create tenant tables
- Create individual tenants for existing users
- Set up proper indexes

### 4. Start Application

```bash
# Backend
uvicorn src.api.app:app --reload

# Frontend
cd web
npm run dev
```

## Usage Examples

### Creating an Organization

```python
from src.tenants import TenantService, TenantType

service = TenantService()
success, msg, tenant = service.create_organization(
    name="City General Hospital",
    email="admin@citygeneral.com",
    owner_id=user.id,
    tenant_type=TenantType.HOSPITAL,
    plan_id="hospital",
    trial_days=14,
)
```

### Adding Members

```python
# Invite via email
success, msg, invitation = service.create_invitation(
    tenant_id=tenant.id,
    email="doctor@example.com",
    role=MemberRole.MEMBER,
    actor_id=owner_id,
)

# Or add existing user directly
success, msg, member = service.add_member(
    tenant_id=tenant.id,
    user_id=doctor_id,
    actor_id=owner_id,
    role=MemberRole.MEMBER,
)
```

### Using Tenant Context

```python
from src.tenants.isolation import set_tenant_context, QueryHistory

# Set context (usually done by middleware)
set_tenant_context(tenant_id, user_id, member, tenant)

# All operations are now scoped to tenant
history = QueryHistory()
query_id = history.save_query(
    question="What is the treatment for diabetes?",
    answer="..."
)

# Only returns queries from current tenant
recent = history.get_user_history(limit=10)
```

### Billing Management

```python
from src.tenants import TenantBillingService

billing = TenantBillingService()

# Get billing info
info = billing.get_billing_info(tenant_id)
print(f"Members: {info.current_members}/{info.max_members}")
print(f"Monthly cost: ₹{info.total_price/100}")

# Upgrade plan
success, msg = billing.upgrade_plan(tenant_id, "enterprise")
```

## Security & Compliance

### HIPAA Compliance
✅ Data isolation per tenant
✅ Audit logging for all operations
✅ Secure data deletion
✅ Access control with RBAC
✅ Encryption at rest (database level)
✅ No cross-tenant data leakage

### Data Isolation
- All queries automatically scoped to `tenant_id`
- Middleware validates tenant access on every request
- Cross-tenant queries blocked at application layer
- Audit trail for compliance review

### Access Control
- Owner: Full control, billing access
- Admin: Member management, settings
- Member: Feature access only
- Viewer: Read-only access

### Audit Logging
Every action logged with:
- Actor (who performed)
- Action (what was done)
- Target (what was affected)
- Timestamp
- IP address & user agent
- Details (metadata)

## API Integration

### Adding Tenant Context to JWT

Already supported! The JWT handler includes `org_id` in token payload:

```python
# Token automatically includes tenant_id
access_token = jwt_handler.create_access_token(
    user_id=user.id,
    email=user.email,
    role=user.role,
    name=user.name,
    org_id=user.organization_id,  # Tenant ID
)
```

### Making Tenant-Scoped API Calls

```javascript
// Frontend example
const response = await fetch(`/api/tenants/${tenantId}/members`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Tenant-ID': tenantId,  // Optional: for multi-tenant users
  },
});
```

## Testing

### Unit Tests

```bash
pytest tests/tenants/
```

### Integration Tests

```bash
# Test tenant creation
pytest tests/tenants/test_service.py::test_create_organization

# Test data isolation
pytest tests/tenants/test_isolation.py::test_cross_tenant_access_denied

# Test billing
pytest tests/tenants/test_billing.py::test_overage_calculation
```

## Monitoring & Analytics

### Usage Dashboard
- Total members
- Queries per period
- Storage usage
- Cost breakdown
- Per-member analytics

### Alerts
- Overage warnings
- Trial expiration
- Payment failures
- Security events

## Future Enhancements

### Planned Features
- [ ] SSO configuration UI
- [ ] Advanced usage quotas
- [ ] Custom roles & permissions
- [ ] Multi-region support
- [ ] Advanced analytics & reporting
- [ ] API rate limiting per tenant
- [ ] Webhook integrations
- [ ] Custom email domains
- [ ] Data retention policies
- [ ] GDPR compliance tools

### Integrations
- [ ] Slack notifications
- [ ] Microsoft Teams integration
- [ ] Calendar integration
- [ ] LDAP/Active Directory sync

## Troubleshooting

### Common Issues

**1. Tenant context not set**
```
Error: TenantIsolationError: Tenant context required
```
Solution: Ensure middleware is properly configured in app.py

**2. Cross-tenant access denied**
```
Error: Access denied: Cannot access tenant X from context Y
```
Solution: User doesn't have permission to access that tenant

**3. Member limit exceeded**
```
Error: Member limit reached. Please upgrade your plan.
```
Solution: Upgrade plan or remove inactive members

### Debug Mode

Enable tenant context logging:

```python
import logging
logging.getLogger('src.tenants').setLevel(logging.DEBUG)
```

## Support

For issues or questions:
1. Check this documentation
2. Review audit logs for security issues
3. Contact: support@docassist.com

---

**Implementation Date:** January 2026
**Version:** 1.0.0
**Status:** Production Ready ✅
