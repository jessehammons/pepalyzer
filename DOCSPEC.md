# pepalyzer — Documentation and Specification

## Overview

**pepalyzer** is a Python CLI tool that assists technical stewardship and editorial practice by analyzing recent Git commits in the Python PEPs repository and surfacing which PEPs may warrant human review and reflection.

pepalyzer does not attempt to evaluate importance, predict language direction, or automate editorial judgment. Its purpose is to turn raw repository activity into structured, inspectable signals that support calm, human-led analysis.

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

- Explicit state over implicit convenience
- Human judgment over automated interpretation
- Local Git history over remote APIs
- Minimal automation, maximal clarity
- Loose coupling between tool and data

## Usage Model

pepalyzer operates on an existing local clone of the Python PEPs repository.

### The user is responsible for:

- Cloning the PEPs repo
- Updating it via `git pull`
- Choosing when to analyze changes

### pepalyzer is responsible for:

- Reading Git history
- Extracting recent changes
- Normalizing those changes into PEP-centric structures
- Emitting structured summaries for human review

### Example usage

Run the CLI with a path to the local PEPs repository and a time window. For example, scan commits from the last 30 days:

```bash
pepalyzer scan ~/src/peps --since 30d
```

## Core Workflow

At a high level, pepalyzer implements the following pipeline:

1. Local Git repo
2. Recent commit extraction
3. File-level change aggregation
4. PEP-centric normalization
5. Light signal classification
6. Structured output for human review

Each stage is intentionally simple and testable in isolation.

## Architecture Overview

### Module Responsibilities (Conceptual)

- **CLI** – Argument parsing, orchestration, output selection
- **Git Adapter** – Read-only interaction with Git history
- **Normalization** – Map file changes to PEP numbers
- **Signal Detection** – Identify notable change patterns
- **Reporting** – Human-readable and machine-readable summaries

## Data Model (Intermediate Structures)

pepalyzer centers around explicit intermediate data structures that reflect progressively higher-level understanding.

### CommitRecord

Represents a single Git commit relevant to analysis. Contains the commit hash, timestamp, and a list of files changed.

### ChangedFile

Represents a file touched by a commit. Includes the file path and type of change (added, modified, deleted).

### PepActivity

Aggregates activity across commits for a single PEP. Answers questions like:

- Which PEPs changed?
- How often?
- Over how many commits?

### PepSignal

Represents detected editorially-interesting signals for a PEP. Signals are descriptive flags, not judgments.

## Signal Detection (Lightweight, Rule-Based)

pepalyzer uses simple heuristics, not NLP.

### Supported Signal Categories (Initial)

- **Status changes** – Draft → Accepted, Accepted → Final, Accepted → Withdrawn
- **Deprecation language** – "deprecated", "removed", "no longer"
- **Normative language presence** – MUST / MUST NOT, SHOULD / SHOULD NOT
- **Legacy cleanup** – Small edits to long-dormant PEPs, removal of unused sections

Signal detection is intentionally:

- Conservative
- Explainable
- Inspectable
- Reversible

## Output Expectations

pepalyzer must support at least two output modes.

### Human-readable summary (default)

Designed for monthly review, editorial note-taking, and stewardship reflection.

**Example:**

```
PEP 815
  Status finalized
  Removed unused security mechanism
  Indicates shift toward index-level trust

PEP 427
  Editorial cleanup
  Alignment with current packaging tooling
```

### Machine-readable output (JSON)

Designed for archival, longitudinal analysis, and possible future NLP work.

Each PEP includes its number, detected signals, and commit count.

## Explicit Non-Goals

pepalyzer explicitly does **not**:

- Rank importance
- Predict Python's future
- Replace reading the PEP
- Perform semantic interpretation
- Automate editorial voice
- Modify the PEPs repository
- Fetch data from the network

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
  - `CommitRecord` - Contains hash, timestamp, list of changed files
  - `ChangedFile` - Contains file path, change type (added, modified, deleted)
  - `PepActivity` - Contains PEP number, commit count, list of files
  - `PepSignal` - Contains PEP number, signal type, description
- **Test cases**:
  - Model creation with valid data
  - Immutability (prefer `@dataclass(frozen=True)`)
  - Handle edge cases: empty lists, None values
  - String representation for debugging

### Phase 2: Core Logic - Stateless Transformations

#### Feature 3: Change Aggregation

- **Module**: `pepalyzer/aggregator.py`
- **Test**: `tests/test_aggregator.py`
- **Responsibility**: Transform list of CommitRecords into PEP-centric PepActivity objects
- **Test cases**:
  - Group changes by PEP number
  - Count commits per PEP
  - Handle multiple files for same PEP in one commit
  - Filter non-PEP files
  - Sort by commit count (descending)

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
- **Responsibility**: Format PepActivity and PepSignal objects as readable text
- **Test cases**:
  - Format single PEP with signals
  - Format multiple PEPs sorted by activity
  - Handle PEPs with no signals (show commit count only)
  - Handle empty results (no PEPs changed)
  - Proper indentation and spacing

**Example output:**
```
PEP 815 (3 commits)
  Status finalized
  Removed unused security mechanism

PEP 427 (1 commit)
  Editorial cleanup
```

#### Feature 7: JSON Formatter

- **Module**: `pepalyzer/formatters.py`
- **Test**: `tests/test_formatters.py`
- **Responsibility**: Format results as machine-readable JSON
- **Test cases**:
  - Output valid JSON schema
  - Include all required fields (pep_number, commit_count, signals)
  - Handle empty results (return empty array)
  - Pretty-print with indentation

**Example output:**
```json
[
  {
    "pep_number": 815,
    "commit_count": 3,
    "signals": ["status_change", "security_mechanism_removed"]
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

pepalyzer is designed as **infrastructure for thinking**, not content generation.

Success is measured by:

- Clarity of output
- Trustworthiness of signals
- Ease of human interpretation
- Long-term maintainability

The architecture favors restraint, explicitness, and editorial humility over automation and novelty.
