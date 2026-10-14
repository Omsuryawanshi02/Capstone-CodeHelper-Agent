"""Tests for CodeChangeAnalyzer.

Tests:
- AST import extraction and comparison
- Added, modified, deleted, and renamed files
- Modified functions and classes (signatures, methods)
- Staged versus unstaged changes
- Syntax errors in baseline and modified code
- Empty diffs
- Path restrictions
- Downstream module impact mapping
- Recommended test generation
"""

import os
import shutil
import subprocess
import tempfile
import pytest

from code_helper.tools.code_change_analyzer import (
    CodeChangeAnalyzer,
    compare_code_ast,
    extract_ast_items,
    AstDifference,
)


def _exec_git(args, cwd, extra_env=None):
    """Safely execute git with redirected stdio to prevent Windows handle duplication errors."""
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Tester",
        "GIT_AUTHOR_EMAIL": "tester@example.com",
        "GIT_COMMITTER_NAME": "Tester",
        "GIT_COMMITTER_EMAIL": "tester@example.com",
    }
    if extra_env:
        git_env.update(extra_env)
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
        env=git_env,
    )


class TestAstComparison:
    """Unit tests for AST comparison functionality."""

    def test_compare_added_and_removed_functions(self):
        """Should detect newly added and removed functions."""
        old_code = """
def existing_function(x, y):
    return x + y

def deprecated_function():
    pass
"""
        new_code = """
def existing_function(x, y):
    return x + y

def brand_new_function(a, b, c):
    return a * b * c
"""
        diff = compare_code_ast(old_code, new_code)
        assert "brand_new_function" in diff.added_functions
        assert "deprecated_function" in diff.removed_functions
        assert diff.syntax_error is None

    def test_compare_modified_function_signature(self):
        """Should detect modified function parameters."""
        old_code = "def process(item):\n    pass"
        new_code = "def process(item, dry_run=False):\n    pass"

        diff = compare_code_ast(old_code, new_code)
        assert len(diff.modified_functions) == 1
        assert "process" in diff.modified_functions[0]
        assert "dry_run" in diff.modified_functions[0]

    def test_compare_added_and_removed_classes(self):
        """Should detect class additions and deletions."""
        old_code = "class OldService:\n    pass"
        new_code = "class NewService:\n    def run(self):\n        pass"

        diff = compare_code_ast(old_code, new_code)
        assert "NewService" in diff.added_classes
        assert "OldService" in diff.removed_classes

    def test_compare_imports(self):
        """Should detect import additions and removals."""
        old_code = "import os\nfrom math import sqrt"
        new_code = "import sys\nimport os\nfrom math import ceil"

        diff = compare_code_ast(old_code, new_code)
        assert "sys" in diff.added_imports
        assert "math.ceil" in diff.added_imports
        assert "math.sqrt" in diff.removed_imports

    def test_syntax_error_reported(self):
        """Should detect and report syntax errors in modified code."""
        old_code = "def foo():\n    return 42"
        bad_code = "def foo(\n    syntax error here"

        diff = compare_code_ast(old_code, bad_code)
        assert diff.syntax_error is not None
        assert "Syntax error in modified code" in diff.syntax_error


class TestGitChangeAnalysis:
    """Integration tests with a real temporary Git repository."""

    @pytest.fixture
    def git_repo(self):
        """Create a temporary git repository for testing."""
        temp_dir = tempfile.mkdtemp(prefix="test_git_repo_")
        orig_cwd = os.getcwd()
        try:
            # Initialize git repo with explicit identity and captured stdio
            _exec_git(["init"], temp_dir)
            _exec_git(["config", "user.email", "tester@example.com"], temp_dir)
            _exec_git(["config", "user.name", "Tester"], temp_dir)

            # Create initial file and commit
            initial_file = os.path.join(temp_dir, "module_a.py")
            with open(initial_file, "w") as f:
                f.write("def helper():\n    return 1\n")

            # Create test directory
            tests_dir = os.path.join(temp_dir, "tests")
            os.makedirs(tests_dir, exist_ok=True)
            test_file = os.path.join(tests_dir, "test_module_a.py")
            with open(test_file, "w") as f:
                f.write("import module_a\ndef test_helper():\n    assert module_a.helper() == 1\n")

            _exec_git(["add", "."], temp_dir)
            _exec_git(["commit", "-m", "Initial commit"], temp_dir)

            yield temp_dir
        finally:
            os.chdir(orig_cwd)
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_empty_diff_clean_working_tree(self, git_repo):
        """When tree is clean, returns has_changes=False."""
        analyzer = CodeChangeAnalyzer(repo_root=git_repo)
        result = analyzer.analyze_changes()

        assert result.is_git_repo is True
        assert result.has_changes is False
        assert "clean" in result.summary.lower()

    def test_unstaged_modification(self, git_repo):
        """Should detect unstaged modification to an existing file."""
        file_path = os.path.join(git_repo, "module_a.py")
        with open(file_path, "w") as f:
            f.write("def helper():\n    return 2\ndef new_func():\n    return 3\n")

        analyzer = CodeChangeAnalyzer(repo_root=git_repo)
        result = analyzer.analyze_changes()

        assert result.has_changes is True
        assert len(result.unstaged_changes) == 1
        change = result.unstaged_changes[0]
        assert change.path == "module_a.py"
        assert change.status == "modified"
        assert not change.is_staged
        assert change.ast_diff is not None
        assert "new_func" in change.ast_diff.added_functions

    def test_staged_vs_unstaged_distinction(self, git_repo):
        """Should distinguish between staged changes and unstaged changes."""
        # Modify module_a and stage it
        file_a = os.path.join(git_repo, "module_a.py")
        with open(file_a, "w") as f:
            f.write("def helper():\n    return 10\n")
        _exec_git(["add", "module_a.py"], git_repo)

        # Create new unstaged file module_b.py
        file_b = os.path.join(git_repo, "module_b.py")
        with open(file_b, "w") as f:
            f.write("def service():\n    return 20\n")

        analyzer = CodeChangeAnalyzer(repo_root=git_repo)
        result = analyzer.analyze_changes()

        assert result.has_changes is True
        # module_a is staged
        assert len(result.staged_changes) == 1
        assert result.staged_changes[0].path == "module_a.py"
        assert result.staged_changes[0].is_staged is True

        # module_b is untracked
        assert "module_b.py" in result.untracked_files

    def test_deleted_file(self, git_repo):
        """Should detect deleted files."""
        file_a = os.path.join(git_repo, "module_a.py")
        os.remove(file_a)

        analyzer = CodeChangeAnalyzer(repo_root=git_repo)
        result = analyzer.analyze_changes()

        assert result.has_changes is True
        assert any(c.path == "module_a.py" and c.status == "deleted" for c in result.unstaged_changes)

    def test_renamed_file_detection(self, git_repo):
        """Should detect file renames when staged in git."""
        _exec_git(["mv", "module_a.py", "module_renamed.py"], git_repo)

        analyzer = CodeChangeAnalyzer(repo_root=git_repo)
        result = analyzer.analyze_changes()

        assert result.has_changes is True
        assert len(result.staged_changes) == 1
        change = result.staged_changes[0]
        assert change.status == "renamed"
        assert change.path == "module_renamed.py"
        assert change.old_path == "module_a.py"

    def test_path_restriction_guard(self, git_repo):
        """Path traversal should be rejected when reading file content."""
        analyzer = CodeChangeAnalyzer(repo_root=git_repo)
        # Attempt traversal
        content = analyzer.get_file_content_on_disk("../../some_secret.txt")
        assert content == ""

    def test_downstream_impact_and_test_recommendations(self, git_repo):
        """Should detect that test_module_a.py depends on module_a and recommend it."""
        # Modify module_a
        file_a = os.path.join(git_repo, "module_a.py")
        with open(file_a, "w") as f:
            f.write("def helper():\n    return 99\n")

        analyzer = CodeChangeAnalyzer(repo_root=git_repo)
        result = analyzer.analyze_changes()

        assert "module_a" in result.impacted_modules
        assert any("test_module_a.py" in t for t in result.recommended_tests)
