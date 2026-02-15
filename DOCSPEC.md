# pepalyzer — Documentation and Specification

## Overview

**pepalyzer** is a Python CLI tool that assists technical stewardship and editorial practice by surfacing recently changed PEPs as editorial artifacts, using Git history as a change detection and provenance mechanism.

pepalyzer treats Git commits as an implementation detail used to identify and de-duplicate recently modified PEP documents, not as a proxy for importance or activity.

The tool does not attempt to evaluate importance, predict language direction, or automate editorial judgment. Its purpose is to present PEPs that changed within a time window, enriched with metadata and lightweight signals, to support calm, human-led analysis.

**Core insight**: PEPs are decisions, not code—and decisions don't need to be frequent to be important.

## Meta DOCSPEC

DOCSPEC is a documentation-first programming style inspired by Literate Programming.

This file serves as the master specification and source of truth for pepalyzer's behavior and architecture.

All requirements defined here are intended to be translated into:

- Unit tests (pure logic, no Git required)
- Integration tests (Git + filesystem + CLI)
- Python implementation code that passes those tests
- User-facing documentation and CLI help text

This document will evolve alongside the codebase and may include explicit references to test files and source modules as they are implemented.

## Design Principles

pepalyzer is guided by the following principles:

- **PEP-centric, not commit-centric** — PEPs are the unit of meaning; commits are implementation details
- **Explicit state over implicit convenience** — Show current state clearly, don't hide behind aggregations
- **Human judgment over automated interpretation** — Surface signals, don't rank importance
- **Local Git history over remote APIs** — Use Git only for change detection and provenance
- **Minimal automation, maximal clarity** — Simple heuristics, inspectable outputs
- **Loose coupling between tool and data** — No opinions about what makes a PEP "important"

## Usage Model

pepalyzer operates on an existing local clone of the Python PEPs repository.

### The user is responsible for:

- Cloning the PEPs repo
- Updating it via `git pull`
- Choosing when to analyze changes

### pepalyzer is responsible for:

- Identifying which PEPs changed (using Git as change detection)
- Reading current PEP metadata (title, status, abstract)
- Detecting what changed (especially status transitions)
- Presenting one entry per PEP with full context
- Surfacing editorial signals to guide human attention
- Emitting useful summaries for review and decision-making

### Example usage

Run the CLI with a path to the local PEPs repository and a time window. For example, scan commits from the last 30 days:

```bash
pepalyzer scan ~/src/peps --since 30d
```

**What gets analyzed:**
- Only commits that touch PEP files (pep-NNNN.rst, pep-NNNN.md)
- Commits modifying only infrastructure files (README, CI configs) are silently filtered
- Each PEP appears once in output, even if touched by multiple commits
- Commit count shown is per-PEP, so totals may exceed the number of commits in the window

## Core Workflow

At a high level, pepalyzer implements the following pipeline:

1. **Local Git repo** - User maintains local clone (input plumbing)
2. **Identify changed PEP documents** - Use Git history to detect which PEPs changed in time window
3. **De-duplicate by PEP number** - Collapse multiple commits into one entry per PEP
4. **Extract current PEP metadata** - Read each PEP file to get title, status, abstract, authors (required)
5. **Analyze what changed** - Parse Git diffs to detect status transitions and content modifications
6. **Synthesize PEP change summary** - Combine current state + detected changes into unified PepActivity
7. **Classify editorial signals** - Apply lightweight heuristics to identify notable patterns
8. **Structured output** - Format for human review (text or JSON)

**Key insight**: Steps 1-3 are implementation details. The meaningful work begins at step 4, where PEPs become the primary unit of analysis.

### Edge Cases in Change Detection

**Commits with no PEP files:**
- Some commits may modify only repository infrastructure (README, CI configs, build scripts)
- These commits are **silently filtered out** during de-duplication (step 3)
- They don't appear in output and don't generate warnings
- The tool only surfaces commits that touch at least one PEP file

**Commits touching multiple PEPs:**
- A single commit may modify multiple PEP files (e.g., cross-references, bulk formatting)
- Each affected PEP gets its own `PepActivity` entry
- Each PEP's `commit_count` increments independently
- Example: Commit ABC touches pep-0001.rst, pep-0002.rst, pep-0003.rst
  - Output: Three separate entries (PEP 1, PEP 2, PEP 3)
  - Each shows `commit_count: 1` (or more, if other commits also touched them)
  - **Expected behavior**: Sum of all `commit_count` values may exceed total commits
  - This is correct: commit_count is per-PEP provenance, not a global metric

Each stage is intentionally simple and testable in isolation.

## Architecture Overview

### Module Responsibilities (Conceptual)

- **CLI** – Argument parsing, orchestration, output selection
- **Git Adapter** – Change detection plumbing (which PEPs changed, what diffs show)
- **PEP Metadata Extractor** – Read and parse current PEP files (RFC 822 headers + abstract)
- **PEP Change Synthesizer** – Combine current state + diff analysis into unified PEP summaries
- **Signal Detection** – Identify editorial signals (status transitions primary, content patterns secondary)
- **Reporting** – Human-readable and machine-readable PEP summaries (title/abstract/status required)

## Data Model (Intermediate Structures)

pepalyzer centers around explicit intermediate data structures that reflect progressively higher-level understanding.

### CommitRecord

Represents a single Git commit relevant to analysis. Contains the commit hash, timestamp, and a list of files changed.

### ChangedFile

Represents a file touched by a commit. Includes the file path and type of change (added, modified, deleted).

### PepActivity

Represents a single PEP that changed within the analysis window, enriched with current metadata and a summary of detected changes.

**This is a one-row-per-PEP structure.** Multiple commits to the same PEP are de-duplicated into a single entry.

**Identity**:
- **pep_number**: PEP number (e.g., 815) — primary key

**Required metadata** (extracted from current PEP file):
- **title**: Human-readable PEP title (from `Title:` field) — required for useful output
- **status**: Current status (Draft, Accepted, Final, Withdrawn, etc.) — required
- **abstract**: First 1-3 sentences from the `Abstract:` section — required for context

**Optional metadata**:
- **authors**: List of author names/emails (from `Author:` field)
- **pep_type**: Type of PEP (Standards Track, Informational, Process)
- **created**: PEP creation date (from `Created:` field)

**Auxiliary provenance** (always shown, informational only, not a measure of importance):
- **commit_count**: Number of commits touching this PEP in the analysis window
  - Note: If a single commit touches multiple PEPs, each PEP's count increments
  - Total commit_count across all PEPs may exceed total commits analyzed
  - This is correct behavior: commit_count is per-PEP, not global
- **files**: List of unique file paths associated with this PEP

**Error handling**: If a PEP file cannot be read or parsed, title/status/abstract should be set to sensible defaults (e.g., "Unknown", "Unable to read"), not hidden from output. A PEP that changed is still editorially relevant even if metadata extraction fails.

### PepSignal

Represents detected editorially-interesting signals for a PEP. Signals are descriptive flags, not judgments.

## Three-Layer Analysis Model

pepalyzer operates in three conceptual layers, moving from raw Git data to editorial understanding:

### Layer 1: Git Change Detection (Input Plumbing)

**Purpose**: Identify which PEPs changed and when.

Analyzes commit diffs to detect:
- Which files were added, modified, or deleted
- What specific lines changed (additions, deletions)
- Status transitions by parsing diff output (e.g., `-Status: Draft` → `+Status: Accepted`)
- Content changes that indicate normative language additions or deprecations

**Data source**: Git commit history (`git log`, `git diff`)

**Output**: List of changed files + diff content, grouped by PEP number

### Layer 2: Current State Extraction (What Is)

**Purpose**: Understand what each PEP currently is.

Reads the **current version** of PEP files from the filesystem to extract structured metadata:

**Header format**: PEPs use RFC 822-style headers at the top of `.rst` or `.md` files:
```
PEP: 815
Title: Disallow reference cycles in tp_traverse
Author: Sam Gross <colesbury@gmail.com>
Status: Draft
Type: Standards Track
Created: 11-Jan-2024
```

**Extraction rules**:
- Parse headers as key-value pairs (format: `Key: Value`)
- Stop at first blank line (end of header section)
- Handle multi-line values (continuation lines start with whitespace)
- Support both `.rst` and `.md` file formats
- Extract abstract from first paragraph after headers (reStructuredText convention)

**Required fields**: title, status, abstract — without these, output is not useful

**Error handling**:
- If file is deleted/missing: use fallback values ("Unknown", "Deleted", "File not available")
- If headers are malformed: extract what's parseable, use fallbacks for rest
- If file is binary or non-text: use fallbacks
- **Never hide a changed PEP due to parsing failure** — it's still editorially relevant

**Data source**: Current files on filesystem (repo working directory)

**Output**: PepMetadata for each changed PEP

### Layer 3: PEP Change Synthesis (What Changed About What)

**Purpose**: Combine current state + detected changes into editorial understanding.

This is where editorial significance emerges:
- A status transition to "Final" matters regardless of commit count
- A single commit adding normative language may be more significant than ten typo fixes
- Knowing what a PEP *is* (title, abstract) is required to understand why changes matter

**Synthesis logic**:
1. Take PEP identity (number)
2. Add current state (title, status, abstract) — required for context
3. Add detected changes (status transitions, content signals) — from diffs
4. Add provenance metadata (commit count, files) — auxiliary information only

**Output**: PepActivity objects ready for human review

**Key insight**: This layer is where "one commit to PEP 815 finalizing the design" becomes obviously more important than "ten commits fixing typos in PEP 8". The tool doesn't rank importance, but it provides the metadata and signals needed for humans to make that judgment instantly.

## Signal Detection (Lightweight, Rule-Based)

pepalyzer uses simple heuristics, not NLP or machine learning.

### Primary Editorial Signals (Always Shown)

These signals indicate major editorial moments and are **always surfaced prominently**:

**Status transitions** (from Git diff analysis):
- Draft → Accepted
- Draft → Rejected
- Accepted → Final
- Any status → Withdrawn
- Detected by parsing diff output for Status field changes (e.g., `-Status: Draft` → `+Status: Accepted`)

**Why primary**: Status transitions often represent LinkedIn-worthy moments — decisions made, proposals accepted, designs finalized. A single commit changing status can be more editorially significant than dozens of content edits.

### Secondary Content Signals

These signals provide additional context but don't override status transitions:

**From current file content:**
- **Normative language presence** – MUST / MUST NOT, SHOULD / SHOULD NOT (RFC 2119 keywords)
- **Deprecation language** – "deprecated", "removed", "no longer"

**From commit patterns:**
- **Legacy cleanup** – Small edits to long-dormant PEPs
- **Documentation updates** – Changes to non-normative sections

### Signal Detection Philosophy

Signal detection is intentionally:

- **Conservative** – Prefer false negatives over false positives
- **Explainable** – Every signal has a clear, inspectable rule
- **Inspectable** – Humans can verify signals by reading diffs
- **Reversible** – Signals suggest attention, don't block output
- **Status-first** – Status transitions are treated as more significant than content changes

## Output Expectations

pepalyzer must support at least two output modes.

### Human-readable summary (default)

Designed for monthly review, editorial note-taking, and stewardship reflection.

**Output guarantees** (required for useful output):
- Every changed PEP is shown (regardless of commit count)
- Every entry includes: PEP number, title, current status, abstract, commit count
- Commit count is **always displayed** as contextual information (e.g., `[3 commits]`)
- Commit count is shown as trailing context, not as a measure of importance or filter criterion
- Status transitions are shown prominently when detected
- PEPs with no detected signals still show full identity, status, abstract, and commit count

**Example output:**

```
PEP 815 — Disallow reference cycles in tp_traverse (Draft) [3 commits]
  Abstract: This PEP proposes disallowing reference cycles in tp_traverse
            to prevent memory leaks in extension modules.
  Files: pep-0815.rst
  Signals:
    - Normative language added (MUST NOT)
    - Contains RFC 2119 keywords

PEP 821 — Improve importlib security (Accepted) [2 commits]
  Abstract: This PEP addresses security vulnerabilities in importlib by
            adding validation checks for module loading paths.
  Files: pep-0821.rst, pep-0821-examples.py
  Signals:
    - STATUS CHANGED: Draft → Accepted ⭐
    - Minor editorial fixes

PEP 807 — Remove optional feature X (Withdrawn) [1 commit]
  Abstract: This PEP originally proposed feature X, now withdrawn after
            implementation testing revealed performance issues.
  Files: pep-0807.rst
  Signals:
    - STATUS CHANGED: Draft → Withdrawn ⭐
    - Contains deprecation language

PEP 729 — Type annotations for async iterators (Draft) [1 commit]
  Abstract: This PEP proposes standardized type annotations for async
            iterator protocols to improve type checker support.
  Files: pep-0729.rst
  (No additional signals detected)
```

**Note**: The example shows that single-commit PEPs (815, 807, 729) are given equal prominence to multi-commit PEPs. Status transitions are marked as primary signals (⭐). PEPs without signals still show full context.

### Machine-readable output (JSON)

Designed for archival, longitudinal analysis, and possible future tooling.

**Schema guarantees**:
- Every PEP includes `pep_number`, `title`, `status`, `abstract` (required fields)
- `commit_count` is included but should not be used as a filter or sort key
- Status transitions are marked with `"primary": true` in signal objects

**JSON format:**

```json
[
  {
    "pep_number": 815,
    "title": "Disallow reference cycles in tp_traverse",
    "status": "Draft",
    "abstract": "This PEP proposes disallowing reference cycles...",
    "authors": ["Sam Gross <colesbury@gmail.com>"],
    "pep_type": "Standards Track",
    "created": "2024-01-11",
    "commit_count": 3,
    "files": ["pep-0815.rst"],
    "signals": [
      {
        "type": "normative_language",
        "description": "Contains normative language (RFC 2119 keywords)",
        "primary": false
      }
    ]
  },
  {
    "pep_number": 821,
    "title": "Improve importlib security",
    "status": "Accepted",
    "abstract": "This PEP addresses security vulnerabilities...",
    "authors": ["Jane Developer <jane@python.org>"],
    "pep_type": "Standards Track",
    "created": "2024-02-01",
    "commit_count": 2,
    "files": ["pep-0821.rst", "pep-0821-examples.py"],
    "signals": [
      {
        "type": "status_transition",
        "description": "Status changed: Draft → Accepted",
        "primary": true,
        "from": "Draft",
        "to": "Accepted"
      }
    ]
  }
]
```

## Explicit Non-Goals

pepalyzer explicitly does **not**:

- **Rank PEPs by importance** — All changed PEPs are shown; humans decide what matters
- **Use commit count as a quality signal** — Frequency ≠ importance for editorial decisions
- **Filter out "low activity" PEPs** — Single-commit status changes may be the most significant
- **Predict Python's future** — Surface changes, don't interpret direction
- **Replace reading the PEP** — Provide context to help humans decide what to read
- **Perform semantic interpretation** — Use simple heuristics, not NLP
- **Automate editorial voice** — Support editorial practice, don't replace judgment
- **Modify the PEPs repository** — Read-only analysis tool
- **Fetch data from the network** — Work entirely with local Git clone

## Testing Strategy

### Unit Tests (Pure, Fast)

Unit tests validate:

- Path → PEP number extraction
- Commit record parsing
- Signal detection heuristics
- Aggregation logic

Unit tests:

- Do not require Git
- Use static fixtures
- Operate on in-memory data structures

### Integration Tests (Controlled Git Repos)

Integration tests use:

- Temporary Git repositories
- Synthetic commit histories
- Minimal PEP-like files

They validate:

- Git log parsing
- End-to-end scan behavior
- CLI output correctness

### CLI Tests

CLI tests validate:

- Argument validation
- Error messages
- Output formatting
- Exit codes

## TDD Implementation Roadmap

This section defines a concrete, bottom-up implementation plan using Test-Driven Development (TDD). Each feature builds on the previous one, starting with pure logic and progressing to external integration.

### Phase 1: Foundation - Pure Logic (No Dependencies)

#### Feature 1: PEP Number Extraction ⭐ START HERE

- **Module**: `pepalyzer/pep_parser.py`
- **Test**: `tests/test_pep_parser.py`
- **Why first**: Pure function, zero dependencies, foundational for everything else
- **Test cases**:
  - Extract PEP number from `pep-0001.rst` → `1`
  - Extract from `pep-0815.md` → `815`
  - Handle directory paths: `peps/pep-0001.rst` → `1`
  - Handle invalid paths → `None`
  - Edge cases: `pep-9999.txt`, `PEP-0001.rst` (uppercase), `pep-0001-draft.rst`
  - Non-PEP files: `README.md`, `index.html` → `None`

#### Feature 2: Data Models

- **Module**: `pepalyzer/models.py`
- **Test**: `tests/test_models.py`
- **Data structures to implement**:
  - `CommitRecord` - Contains hash, timestamp, list of changed files (input plumbing)
  - `ChangedFile` - Contains file path, change type (added, modified, deleted)
  - `PepMetadata` - Contains title, status, abstract, authors, pep_type, created (extracted from files)
  - `PepActivity` - One-row-per-PEP structure combining metadata + change summary
    - Identity: pep_number
    - Required: title, status, abstract
    - Optional: authors, pep_type, created
    - Auxiliary: commit_count, files
  - `PepSignal` - Contains PEP number, signal type, description, primary flag
- **Test cases**:
  - Model creation with valid data
  - Immutability (prefer `@dataclass(frozen=True)`)
  - Handle edge cases: None metadata fields, empty lists
  - String representation for debugging
  - PepActivity requires pep_number but allows None for metadata fields

### Phase 2: Core Logic - Stateless Transformations

#### Feature 3: PEP Change Identification & De-duplication

- **Module**: `pepalyzer/aggregator.py`
- **Test**: `tests/test_aggregator.py`
- **Responsibility**: Transform list of CommitRecords into PEP-centric PepActivity objects (one per PEP)
- **Test cases**:
  - Identify unique PEPs that changed
  - De-duplicate multiple commits to same PEP into single entry
  - Handle multiple files for same PEP in one commit
  - **Handle commits with no PEP files** (silently filter out)
  - **Handle single commit touching multiple PEPs** (create separate entry for each)
  - Verify commit_count is per-PEP (sum across PEPs may exceed total commits)
  - Filter non-PEP files (README, .github/, etc.)
  - Sort by PEP number (ascending) for consistent output
  - Track commit count as auxiliary metadata (always shown, not for ranking)

#### Feature 4: Signal Detection

- **Module**: `pepalyzer/signals.py`
- **Test**: `tests/test_signals.py`
- **Responsibility**: Detect editorial signals in file content or metadata
- **Test cases**:
  - Detect status changes: `Status: Draft` → `Status: Accepted`
  - Detect deprecation keywords: "deprecated", "removed", "no longer"
  - Detect normative language: MUST, MUST NOT, SHOULD, SHOULD NOT (RFC 2119)
  - Avoid false positives in code examples or quoted text
  - Return empty list when no signals found

### Phase 3: External Integration - Git

#### Feature 5: Git Adapter

- **Module**: `pepalyzer/git_adapter.py`
- **Test**: `tests/test_git_adapter.py` (integration test)
- **Responsibility**: Read commit history from a local Git repository
- **Test cases**:
  - Parse `git log --name-status --since=<date>` output
  - Extract commit hash, author date, changed files
  - Handle `--since` time windows (30d, 7d, 2024-01-01)
  - Gracefully handle git errors (not a git repo, invalid path)
  - Return empty list for repos with no commits in window

### Phase 4: Output & Presentation

#### Feature 6: Human-Readable Formatter

- **Module**: `pepalyzer/formatters.py`
- **Test**: `tests/test_formatters.py`
- **Responsibility**: Format PepActivity and PepSignal objects as readable text with required context
- **Test cases**:
  - Always show title, status, abstract for every PEP (required fields)
  - Format single PEP with signals
  - Format multiple PEPs sorted by PEP number
  - Handle PEPs with no signals (show identity, status, abstract only)
  - Mark status transition signals as primary
  - Handle empty results (no PEPs changed)
  - Proper indentation and spacing
  - Gracefully handle missing metadata (show "Unknown" rather than hiding PEP)

**Example output:**
```
PEP 815 — Disallow reference cycles in tp_traverse (Draft) [3 commits]
  Abstract: This PEP proposes disallowing reference cycles...
  Files: pep-0815.rst
  Signals:
    - Normative language added (MUST NOT)

PEP 821 — Improve importlib security (Accepted) [1 commit]
  Abstract: This PEP addresses security vulnerabilities...
  Files: pep-0821.rst
  Signals:
    - STATUS CHANGED: Draft → Accepted ⭐
```

#### Feature 7: JSON Formatter

- **Module**: `pepalyzer/formatters.py`
- **Test**: `tests/test_formatters.py`
- **Responsibility**: Format results as machine-readable JSON with required metadata
- **Test cases**:
  - Output valid JSON schema
  - Include all required fields (pep_number, title, status, abstract)
  - Include optional fields (authors, pep_type, created)
  - Include auxiliary fields (commit_count, files)
  - Mark primary signals with "primary": true
  - Handle empty results (return empty array)
  - Pretty-print with indentation

**Example output:**
```json
[
  {
    "pep_number": 815,
    "title": "Disallow reference cycles in tp_traverse",
    "status": "Draft",
    "abstract": "This PEP proposes disallowing reference cycles...",
    "authors": ["Sam Gross <colesbury@gmail.com>"],
    "pep_type": "Standards Track",
    "created": "2024-01-11",
    "commit_count": 3,
    "files": ["pep-0815.rst"],
    "signals": [
      {
        "type": "normative_language",
        "description": "Normative language added (MUST NOT)",
        "primary": false
      }
    ]
  }
]
```

### Phase 5: CLI & Orchestration

#### Feature 8: CLI Argument Parsing

- **Module**: `pepalyzer/cli.py`
- **Test**: `tests/test_cli.py`
- **Responsibility**: Parse command-line arguments and orchestrate pipeline
- **Test cases**:
  - Parse `scan` subcommand with repository path
  - Parse `--since` argument (30d, 7d, 2024-01-01)
  - Parse `--format` argument (text, json)
  - Require repository path argument
  - Validate repository path exists
  - Show helpful error messages
  - Exit codes: 0 (success), 1 (error), 2 (invalid arguments)

**Example commands:**
```bash
pepalyzer scan ~/src/peps --since 30d
pepalyzer scan ~/src/peps --since 2024-01-01 --format json
```

#### Feature 9: End-to-End Integration

- **Test**: `tests/test_integration.py`
- **Responsibility**: Validate the complete pipeline with real Git operations
- **Test cases**:
  - Create temporary Git repository
  - Add synthetic PEP files and commits
  - Run full scan pipeline
  - Verify output contains expected PEPs and signals
  - Test both text and JSON output formats

### Implementation Order Summary

1. **PEP Number Extraction** ← 🎯 **START HERE**
2. Data Models
3. Change Aggregation
4. Signal Detection
5. Git Adapter
6. Formatters (Human + JSON)
7. CLI Argument Parsing
8. End-to-End Integration

### TDD Cycle for Each Feature

Each feature follows the Red-Green-Refactor cycle:

1. **Red** - Write a failing test that describes the desired behavior
2. **Green** - Write the minimal code needed to pass the test
3. **Refactor** - Improve code quality without changing behavior
4. **Repeat** - Add more test cases to cover edge cases

### Success Criteria

Each feature is complete when:

- ✅ All tests pass
- ✅ Test coverage is >90% for the module
- ✅ Code passes pre-commit hooks (black, flake8, mypy, bandit)
- ✅ Edge cases are documented
- ✅ Next feature can build on this foundation

## Evolution Path (Non-Binding)

Future versions may include:

- Longitudinal trend tracking
- Historical comparisons
- Optional semantic analysis
- NLP over selected PEP corpora

These are explicitly out of scope for the initial architecture.

## Summary

pepalyzer is designed as **infrastructure for editorial thinking**, not content generation or activity tracking.

The tool treats PEPs as the primary unit of meaning, using Git commits only as a change detection mechanism. It surfaces recently changed PEPs with full context (title, abstract, status) and lightweight signals (especially status transitions), allowing humans to quickly identify which PEPs warrant deeper review.

Success is measured by:

- **Usefulness of output** — Can a human understand what changed and why it might matter?
- **Respect for editorial judgment** — Does the tool support decisions without making them?
- **Clarity of signals** — Are status transitions and content changes immediately obvious?
- **Completeness** — Are all changed PEPs shown, regardless of commit frequency?
- **Trustworthiness** — Can signals be verified by reading the source?
- **Long-term maintainability** — Simple, inspectable architecture

The architecture favors **PEP-centric analysis**, restraint, explicitness, and editorial humility over commit-counting, automation, and novelty.

**Core truth**: A single commit finalizing a PEP's status is more editorially significant than a hundred typo fixes. The tool should make this obvious, not obscure it.
