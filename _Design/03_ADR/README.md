# Architecture Decision Records

ADRs for Spotify CLI. Each record captures a significant architectural or technology decision with full rationale.

## Records

| # | Area | Title | Date | Status |
|---|------|-------|------|--------|
| 001 | sys | [Authentication Flow — OAuth 2.0 Authorization Code with PKCE](./ADR-001__sys__authentication-flow-pkce.md) | 2026-06-03 | Accepted |
| 002 | sys | [Track Resolution Strategy — Discography-First over Search-First](./ADR-002__sys__track-resolution-strategy.md) | 2026-06-03 | Accepted |
| 003 | sys | [Track List Input Contract — JSON stdin for Agent Invocation](./ADR-003__sys__track-list-input-contract.md) | 2026-06-03 | Accepted |

## When to Create an ADR

- Making an architectural or technology choice
- Choosing between approaches with trade-offs
- A decision that affects multiple components
- Something future-you will wonder "why did we do it this way?"

## Naming Convention

`ADR-NNN__[area]__slug.md` — Three-digit number, area code, kebab-case slug. Double underscores separate each segment.

### Area Codes

| Code | Area |
|------|------|
| `sys` | System / cross-cutting |
| `dp` | Data Platform |
| `wf` | Web Frontend |
| `wa` | WhatsApp API |
| `auto` | Automation |

Custom area codes are allowed (lowercase, 2-4 chars).

### Examples

- `ADR-001__wa__whatsapp-library-selection.md`
- `ADR-002__dp__database-choice.md`
- `ADR-003__sys__auth-strategy.md`

## ADR Lifecycle

```
Draft → In Review → Approved → Implemented
                              → Deprecated (if superseded)
```

---

Last Updated: 2026-06-03
