# Git Diff Signal Analysis for Pepalyzer

## Context

This analysis examines 90 days of git diffs from the PEPs repository (../peps) to identify signal categories that can be extracted from diff text to surface technically interesting PEP content. The goal is to extend pepalyzer's signal detection beyond just status transitions.

---

## Methodology

Analyzed git log with diffs from the last 90 days using:
```bash
git log --since="90 days ago" -p --stat
```

Examined ~50 commits across various PEP changes including:
- Status transitions (PEP 814, 815, 534, 686, 798)
- New PEPs (818, 817, 821, 822, 819, 820, 797)
- Content updates (PEP 820, 821, 807, 822)
- Metadata updates (Discussion-To, Post-History, Resolution)
- Infrastructure changes (CSS, CI, documentation)
- Release schedule updates (PEP 790, 719, 745)

---

## Signal Categories Identified

### 1. Status Transitions ⭐ (signal_value=100)
**Already known, but confirms high importance**

**Diff Pattern:**
```diff
-Status: Draft
+Status: Final
```
or
```diff
-Status: Accepted
+Status: Final
```

**Additional Indicator:** Resolution field often added at same time:
```diff
+Resolution: `28-Jan-2026 <https://discuss.python.org/t/105232/10>`__
```

**Examples:**
- PEP 815: Draft → Final (2404ca8d)
- PEP 814: Draft → Accepted (853aed4b)
- PEP 798: Draft → Accepted (2bd92170)
- PEP 686: Draft → Final (e57d6fab)
- PEP 534: Draft → Withdrawn (c9a6f284)

**Why Important:** Marks major lifecycle milestones - these are "LinkedIn-worthy" moments.

---

### 2. New PEP Creation 🆕 (signal_value=100)
**High-value signal for tracking emerging proposals**

**Diff Pattern:**
```diff
+++ b/peps/pep-XXXX.rst
@@ -0,0 +1,XXX @@
+PEP: XXXX
+Title: ...
+Author: ...
+Status: Draft
```

**Key Indicators:**
- New file with `pep-XXXX.rst` or `pep-XXXX.md`
- File starts with PEP header (PEP:, Title:, Author:, Status: Draft)
- Large addition (typically 100+ lines)
- Change type 'A' (Added) in git log

**Examples:**
- PEP 818: Foreign Function Interface (616c96ae) - 3372 new lines
- PEP 821: TypedDict unpacking (d53fdc55) - 408 new lines
- PEP 822: d-strings (8b2e1d54)
- PEP 820: PySlot (0df31908)
- PEP 797: Shared Object Proxies (1eab7c2d)

**Why Important:** Brand new proposals entering the PEP process - high editorial interest.

---

### 3. Canonical Spec Designation 🎯 (signal_value=90)
**Marks PEPs that become authoritative specifications**

**Diff Pattern:**
```diff
+.. canonical-pypa-spec:: :ref:`packaging:binary-distribution-format`
```

**Key Indicators:**
- Addition of `.. canonical-pypa-spec::` directive
- Usually appears when PEP reaches Final status
- Indicates this PEP is THE specification for a feature

**Examples:**
- PEP 815: Added canonical spec marker when marked Final (2404ca8d)

**Why Important:** Marks PEPs that become the authoritative source - critical for documentation.

---

### 4. Metadata State Changes 📋 (signal_value=60)
**Indicates PEP moving through process stages**

**Diff Pattern:**
```diff
-Discussions-To: Pending
+Discussions-To: https://discuss.python.org/t/105952
```
or
```diff
-Post-History: `28-Jun-2025 <https://discuss.python.org/t/96975>`__
+Post-History: `28-Jun-2025 <https://discuss.python.org/t/96975>`__,
+              `31-Jan-2026 <https://discuss.python.org/t/105952>`__
```

**Key Indicators:**
- Discussions-To field changes from "Pending" to actual URL
- New Post-History entries (new discussion rounds)
- PEP-Delegate assignments
- Sponsor additions
- Python-Version field changes

**Examples:**
- PEP 821: Discussion links added (0d2bacb3)
- PEP 817: Discussions-To updated (67c87140)
- PEP 819: Discussion-To and Post-History updated (93f4723d)
- PEP 820: Discussion links added (166e82e8)

**Why Important:** Shows active PEP progression through review process.

---

### 5. API/Specification Changes 🔧 (signal_value=70)
**Substantive technical content changes**

**Diff Pattern:**
```diff
+The following function will be added::
+    PyObject *PyType_FromSlots(const PySlot *slots);
```
or
```diff
-This proposal uses fixed-width integers (``uint16_t``), for slot IDs and
+This proposal uses fixed-width integers (``uint16_t``) for slot IDs and
```

**Key Indicators:**
- Addition/removal of function signatures
- Changes to specification sections
- Addition of new requirements (MUST, SHOULD, SHALL)
- Struct/class/API definition changes
- Changes to Abstract or Specification sections
- Changes based on "discussion & implementation"

**Examples:**
- PEP 820: API changes based on discussion (8c68109a)
- PEP 822: Spec and rejected ideas updated (e9d6d5ec)
- PEP 797: Revisions from discussion round (c9128965)
- PEP 807: Feature negotiation additions (9f610690)
- PEP 821: New TypedDict unpacking spec (d53fdc55)

**Why Important:** Core technical content is evolving - important for implementers.

---

### 6. Normative Language Changes 📝 (signal_value=50)
**Already partially implemented, but diff-based detection is more accurate**

**Diff Pattern:**
```diff
+Extensions MUST implement this protocol
```
or
```diff
-Extensions should consider
+Extensions MUST consider
```

**Key Indicators:**
- Addition of RFC 2119 keywords (MUST, MUST NOT, SHOULD, SHOULD NOT, SHALL, SHALL NOT, REQUIRED)
- Changes from permissive to required language
- Addition of requirement sections

**Current Detection:** Already implemented in `signals.py` but only detects presence, not additions/changes.

**Why Important:** Indicates strengthening of requirements - affects implementation obligations.

---

### 7. Deprecation/Removal Additions ⚠️ (signal_value=60)
**Already implemented, but diff-based detection is more accurate**

**Diff Pattern:**
```diff
+The existing slot structures and related API is soft-deprecated.
+
+(That is: they will continue to work without warnings, and it'll be fully
+documented and supported, but we plan to not add any new features to it.)
```
or
```diff
+To allow changing the edge case behaviour in the (far) future,
+and to allow freedom for possible alternative implementations of the C API,
+we'll start issuing runtime deprecation warnings in these cases.
```

**Key Indicators:**
- Addition of "deprecated", "soft-deprecated", "removed", "no longer"
- Addition of deprecation warning sections
- Removal of feature documentation

**Current Detection:** Already implemented but only detects presence.

**Examples:**
- PEP 820: Soft-deprecation section added (8c68109a)

**Why Important:** Warns about future-incompatible changes.

---

### 8. Section Structure Changes 📑 (signal_value=40)
**Major organizational changes to PEP**

**Diff Pattern:**
```diff
+Rationale
+=========
+
+Design goals
+------------
```
or
```diff
-Future Work
-===========
-
-We are also going to make ``frozendict`` to be more efficient
```

**Key Indicators:**
- Addition of major new sections (Rationale, Specification, Rejected Ideas, etc.)
- Removal of entire sections
- Section heading changes
- Reorganization of content

**Examples:**
- PEP 814: Thread Safety section rewritten, Future Work removed (853aed4b)
- PEP 820: Added pep820-rationale anchor (8c68109a)
- PEP 821: Complete new specification with multiple sections (d53fdc55)

**Why Important:** Indicates major content revisions or clarifications.

---

### 9. Release Schedule Updates 📅 (signal_value=35)
**For release management PEPs (PEP 719, 745, 790, etc.)**

**Diff Pattern:**
```diff
-stage = "3.15.0 alpha 6"
-state = "expected"
-date = 2026-02-10
+stage = "3.15.0 alpha 6"
+state = "actual"
+date = 2026-02-11
```
or
```diff
+- 3.15.0 alpha 6: Wednesday, 2026-02-11

 Expected:

-- 3.15.0 alpha 6: Tuesday, 2026-02-10
```

**Key Indicators:**
- Changes from "expected" to "actual" in release dates
- Addition of new release dates
- Changes to release schedule tables
- Updates to python-releases.toml

**Examples:**
- PEP 790: 3.15.0a6 released (e03cc902)
- PEP 790: 3.15.0a4 released (93ea7f40)
- PEP 719, 745: 3.13.12 and 3.14.3 released (0514eb94)

**Why Important:** Tracks Python release progress - important for release managers.

---

### 10. PEP Cross-Reference Additions 🔗 (signal_value=25)
**Shows relationships between PEPs**

**Diff Pattern:**
```diff
+This interface is similar to :pep:`776` for Emscripten support.
```
or
```diff
+See also :pep:`692` (Unpack for **kwargs) and :pep:`728` (extra_items).
```

**Key Indicators:**
- Addition of `:pep:` role references
- Addition of "See also" sections
- References to related proposals

**Why Important:** Helps understand PEP ecosystem and dependencies.

---

### 11. Editorial/Typo Fixes 📝 (signal_value=5)
**Low-value but common changes**

**Diff Pattern:**
```diff
-Users MUST impliment this
+Users MUST implement this
```

**Key Indicators:**
- Commit messages mentioning "typo", "fix", "warning"
- Small single-line changes
- Sphinx directive fixes
- Formatting corrections

**Examples:**
- PEP 512: Fix Sphinx warnings (8778a1bb)
- PEP 788: Fix a typo (e7f57ee0)
- PEP 523: Fix Sphinx warnings (4dc116cc)

**Why Important:** Usually not interesting, but shouldn't be ignored completely (may indicate active maintenance).

---

### 12. Process Documentation Changes 📖 (signal_value=30)
**Updates to PEP 1, 12, 101, 387 etc.**

**Diff Pattern:**
```diff
+Add a Change History section
```
or
```diff
-Remove the release from the list of "Active Python Releases"
+- In python-releases.toml_, set the branch status to end-of-life.
```

**Key Indicators:**
- Changes to meta-PEPs (PEP 1, 12, 101, 387)
- Addition of new process requirements
- Updates to release management procedures

**Examples:**
- PEP 12 & 1: Add Change History section (d0dce1d8)
- PEP 101: Remove manual steps (073e5ea7, 1c0dc82c)
- PEP 387: Update discussion venues (c18506d7, 9b469754)

**Why Important:** Changes to how PEPs are managed - meta-level editorial interest.

---

## Recommendations for Implementation

### Priority 1: High-Value Signals (Implement First)
1. **Status Transitions** (100) - Already planned, highest value
2. **New PEP Creation** (100) - Easy to detect (check change_type='A' + PEP header)
3. **Canonical Spec Designation** (90) - Easy to detect (canonical-pypa-spec directive)

### Priority 2: Medium-Value Signals (Implement Next)
4. **API/Specification Changes** (70) - Detect changes to "Specification" section
5. **Metadata State Changes** (60) - Detect Discussions-To, Post-History, Resolution changes
6. **Deprecation Additions** (60) - Diff-based version of existing detection

### Priority 3: Lower-Value Signals (Optional)
7. **Normative Language Changes** (50) - Diff-based version
8. **Section Structure Changes** (40) - Detect major section additions/removals
9. **Release Schedule Updates** (35) - For release PEPs only
10. **Process Documentation Changes** (30) - For meta-PEPs

### Priority 4: Background Signals (Mostly for Filtering)
11. **PEP Cross-Reference Additions** (25) - Shows relationships
12. **Editorial/Typo Fixes** (5) - Mostly noise, but useful for filtering

---

## Implementation Strategy

### Phase 1: Add git diff capability to aggregator
- Modify `git_adapter.py` to support `get_commit_diff(hash, file_path)`
- Use `git show <hash> -- <file_path>` to get unified diff for specific files
- Return diff text for parsing

### Phase 2: Create diff-based signal detection
- New module: `diff_signals.py`
- Function: `detect_signals_from_diff(diff_text: str, pep_number: int) -> list[PepSignal]`
- Parse unified diff format (+/- lines)
- Extract patterns for each signal type

### Phase 3: Integrate with CLI
- Pass commit hash to aggregator
- For each PEP in each commit, get diff
- Run both content-based and diff-based signal detection
- Merge signals (deduplicate if same signal detected both ways)

---

## Diff Parsing Patterns

### Status Transition Detection
```python
def detect_status_transition(diff_text: str, pep_number: int) -> list[PepSignal]:
    """Detect status field changes in diff."""
    old_status = None
    new_status = None

    for line in diff_text.split('\n'):
        if line.startswith('-Status:'):
            old_status = line.split(':', 1)[1].strip()
        elif line.startswith('+Status:'):
            new_status = line.split(':', 1)[1].strip()

    if old_status and new_status and old_status != new_status:
        return [PepSignal(
            pep_number=pep_number,
            signal_type="status_transition",
            description=f"Status: {old_status} → {new_status}",
            signal_value=100,
        )]
    return []
```

### New PEP Detection
```python
def detect_new_pep(commit: CommitRecord, file_path: str) -> list[PepSignal]:
    """Detect new PEP file creation."""
    for changed_file in commit.files:
        if changed_file.path == file_path and changed_file.change_type == 'A':
            # File was added - check if it's a new PEP
            pep_number = extract_pep_number(file_path)
            if pep_number:
                return [PepSignal(
                    pep_number=pep_number,
                    signal_type="new_pep",
                    description="New PEP created",
                    signal_value=100,
                )]
    return []
```

### Canonical Spec Detection
```python
def detect_canonical_spec(diff_text: str, pep_number: int) -> list[PepSignal]:
    """Detect addition of canonical spec marker."""
    for line in diff_text.split('\n'):
        if line.startswith('+') and 'canonical-pypa-spec::' in line:
            return [PepSignal(
                pep_number=pep_number,
                signal_type="canonical_spec",
                description="Designated as canonical specification",
                signal_value=90,
            )]
    return []
```

### Metadata Changes Detection
```python
def detect_metadata_changes(diff_text: str, pep_number: int) -> list[PepSignal]:
    """Detect PEP metadata changes."""
    signals = []

    for line in diff_text.split('\n'):
        # Discussions-To from Pending → URL
        if line.startswith('-Discussions-To:') and 'Pending' in line:
            signals.append(PepSignal(
                pep_number=pep_number,
                signal_type="discussion_started",
                description="Discussion URL added",
                signal_value=60,
            ))
        # Post-History additions
        elif line.startswith('+Post-History:') or (
            line.startswith('+              `') and 'discuss.python.org' in line
        ):
            signals.append(PepSignal(
                pep_number=pep_number,
                signal_type="new_discussion_round",
                description="New discussion round",
                signal_value=60,
            ))
        # Resolution added
        elif line.startswith('+Resolution:'):
            signals.append(PepSignal(
                pep_number=pep_number,
                signal_type="resolution_added",
                description="Resolution link added",
                signal_value=60,
            ))

    return signals
```

### API Changes Detection
```python
def detect_api_changes(diff_text: str, pep_number: int) -> list[PepSignal]:
    """Detect changes to Specification or API sections."""
    in_spec_section = False
    has_spec_changes = False
    lines_changed = 0

    for line in diff_text.split('\n'):
        # Track if we're in important sections
        if any(section in line for section in ['Specification', 'Abstract', 'API']):
            in_spec_section = True
        elif line.startswith('===') or line.startswith('---'):
            in_spec_section = False

        # Count substantive changes (not just formatting)
        if in_spec_section and (line.startswith('+') or line.startswith('-')):
            stripped = line[1:].strip()
            if stripped and not stripped.startswith(('+++', '---', '@@')):
                has_spec_changes = True
                lines_changed += 1

    if has_spec_changes and lines_changed > 5:  # Threshold for substantive changes
        return [PepSignal(
            pep_number=pep_number,
            signal_type="api_changes",
            description=f"Specification changes ({lines_changed} lines)",
            signal_value=70,
        )]
    return []
```

---

## Summary

From analyzing 90 days of PEP diffs, I've identified **12 distinct signal categories** that can be extracted from diff text:

**High-Value Signals (90-100):**
- Status transitions (Draft → Final, etc.)
- New PEP creation
- Canonical spec designation

**Medium-Value Signals (40-70):**
- API/Specification changes
- Metadata state changes (Discussions-To, Post-History, Resolution)
- Deprecation additions
- Normative language changes
- Section structure changes
- Release schedule updates

**Lower-Value Signals (5-30):**
- Process documentation changes
- PEP cross-references
- Editorial/typo fixes

The most important finding is that **diff-based detection eliminates false positives** - detecting that something *changed* rather than just that it *exists* makes signals far more accurate and valuable.

Implementation should prioritize the high-value signals first (status transitions, new PEPs, canonical specs), as these provide immediate editorial value with straightforward detection logic.
