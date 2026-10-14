---
name: code-change-analyzer
description: Deterministic and evidence-based analysis of Git changes, AST structural differences, downstream module impacts, and test recommendations.
---

# Code Change Analyzer Skill

## Overview
This skill guides the AI coding agent in analyzing existing code modifications before proposing or applying code changes. It establishes a rigorous, evidence-based procedure using Git status, Git diff, Python AST inspection, and dependency tracing to determine exactly what changed, what may break, and what tests must run.

---

## Core Questions Answered
1. **What changed in the code?** (Exact diff lines and files involved).
2. **Which files were added, modified, renamed, or deleted?** (Categorized by Git state).
3. **Which functions, classes, modules, APIs, or configurations were affected?** (Verified via AST structural extraction).
4. **Why does each change matter?** (Semantic purpose and structural intent).
5. **What behavior may have changed?** (Functional alterations, signature changes, side-effects).
6. **Which dependencies or downstream components may be affected?** (Modules importing modified files).
7. **Which tests should be executed?** (Targeted unit and integration tests mapped to changed code).
8. **What is confirmed versus inferred?** (Strictly labeled confidence ratings).
9. **Did the change introduce potential errors, security problems, or regressions?** (Syntax errors, broken signatures, missing parameters, unhandled exceptions).

---

## Evidence & Confidence Standards

All findings must be classified using explicit confidence ratings:
- `[Confirmed]`: Directly observed in `git status`, `git diff`, or syntax tree nodes. Unambiguous facts.
- `[Likely]`: Inferred from verified static imports, callers, or standard project naming conventions; requires runtime validation.
- `[Unknown]`: Insufficient static evidence (e.g. dynamic imports, reflection, environment variables, external API contracts).

### Cardinal Rules
- **No Unsolicited Modifications**: Never modify source code when the user only inquires what changed.
- **No Git State Mutation**: Never run `git reset`, `git checkout --`, `git restore`, `git commit`, `git add`, or `git push` during analysis.
- **No False Positives**: Never claim a file has changed merely because it exists in the repository.
- **Do Not Conflate Git States**: Clearly distinguish **Unstaged changes**, **Staged changes**, **Untracked files**, and **Committed history**.
- **Inspect Non-Code Changes**: Do not treat generated files, lockfiles (`package-lock.json`), or whitespace formatting as functional modifications without reviewing their contents.

---

## 10-Step Deterministic Analysis Workflow

### Step 1: Inspect Git Status
Examine working tree state without modifying files:
```bash
git status --porcelain=v1 -uall
```
Identify index status (staged) vs worktree status (unstaged) and untracked files (`??`).

### Step 2: Inspect Unstaged Changes
Inspect raw line diffs for unstaged modifications:
```bash
git diff --no-color
```
Note lines added (`+`), lines removed (`-`), and modified line blocks.

### Step 3: Inspect Staged Changes
Inspect modifications that have already been added to the staging index:
```bash
git diff --cached --no-color
```

### Step 4: Categorize Changed Files
Classify every detected path into one of five categories:
- **Added (`A`)**: New file introduced.
- **Modified (`M`)**: Existing file updated.
- **Deleted (`D`)**: Existing file removed.
- **Renamed (`R`)**: File moved or renamed (trace original path `old -> new`).
- **Untracked (`??`)**: Uncommitted new file not yet staged.

### Step 5: Read Relevant Source Context
Read the modified file content around the changed lines using bounded file reading. Do not read unrelated files or scan entire large codebases unnecessarily.

### Step 6: Compare Function and Class Definitions via AST
For Python files, perform AST diffing:
- **Function Changes**: Added functions, deleted functions, altered signatures (added/removed/renamed arguments).
- **Class Changes**: Added/removed classes, modified class bases, altered method sets.
- **Import Changes**: Added or removed import statements.
- **Syntax Validation**: Check for `SyntaxError` in either baseline (`HEAD`) or working tree.

### Step 7: Trace Imports, Callers, and Downstream Components
- Find internal project files that import the modified modules.
- Check if public function/class signatures were altered in a way that breaks existing callers.
- Identify configuration files (`.env`, `config.py`, `settings.json`) that govern the modified logic.

### Step 8: Identify Potential Regressions and Missing Coverage
- Check if argument counts or types changed without updating caller locations.
- Check if default values were removed.
- Check if new exceptions can be raised.
- Check if corresponding unit test files exist and whether tests were added for the new behavior.

### Step 9: Recommend Specific Validation Commands
Formulate exact, runnable test commands targeting the affected areas:
```bash
# Focused test execution
pytest tests/test_<affected_module>.py -v

# Full suite verification if core dependencies changed
pytest -v
```

### Step 10: Deliver a Concise, Evidence-Based Change Report
Present the findings organized by confirmed facts, downstream impact, and recommendations.

---

## Output Template

When reporting code changes to the user, format the response as follows:

```markdown
### Code Change Analysis Report

#### 1. File Status Summary [Confirmed]
- **Modified**: `path/to/file.py` (unstaged)
- **Added**: `path/to/new_file.py` (staged)
- **Deleted**: `path/to/old_file.py`
- **Renamed**: `path/to/old.py` -> `path/to/new.py`

#### 2. Structural & AST Modifications [Confirmed]
- `path/to/file.py`:
  - Added function: `calculate_total(items, tax_rate)`
  - Modified function: `process_order(order_id)` — added parameter `dry_run=False`
  - Removed import: `import legacy_module`

#### 3. Semantic Impact & Behavior Changes [Likely]
- **Reason**: Enhances order processing with dry-run capabilities.
- **Potential Risk**: Callers using positional arguments might be affected if parameter positions changed.

#### 4. Downstream Dependencies & Impacted Modules [Likely]
- Changes to `order_service` affect:
  - `controllers/order_controller.py`
  - `tasks/billing_worker.py`

#### 5. Recommended Validation Commands [Likely]
- `pytest tests/test_order_service.py -v`
- `pytest tests/test_order_controller.py -v`

#### 6. Static Analysis Limitations [Unknown]
- Dynamic event dispatching or runtime plugin hooks cannot be statically verified.
```

---

## Reusability & Compatibility
This skill is repository-agnostic and language-adaptable. While AST steps specifically leverage Python's `ast` parser for Python source files, Steps 1–5 and 8–10 apply universally to any Git-tracked project across languages.
