# Analysis of PEP Diff Text for Interesting Signals

This document analyzes the `git log` diffs from the `peps` repository over the last 90 days to identify patterns, or "signals," that indicate technically interesting or editorially significant changes.

---

## 1. Status Transitions

This is the most direct and important signal. Changes to the `Status` field mark key lifecycle moments for a PEP.

*   **Why it's interesting:** It represents a formal decision by the Python steering council or PEP editors (e.g., Draft -> Accepted, Accepted -> Final, or Draft -> Withdrawn). This is the primary signal of a PEP's progression.
*   **Example:** PEP 814 (`frozendict`) being accepted.

```diff
--- a/peps/pep-0814.rst
+++ b/peps/pep-0814.rst
@@ -2,11 +2,12 @@
 Title: Add frozendict built-in type
 Author: Victor Stinner <vstinner@python.org>, Donghee Na <donghee.na@python.org>
 Discussions-To: https://discuss.python.org/t/104854
-Status: Draft
+Status: Accepted
 Type: Standards Track
 Created: 12-Nov-2025
 Python-Version: 3.15
 Post-History: `13-Nov-2025 <https://discuss.python.org/t/104854>`__
+Resolution: `11-Feb-2026 <https://discuss.python.org/t/pep-814-add-frozendict-built-in-type/104854/121>`__
```

---

## 2. Addition of a `Resolution` Link

This often accompanies a `Status` change and points directly to the official decision.

*   **Why it's interesting:** It provides a direct link to the specific discussion and justification for a PEP's acceptance, rejection, or withdrawal, offering valuable context.
*   **Example:** PEP 815 being marked `Final`.

```diff
--- a/peps/pep-0815.rst
+++ b/peps/pep-0815.rst
@@ -5,12 +5,16 @@
 Sponsor: Emma Harper Smith <emma@python.org>
 PEP-Delegate: Paul Moore <p.f.moore@gmail.com>
 Discussions-To: https://discuss.python.org/t/105232
-Status: Draft
+Status: Final
 Type: Standards Track
 Topic: Packaging
 Created: 04-Dec-2025
 Post-History: `09-Jun-2025 <https://discuss.python.org/t/94968>`__,
               `08-Dec-2025 <https://discuss.python.org/t/105232>`__,
+Resolution: `28-Jan-2026 <https://discuss.python.org/t/105232/10>`__
```

---

## 3. Introduction of a New PEP File

The creation of a new PEP file is the very first step in proposing a new idea.

*   **Why it's interesting:** It signals a brand new proposal entering the ecosystem. These are often the most technically significant diffs as they introduce novel concepts. PEP 818 is a prime example, proposing a major new feature (JS FFI).
*   **Example:** The initial commit for PEP 818.

```diff
--- /dev/null
+++ b/peps/pep-0818.rst
@@ -0,0 +1,3372 @@
+PEP: 818
+Title: Adding the Core of the Pyodide Foreign Function Interface to Python
+Author: Hood Chatham <roberthoodchatham at gmail.com>
+Sponsor: Łukasz Langa <lukasz at python.org>
+Discussions-To: https://discuss.python.org/t/pep-818-upstreaming-the-pyodide-ffi/105530
+Status: Draft
+Type: Standards Track
+Created: 10-Dec-2025
+Python-Version: 3.15
+
+Abstract
+========
+
+Pyodide is a distribution of Python for JavaScript runtimes, including browsers.
...
```

---

## 4. Substantial Changes to Core Sections (Rationale, Specification)

Significant additions or removals from `Rationale` or `Specification` sections indicate an evolution of the core idea.

*   **Why it's interesting:** A change in rationale means the justification for the PEP is being refined. A change in the specification is a direct modification of the proposed technical implementation.
*   **Example:** PEP 814 (`frozendict`) removing arguments from its rationale, likely in response to community feedback.

```diff
--- a/peps/pep-0814.rst
+++ b/peps/pep-0814.rst
@@ -43,10 +44,6 @@ desirable:
 * Using an immutable mapping as a function parameter's default value
   avoids the problem of mutable default values.

-* Immutable mappings can be used to safely share dictionaries across
-  thread and asynchronous task boundaries. The immutability makes it
-  easier to reason about threads and asynchronous tasks.
-
 There are already third-party ``frozendict`` and ``frozenmap`` packages
 available on PyPI, proving that there is demand for
 immutable mappings.
```
---

## 5. Changes to Normative Language (RFC 2119 keywords)

Changes involving keywords like `MUST`, `SHOULD`, and `MAY` can significantly alter the strictness of a specification.

*   **Why it's interesting:** Elevating a `SHOULD` to a `MUST` strengthens a requirement, while the reverse weakens it. This directly impacts how implementers must conform to the PEP.
*   **Example:** PEP 807 refining its discovery mechanism. While this example doesn't change a keyword, it changes the technical implementation of a `MUST` constraint.

```diff
--- a/peps/pep-0807.rst
+++ b/peps/pep-0807.rst
@@ -114,7 +114,7 @@ apply to all parts of this PEP's specification:
   clients **MUST** reject any URLs that do not meet this constraint.

   In practice, this means that a discovery request to
-  ``https://upload.example.com/.well-known/pytp/{key}`` can only
+  ``https://upload.example.com/.well-known/pytp?discover={key}`` can only
   return URLs with the ``upload.example.com`` host.
```
---

## 6. Addition of New Sections

The addition of entirely new top-level sections can signal a significant expansion or clarification of a PEP.

*   **Why it's interesting:** Adding a "Change History" or "Deferred Ideas" section provides meta-level context about the PEP's evolution.
*   **Example:** PEP 12 and PEP 1 adding a `Change History` section.

```diff
--- a/peps/pep-0001.rst
+++ b/peps/pep-0001.rst
@@ -876,6 +887,14 @@ Footnotes
 .. _Contributing Guide: https://github.com/python/peps/blob/main/CONTRIBUTING.rst


+Change History
+==============
+
+* 2026-02-02
+
+  * Added an optional ``Change History`` section for PEPs, for summarizing changes when updating the
+    ``Post-History`` header.
+
 Copyright
 =========
```

---

## 7. Infrastructure and Process Changes

Changes to files outside of the `peps/` directory can indicate important process changes that affect all PEPs.

*   **Why it's interesting:** Modifications to `.github/workflows`, `release_management/`, or root configuration files show changes in CI, release processes, or linting, which are technically significant for the project's health and maintenance.
*   **Example:** Updating the CI to use a new linting tool or adding a new release management script.

```diff
--- a/.github/workflows/lint.yml
+++ b/.github/workflows/lint.yml
@@ -2,8 +2,7 @@ name: Lint PEPs

 on: [push, pull_request, workflow_dispatch]

-permissions:
-  contents: read
+permissions: {}

 concurrency:
   group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}
```
