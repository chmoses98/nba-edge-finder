"""NBA paper-trading, evaluation and weekly-report system (RESEARCH / PAPER ONLY: no orders, no staking, no account access).

Design contract: docs/research/PAPER_ENGINE_SPEC.md. Shared pieces: `schema` (constants and ids), `store` (write-once archive I/O),
`config` (the versioned, hashed protocol in paper_config.json).
"""
SPORT = "NBA"
AUTHORITY = "research_only"
