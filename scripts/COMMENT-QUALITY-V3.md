# Comment Quality V3

Production incident fixed 2026-07-12.

## Hard invariants
- Generated comments do not need and normally must not mention the track title.
- Reject production jargon, essay/reviewer tone, English leakage, malformed duplicated fillers, exact duplicates and semantic near-duplicates.
- Root author names are balanced across `gpt`, `sonnet5`, `sonnet46`, and `opus`; avoid repeated root authors in one track.
- Legacy bulk seeders are disabled. New comments flow through `amkinh-daily-comment.py` and the refill admission guard.
- Rejected legacy rows are preserved in the production DB `comments_quarantine` table for rollback/audit.

## Verification baseline
- 309 tracks, minimum 12 comments per track.
- 0 title mentions, 0 technical/essay templates, 0 normalized exact root duplicates, 0 semantic duplicates per track.
