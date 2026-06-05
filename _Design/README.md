# Spotify CLI — Design

**Created**: 2026-06-02
**Author**: Orlando Bruno
**Scope**: Full setup (thinking + doing)

Centralized design artifacts for Spotify CLI. Research, architectural decisions, and feature specs all live here.

## Structure

```
_Design/
├── README.md          ← You are here
├── 01_PRD/            ← Product intent (run /sdd:prd to populate)
├── 02_Research/       ← Exploration and context gathering
├── 03_ADR/            ← Architecture Decision Records
└── 04_Specs/          ← Feature specifications (requirements → design → tasks)
    ├── active/        ← In-progress specs
    └── archive/       ← Completed specs
```

## Workflow

1. **Research** — Explore options, gather context (`/sdd:research`)
2. **ADR** — Record architectural decisions with rationale (`/sdd:adr`)
3. **Spec** — Define requirements → design → tasks (`/sdd:spec`)
4. **Implement** — Code from spec

## Quick Links

- [PRD](./01_PRD/prd.md) — Product Requirements Document
- [Research](./02_Research/README.md) — Exploration documents
- [ADR](./03_ADR/README.md) — Architecture Decision Records
- [Specs](./04_Specs/README.md) — Feature specifications

## Conventions

- **Diagrams**: Always use Mermaid (never ASCII art)
- **Cross-references**: Use relative paths between documents
- **Status values**: Draft | In Review | Approved | Implemented | Deprecated
- **ADR naming**: `ADR-NNN__[area]__topic.md` (see 03_ADR/README.md for area codes)

---

Last Updated: 2026-06-02
