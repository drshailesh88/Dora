# Quick Start: Multi-Tenant Mode

## 1. Setup (5 minutes)

```bash
# Run the setup script
./scripts/setup_tenants.sh

# Or manually:
pip install razorpay
python migrations/001_add_tenant_support.py
```

## 2. Start Servers

```bash
# Terminal 1: Backend
uvicorn src.api.app:app --reload

# Terminal 2: Frontend
cd web && npm run dev
```

## 3. Create Your First Organization

### Via API:

```bash
curl -X POST http://localhost:8000/api/tenants \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "City General Hospital",
    "email": "admin@citygeneral.com",
    "tenant_type": "hospital",
    "plan_id": "hospital"
  }'
```

### Via Python:

```python
from src.tenants import TenantService, TenantType

service = TenantService()
success, msg, tenant = service.create_organization(
    name="City General Hospital",
    email="admin@citygeneral.com",
    owner_id="your-user-id",
    tenant_type=TenantType.HOSPITAL,
    plan_id="hospital",
)

print(f"Tenant ID: {tenant.id}")
```

## 4. Invite Team Members

```bash
curl -X POST http://localhost:8000/api/tenants/TENANT_ID/invitations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hospital.com",
    "role": "member"
  }'
```

## 5. Access Admin Dashboard

Visit: `http://localhost:3000/clinic`

## Common Operations

### Add a Member
```python
service.add_member(
    tenant_id=tenant.id,
    user_id=doctor_id,
    actor_id=owner_id,
    role=MemberRole.MEMBER,
)
```

### Check Billing
```python
from src.tenants import TenantBillingService

billing = TenantBillingService()
info = billing.get_billing_info(tenant_id)
print(f"Monthly cost: ₹{info.total_price/100}")
```

### Use Tenant Context
```python
from src.tenants.isolation import set_tenant_context

# Set context (middleware does this automatically)
set_tenant_context(tenant_id, user_id, member, tenant)

# Now all operations are scoped to this tenant
# Queries, documents, etc. are automatically isolated
```

## API Endpoints

### Organizations
- `POST /api/tenants` - Create
- `GET /api/tenants/{id}` - Get details
- `PUT /api/tenants/{id}` - Update
- `DELETE /api/tenants/{id}` - Delete

### Members
- `POST /api/tenants/{id}/members` - Add
- `GET /api/tenants/{id}/members` - List
- `PUT /api/tenants/{id}/members/{member_id}/role` - Update role
- `DELETE /api/tenants/{id}/members/{member_id}` - Remove

### Invitations
- `POST /api/tenants/{id}/invitations` - Send
- `GET /api/tenants/{id}/invitations` - List
- `POST /api/invitations/{token}/accept` - Accept
- `POST /api/invitations/{token}/decline` - Decline

### Analytics
- `GET /api/tenants/{id}/billing` - Billing info
- `GET /api/tenants/{id}/usage` - Usage stats
- `GET /api/tenants/{id}/usage/members` - Per-member usage

## Pricing

### Clinic Plan - ₹4,999/month
- Up to 5 doctors
- ₹999 per additional doctor
- Team library, analytics, EMR integration

### Hospital Plan - ₹14,999/month
- Up to 25 doctors
- ₹599 per additional doctor
- All + Custom branding, SSO, API access

### Enterprise - Custom Pricing
- Unlimited doctors
- On-premise deployment
- White-label option
- SLA guarantee

## Troubleshooting

### Error: Tenant context required
**Solution:** Ensure you're passing a valid JWT token with Authorization header

### Error: Access denied
**Solution:** User doesn't have permission. Check their role.

### Error: Member limit reached
**Solution:** Upgrade plan or remove inactive members

## Next Steps

1. **Configure Payments**: Add Razorpay credentials to `.env`
2. **Enable SSO**: Configure Google/Microsoft OAuth
3. **Custom Branding**: Upload logo and set colors (Hospital/Enterprise plans)
4. **Set Up Teams**: Create departments within your organization
5. **Bulk Import**: Upload CSV to add multiple members at once

## Resources

- Full Documentation: `TENANT_IMPLEMENTATION.md`
- API Documentation: `http://localhost:8000/docs`
- Frontend UI: `http://localhost:3000/clinic`

## Support

Questions? Issues?
- Check `TENANT_IMPLEMENTATION.md` for detailed docs
- Review audit logs for security issues
- Test with `/api/tenants/plans` to see available plans
