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
