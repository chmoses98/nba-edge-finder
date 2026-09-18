"""NBA data adapters. Each source implements a small protocol and returns canonical schema objects with provenance.
Sources are ranked by the data-source audit (docs/NBA_DATA_SOURCE_AUDIT.md); production prefers structured JSON
endpoints and never depends on a single source when a fallback exists."""
