# Dora Beta Launch Checklist

## Pre-Launch Requirements

### Infrastructure
- [ ] Production Docker Compose tested
- [ ] SSL certificates configured
- [ ] DNS records set up
- [ ] Backup procedures verified
- [ ] Disaster recovery plan documented

### Security (HIPAA Compliance)
- [ ] Audit logging enabled and tested
- [ ] PHI encryption at rest verified
- [ ] TLS 1.2+ enforced
- [ ] Access controls configured
- [ ] BAA (Business Associate Agreement) template ready
- [ ] Security incident response plan documented

### Database
- [ ] PostgreSQL optimized for production
- [ ] Qdrant collections created
- [ ] Neo4j UMLS data loaded
- [ ] Backup automation configured
- [ ] Connection pooling tuned

### Monitoring
- [ ] Prometheus metrics flowing
- [ ] Grafana dashboards created
- [ ] Alert rules configured
- [ ] On-call rotation established
- [ ] Incident response procedures documented

### Performance
- [ ] Load testing completed (target: 100 concurrent users)
- [ ] Query latency < 3s at p95
- [ ] LLM fallback to Ollama tested
- [ ] Cache warming strategy implemented
- [ ] CDN configured (if applicable)

### Features
- [ ] Core RAG pipeline tested
- [ ] Voice features tested
- [ ] Offline mode tested
- [ ] EMR integration tested
- [ ] Calculators and protocols verified

### Documentation
- [ ] User guide complete
- [ ] API documentation published
- [ ] Deployment guide reviewed
- [ ] Support runbook finalized

### Legal & Compliance
- [ ] Terms of Service finalized
- [ ] Privacy Policy finalized
- [ ] Data Processing Agreement ready
- [ ] Medical disclaimer displayed
- [ ] Cookie consent (if applicable)

## Launch Day Checklist

### T-24 Hours
- [ ] Final backup of all data
- [ ] Notify on-call team
- [ ] Prepare rollback procedure
- [ ] Test monitoring alerts

### T-4 Hours
- [ ] Deploy production build
- [ ] Smoke test all features
- [ ] Verify SSL and security headers
- [ ] Check logging pipeline

### T-0 (Launch)
- [ ] Enable beta user access
- [ ] Monitor error rates
- [ ] Watch performance metrics
- [ ] Staff support channels

### T+1 Hour
- [ ] Review initial metrics
- [ ] Check for any errors
- [ ] Verify backup ran successfully
- [ ] Send launch confirmation

## Post-Launch

### Day 1
- [ ] Review all error logs
- [ ] Collect initial user feedback
- [ ] Document any issues
- [ ] Plan hotfixes if needed

### Week 1
- [ ] Analyze usage patterns
- [ ] Review performance metrics
- [ ] Gather detailed user feedback
- [ ] Prioritize improvements

### Month 1
- [ ] Monthly metrics report
- [ ] User satisfaction survey
- [ ] Plan next feature release
- [ ] Security audit review

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Technical Lead | TBD | TBD |
| On-Call Engineer | TBD | TBD |
| Product Owner | TBD | TBD |
| Compliance Officer | TBD | TBD |

## Rollback Procedure

1. Stop API containers: `docker-compose stop api`
2. Restore previous image: `docker-compose pull api:previous`
3. Start previous version: `docker-compose up -d api`
4. Verify health: `curl https://api.dora.health/health`
5. Notify stakeholders
6. Document incident

---

*Last Updated: January 2026*
*Version: 1.0*
