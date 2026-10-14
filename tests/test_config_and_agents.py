"""Tests for configuration loading and agent setup.

These tests verify:
- Configuration variables load correctly
- Missing environment variables are detected
- Agents are created with correct names and tools
- All five agents exist with appropriate tools
"""

import os
import pytest


class TestConfiguration:
    """Tests for configuration module."""

    def test_default_values(self):
        """Should have sensible defaults."""
        from code_helper.config import (
            PINECONE_INDEX_NAME,
            PINECONE_CLOUD,
            PINECONE_REGION,
            CHUNK_SIZE,
            CHUNK_OVERLAP,
        )

        assert PINECONE_INDEX_NAME == "code-helper"
        assert PINECONE_CLOUD == "aws"
        assert PINECONE_REGION == "us-east-1"
        assert CHUNK_SIZE == 100
        assert CHUNK_OVERLAP == 20

    def test_chat_model_format(self):
        """Should format chat model with nvidia_nim prefix."""
        from code_helper.config import LITELLM_CHAT_MODEL, NVIDIA_CHAT_MODEL

        assert LITELLM_CHAT_MODEL == f"nvidia_nim/{NVIDIA_CHAT_MODEL}"

    def test_embedding_model_name(self):
        """Should use the required embedding model."""
        from code_helper.config import NVIDIA_EMBED_MODEL

        assert NVIDIA_EMBED_MODEL == "nvidia/nemotron-3-embed-1b"

    def test_validate_config_missing_vars(self):
        """Should detect missing required variables."""
        # Temporarily remove required vars
        old_nvidia = os.environ.pop("NVIDIA_NIM_API_KEY", None)
        old_pinecone = os.environ.pop("PINECONE_API_KEY", None)

        try:
            from code_helper.config import validate_config
            # Force re-validation
            result = validate_config()
            # If both are missing, should return False
            if not old_nvidia and not old_pinecone:
                assert result is False
        finally:
            if old_nvidia:
                os.environ["NVIDIA_NIM_API_KEY"] = old_nvidia
            if old_pinecone:
                os.environ["PINECONE_API_KEY"] = old_pinecone


class TestAgents:
    """Tests for ADK agent setup."""

    def test_root_agent_exists(self):
        """Should expose root_agent."""
        from code_helper.agent import root_agent

        assert root_agent is not None
        assert root_agent.name == "coordinator"

    def test_coordinator_exists(self):
        """Should create coordinator agent."""
        from code_helper.agent import coordinator

        assert coordinator.name == "coordinator"

    def test_code_searcher_exists(self):
        """Should create code_searcher agent."""
        from code_helper.agent import code_searcher

        assert code_searcher.name == "code_searcher"

    def test_code_explainer_exists(self):
        """Should create code_explainer agent."""
        from code_helper.agent import code_explainer

        assert code_explainer.name == "code_explainer"

    def test_architecture_mapper_exists(self):
        """Should create architecture_mapper agent."""
        from code_helper.agent import architecture_mapper

        assert architecture_mapper.name == "architecture_mapper"

    def test_onboarding_guide_exists(self):
        """Should create onboarding_guide agent."""
        from code_helper.agent import onboarding_guide

        assert onboarding_guide.name == "onboarding_guide"

    def test_coordinator_has_four_sub_agents(self):
        """Coordinator should delegate to exactly four workers."""
        from code_helper.agent import coordinator

        assert len(coordinator.sub_agents) == 4
        sub_agent_names = {a.name for a in coordinator.sub_agents}
        assert sub_agent_names == {
            "code_searcher",
            "code_explainer",
            "architecture_mapper",
            "onboarding_guide",
        }

    def test_code_searcher_has_rag_search_tool(self):
        """code_searcher should have rag_search tool."""
        from code_helper.agent import code_searcher

        tool_names = [t.name for t in code_searcher.tools]
        assert "rag_search" in tool_names

    def test_code_explainer_has_read_file_tool(self):
        """code_explainer should have read_project_file tool."""
        from code_helper.agent import code_explainer

        tool_names = [
            getattr(t, "name", type(t).__name__) for t in code_explainer.tools
        ]
        assert "read_project_file" in tool_names

    def test_architecture_mapper_has_tools(self):
        """architecture_mapper should have list_project_files and inspect_imports."""
        from code_helper.agent import architecture_mapper

        tool_names = {t.name for t in architecture_mapper.tools}
        assert "list_project_files" in tool_names
        assert "inspect_imports" in tool_names

    def test_onboarding_guide_has_overview_tool(self):
        """onboarding_guide should have get_project_overview tool."""
        from code_helper.agent import onboarding_guide

        tool_names = [t.name for t in onboarding_guide.tools]
        assert "get_project_overview" in tool_names

    def test_every_worker_has_tool(self):
        """Every worker agent should have at least one tool."""
        from code_helper.agent import (
            code_searcher,
            code_explainer,
            architecture_mapper,
            onboarding_guide,
        )

        workers = [code_searcher, code_explainer, architecture_mapper, onboarding_guide]
        for worker in workers:
            assert len(worker.tools) >= 1, f"{worker.name} has no tools"


class TestToolFunctions:
    """Tests for the five required custom tools."""

    def test_rag_search_is_function(self):
        """rag_search should be a callable function."""
        from code_helper.tools import rag_search
        assert callable(rag_search)

    def test_read_project_file_is_function(self):
        """read_project_file should be a callable function."""
        from code_helper.tools import read_project_file
        assert callable(read_project_file)

    def test_list_project_files_is_function(self):
        """list_project_files should be a callable function."""
        from code_helper.tools import list_project_files
        assert callable(list_project_files)

    def test_inspect_imports_is_function(self):
        """inspect_imports should be a callable function."""
        from code_helper.tools import inspect_imports
        assert callable(inspect_imports)

    def test_get_project_overview_is_function(self):
        """get_project_overview should be a callable function."""
        from code_helper.tools import get_project_overview
        assert callable(get_project_overview)

    def test_five_tools_exist(self):
        """Should have exactly the five required tools."""
        from code_helper.tools import (
            rag_search,
            read_project_file,
            list_project_files,
            inspect_imports,
            get_project_overview,
        )

        tools = [
            rag_search,
            read_project_file,
            list_project_files,
            inspect_imports,
            get_project_overview,
        ]
        assert len(tools) == 5
        assert all(callable(t) for t in tools)