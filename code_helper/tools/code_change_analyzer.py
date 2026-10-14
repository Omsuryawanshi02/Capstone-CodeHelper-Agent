"""Code Change Analyzer.

Provides deterministic inspection of Git changes, AST structural differences,
downstream module impacts, and test recommendations.

Adheres to evidence-based confidence levels:
- Confirmed: directly supported by git diff or AST inspection.
- Likely: downstream dependency impact based on verified import graph.
- Unknown: dynamic runtime behavior that static analysis cannot confirm.
"""

import ast
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any


@dataclass
class AstDifference:
    """Represents differences detected between two versions of a Python file."""
    added_functions: List[str] = field(default_factory=list)
    removed_functions: List[str] = field(default_factory=list)
    modified_functions: List[str] = field(default_factory=list)
    added_classes: List[str] = field(default_factory=list)
    removed_classes: List[str] = field(default_factory=list)
    modified_classes: List[str] = field(default_factory=list)
    added_imports: List[str] = field(default_factory=list)
    removed_imports: List[str] = field(default_factory=list)
    syntax_error: Optional[str] = None


@dataclass
class FileChange:
    """Represents a single changed file in Git."""
    path: str
    status: str  # 'added', 'modified', 'deleted', 'renamed', 'untracked'
    is_staged: bool
    old_path: Optional[str] = None  # for renames
    diff_content: str = ""
    ast_diff: Optional[AstDifference] = None


@dataclass
class ChangeAnalysisResult:
    """Complete structured result of code change analysis."""
    is_git_repo: bool
    has_changes: bool
    staged_changes: List[FileChange] = field(default_factory=list)
    unstaged_changes: List[FileChange] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    impacted_modules: List[str] = field(default_factory=list)
    downstream_dependents: Dict[str, List[str]] = field(default_factory=dict)
    recommended_tests: List[str] = field(default_factory=list)
    confidence_ratings: Dict[str, str] = field(default_factory=dict)
    summary: str = ""
    error: Optional[str] = None


def extract_ast_items(tree: ast.AST) -> Dict[str, Any]:
    """Extract functions, classes, and imports with signatures from an AST."""
    functions: Dict[str, str] = {}
    classes: Dict[str, Set[str]] = {}
    imports: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arg_names = [a.arg for a in node.args.args]
            functions[node.name] = f"({', '.join(arg_names)})"
        elif isinstance(node, ast.ClassDef):
            base_names = [getattr(b, "id", getattr(b, "name", "unknown")) for b in node.bases]
            methods = {m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
            classes[node.name] = methods
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imports.add(f"{mod}.{alias.name}")

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
    }


def compare_code_ast(old_code: str, new_code: str) -> AstDifference:
    """Compare two code versions using Python's AST module."""
    diff = AstDifference()

    # Parse old code
    old_tree = None
    if old_code.strip():
        try:
            old_tree = ast.parse(old_code)
        except SyntaxError as e:
            diff.syntax_error = f"Syntax error in baseline code: {e}"

    # Parse new code
    new_tree = None
    if new_code.strip():
        try:
            new_tree = ast.parse(new_code)
        except SyntaxError as e:
            diff.syntax_error = f"Syntax error in modified code: {e}"
            return diff

    old_items = extract_ast_items(old_tree) if old_tree else {"functions": {}, "classes": {}, "imports": set()}
    new_items = extract_ast_items(new_tree) if new_tree else {"functions": {}, "classes": {}, "imports": set()}

    # Compare functions
    old_funcs = old_items["functions"]
    new_funcs = new_items["functions"]
    for f in new_funcs:
        if f not in old_funcs:
            diff.added_functions.append(f)
        elif old_funcs[f] != new_funcs[f]:
            diff.modified_functions.append(f"{f}{new_funcs[f]} (was {old_funcs[f]})")

    for f in old_funcs:
        if f not in new_funcs:
            diff.removed_functions.append(f)

    # Compare classes
    old_classes = old_items["classes"]
    new_classes = new_items["classes"]
    for c in new_classes:
        if c not in old_classes:
            diff.added_classes.append(c)
        elif old_classes[c] != new_classes[c]:
            diff.modified_classes.append(c)

    for c in old_classes:
        if c not in new_classes:
            diff.removed_classes.append(c)

    # Compare imports
    old_imps = old_items["imports"]
    new_imps = new_items["imports"]
    diff.added_imports = sorted(list(new_imps - old_imps))
    diff.removed_imports = sorted(list(old_imps - new_imps))

    return diff


class CodeChangeAnalyzer:
    """Deterministic analyzer for git changes, AST impact, and tests."""

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)

    def _run_git(self, args: List[str]) -> Tuple[int, str, str]:
        """Run a git command safely in repo_root without shell execution."""
        try:
            proc = subprocess.run(
                ["git"] + args,
                cwd=self.repo_root,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return proc.returncode, proc.stdout, proc.stderr
        except FileNotFoundError:
            return 127, "", "git executable not found in PATH"
        except subprocess.TimeoutExpired:
            return 124, "", "git command timed out"
        except Exception as e:
            return 1, "", str(e)

    def is_git_repository(self) -> bool:
        """Check if repo_root is inside a valid git working tree."""
        code, stdout, _ = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return code == 0 and stdout.strip() == "true"

    def get_git_status_files(self) -> List[Tuple[str, str, bool, Optional[str]]]:
        """Parse git status --porcelain=v1.

        Returns list of (filepath, status, is_staged, old_path)
        """
        code, stdout, _ = self._run_git(["status", "--porcelain=v1", "-uall"])
        if code != 0 or not stdout.strip():
            return []

        results = []
        for line in stdout.splitlines():
            if len(line) < 4:
                continue
            index_status = line[0]
            worktree_status = line[1]
            rest = line[3:].strip()

            old_file = None
            new_file = rest
            if " -> " in rest:
                parts = rest.split(" -> ")
                old_file = parts[0].strip()
                new_file = parts[1].strip()

            # Staged changes (index)
            if index_status != " " and index_status != "?":
                status = "modified"
                if index_status == "A":
                    status = "added"
                elif index_status == "D":
                    status = "deleted"
                elif index_status == "R":
                    status = "renamed"
                results.append((new_file, status, True, old_file))

            # Unstaged changes (worktree)
            if worktree_status != " " and worktree_status != "?":
                status = "modified"
                if worktree_status == "D":
                    status = "deleted"
                results.append((new_file, status, False, None))

            # Untracked files
            if index_status == "?" and worktree_status == "?":
                results.append((new_file, "untracked", False, None))

        return results

    def get_file_content_at_head(self, rel_path: str) -> str:
        """Get file content from git HEAD."""
        code, stdout, _ = self._run_git(["show", f"HEAD:{rel_path}"])
        if code == 0:
            return stdout
        return ""

    def get_file_content_on_disk(self, rel_path: str) -> str:
        """Get current file content on disk with path traversal guard."""
        # Validate path
        norm = os.path.normpath(rel_path)
        if norm.startswith("..") or os.path.isabs(norm):
            return ""

        full_path = os.path.join(self.repo_root, norm)
        if not full_path.startswith(self.repo_root + os.sep) and full_path != self.repo_root:
            return ""

        if not os.path.isfile(full_path):
            return ""

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return ""

    def analyze_changes(
        self,
        target_subpath: Optional[str] = None,
        build_dependency_map: bool = True,
    ) -> ChangeAnalysisResult:
        """Perform comprehensive deterministic change analysis."""
        if not self.is_git_repository():
            return ChangeAnalysisResult(
                is_git_repo=False,
                has_changes=False,
                summary="The workspace is not an initialized Git repository.",
                error="Directory is not a git repository.",
            )

        status_items = self.get_git_status_files()

        # Filter by subpath if specified
        if target_subpath:
            norm_sub = os.path.normpath(target_subpath).replace("\\", "/")
            status_items = [
                item for item in status_items
                if os.path.normpath(item[0]).replace("\\", "/").startswith(norm_sub)
            ]

        if not status_items:
            return ChangeAnalysisResult(
                is_git_repo=True,
                has_changes=False,
                summary="Working tree is clean. No uncommitted, staged, or untracked changes detected.",
            )

        staged_changes: List[FileChange] = []
        unstaged_changes: List[FileChange] = []
        untracked_files: List[str] = []
        impacted_modules: Set[str] = set()

        for path_str, status, is_staged, old_path in status_items:
            if status == "untracked":
                untracked_files.append(path_str)
                continue

            # Get diff snippet
            diff_args = ["diff"]
            if is_staged:
                diff_args.append("--cached")
            diff_args.extend(["--", path_str])
            _, diff_out, _ = self._run_git(diff_args)

            # AST comparison for Python files
            ast_diff = None
            if path_str.endswith(".py"):
                if status == "added":
                    new_code = self.get_file_content_on_disk(path_str)
                    ast_diff = compare_code_ast("", new_code)
                elif status == "deleted":
                    old_code = self.get_file_content_at_head(path_str)
                    ast_diff = compare_code_ast(old_code, "")
                elif status == "renamed" and old_path:
                    old_code = self.get_file_content_at_head(old_path)
                    new_code = self.get_file_content_on_disk(path_str)
                    ast_diff = compare_code_ast(old_code, new_code)
                else:  # modified
                    old_code = self.get_file_content_at_head(path_str)
                    new_code = self.get_file_content_on_disk(path_str)
                    ast_diff = compare_code_ast(old_code, new_code)

                # Record module name
                stem = Path(path_str).stem
                impacted_modules.add(stem)

            change = FileChange(
                path=path_str,
                status=status,
                is_staged=is_staged,
                old_path=old_path,
                diff_content=diff_out[:2000] if diff_out else "",
                ast_diff=ast_diff,
            )

            if is_staged:
                staged_changes.append(change)
            else:
                unstaged_changes.append(change)

        # Trace downstream dependencies using AST across target codebase
        downstream: Dict[str, List[str]] = {}
        if build_dependency_map and impacted_modules:
            downstream = self._find_downstream_dependents(impacted_modules)

        # Recommend tests
        recommended_tests = self._recommend_tests(impacted_modules, downstream)

        # Formulate confidence ratings
        confidence_ratings = {
            "git_file_status": "Confirmed (Direct Git status)",
            "ast_structural_changes": "Confirmed (Direct AST analysis)",
            "downstream_impact": "Likely (Inferred from import statements; verify runtime execution paths)",
            "test_recommendations": "Likely (Mapped from affected module names and test filenames)",
        }

        # Generate summary text
        summary = self._format_summary(
            staged_changes,
            unstaged_changes,
            untracked_files,
            downstream,
            recommended_tests,
        )

        return ChangeAnalysisResult(
            is_git_repo=True,
            has_changes=True,
            staged_changes=staged_changes,
            unstaged_changes=unstaged_changes,
            untracked_files=untracked_files,
            impacted_modules=sorted(list(impacted_modules)),
            downstream_dependents=downstream,
            recommended_tests=recommended_tests,
            confidence_ratings=confidence_ratings,
            summary=summary,
        )

    def _find_downstream_dependents(self, changed_modules: Set[str]) -> Dict[str, List[str]]:
        """Search all python files in repo to find who imports changed_modules."""
        dependents: Dict[str, Set[str]] = {m: set() for m in changed_modules}

        for root, dirs, files in os.walk(self.repo_root):
            # Skip hidden / build dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("build", "dist", "node_modules", "venv", "__pycache__")]
            for f in files:
                if not f.endswith(".py"):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, self.repo_root)
                file_stem = Path(f).stem
                if file_stem in changed_modules:
                    continue  # skip self

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                        tree = ast.parse(fp.read())
                    for node in ast.walk(tree):
                        imported = None
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imported = alias.name.split(".")[0]
                                if imported in dependents:
                                    dependents[imported].add(rel_path)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imported = node.module.split(".")[0]
                                if imported in dependents:
                                    dependents[imported].add(rel_path)
                except Exception:
                    continue

        return {k: sorted(list(v)) for k, v in dependents.items() if v}

    def _recommend_tests(
        self,
        changed_modules: Set[str],
        downstream: Dict[str, List[str]],
    ) -> List[str]:
        """Find relevant pytest files matching changed or downstream modules."""
        all_affected = set(changed_modules)
        for deps in downstream.values():
            for d in deps:
                all_affected.add(Path(d).stem)

        test_files: Set[str] = set()
        tests_dir = os.path.join(self.repo_root, "tests")
        if os.path.isdir(tests_dir):
            for root, _, files in os.walk(tests_dir):
                for f in files:
                    if f.startswith("test_") and f.endswith(".py"):
                        rel_test = os.path.relpath(os.path.join(root, f), self.repo_root)
                        for aff in all_affected:
                            if aff in f or f"test_{aff}" in f:
                                test_files.add(f"pytest {rel_test} -v")

        # Also check backend/tests if it exists
        backend_tests_dir = os.path.join(self.repo_root, "backend", "tests")
        if os.path.isdir(backend_tests_dir):
            for root, _, files in os.walk(backend_tests_dir):
                for f in files:
                    if f.startswith("test_") and f.endswith(".py"):
                        rel_test = os.path.relpath(os.path.join(root, f), self.repo_root)
                        for aff in all_affected:
                            if aff in f:
                                test_files.add(f"pytest {rel_test} -v")

        if not test_files:
            test_files.add("pytest -v")

        return sorted(list(test_files))

    def _format_summary(
        self,
        staged: List[FileChange],
        unstaged: List[FileChange],
        untracked: List[str],
        downstream: Dict[str, List[str]],
        tests: List[str],
    ) -> str:
        """Format an evidence-based change analysis report in markdown."""
        lines = ["### Code Change Analysis Report", ""]

        if staged:
            lines.append("#### Staged Changes [Confirmed]")
            for c in staged:
                extra = f" (from {c.old_path})" if c.old_path else ""
                lines.append(f"- **{c.status.upper()}**: `{c.path}`{extra}")
                if c.ast_diff:
                    d = c.ast_diff
                    if d.syntax_error:
                        lines.append(f"  - ⚠️ *{d.syntax_error}*")
                    if d.added_functions:
                        lines.append(f"  - Added functions: {', '.join(d.added_functions)}")
                    if d.modified_functions:
                        lines.append(f"  - Modified functions: {', '.join(d.modified_functions)}")
                    if d.removed_functions:
                        lines.append(f"  - Removed functions: {', '.join(d.removed_functions)}")
                    if d.added_classes:
                        lines.append(f"  - Added classes: {', '.join(d.added_classes)}")
                    if d.added_imports:
                        lines.append(f"  - Added imports: {', '.join(d.added_imports)}")
            lines.append("")

        if unstaged:
            lines.append("#### Unstaged Changes [Confirmed]")
            for c in unstaged:
                lines.append(f"- **{c.status.upper()}**: `{c.path}`")
                if c.ast_diff:
                    d = c.ast_diff
                    if d.syntax_error:
                        lines.append(f"  - ⚠️ *{d.syntax_error}*")
                    if d.added_functions:
                        lines.append(f"  - Added functions: {', '.join(d.added_functions)}")
                    if d.modified_functions:
                        lines.append(f"  - Modified functions: {', '.join(d.modified_functions)}")
                    if d.removed_functions:
                        lines.append(f"  - Removed functions: {', '.join(d.removed_functions)}")
                    if d.added_classes:
                        lines.append(f"  - Added classes: {', '.join(d.added_classes)}")
            lines.append("")

        if untracked:
            lines.append("#### Untracked Files [Confirmed]")
            for u in untracked:
                lines.append(f"- `{u}`")
            lines.append("")

        if downstream:
            lines.append("#### Downstream Impact [Likely]")
            for mod, callers in downstream.items():
                lines.append(f"- Changes to `{mod}` affect:")
                for caller in callers:
                    lines.append(f"  - `{caller}`")
            lines.append("")

        if tests:
            lines.append("#### Recommended Validation Commands [Likely]")
            for t in tests:
                lines.append(f"- `{t}`")
            lines.append("")

        return "\n".join(lines)
