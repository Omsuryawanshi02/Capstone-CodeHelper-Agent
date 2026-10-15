"""Phase 3 — Test Agent Routing.

Verifies that Google ADK correctly routes questions from the root Coordinator
to the designated specialist:
- Code-location questions reach Code Searcher.
- Whole-file explanation questions reach Code Explainer.
- Import and dependency questions reach Architecture Mapper.
- Setup and onboarding questions reach Onboarding Guide.
"""

import asyncio
import pytest
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from code_helper.agent import root_agent


ROUTING_CASES = [
    {
        "category": "code_location",
        "question": "Where is the chunk_code function implemented?",
        "expected_worker": "code_searcher",
    },
    {
        "category": "file_explanation",
        "question": "Explain what target_project/main.py does and its functions.",
        "expected_worker": "code_explainer",
    },
    {
        "category": "file_explanation",
        "question": "What is the purpose of indexer.py?",
        "expected_worker": "code_explainer",
    },
    {
        "category": "architecture_imports",
        "question": "Which files import config.py and how are modules connected?",
        "expected_worker": "architecture_mapper",
    },
    {
        "category": "setup_onboarding",
        "question": "How do I get started with this project and run onboarding?",
        "expected_worker": "onboarding_guide",
    },
]


async def run_routing_check(case):
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="code_helper", user_id="test_user")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="code_helper")

    content = types.Content(role="user", parts=[types.Part.from_text(text=case["question"])])
    authors = []
    # Collect authors in execution sequence until a specialist is reached
    async for event in runner.run_async(session_id=session.id, user_id="test_user", new_message=content):
        if event.author and event.author not in authors:
            authors.append(event.author)
            print(f"[{case['category']}] Detected active author: {event.author}", flush=True)
            if event.author != "coordinator":
                break

    return {
        "category": case["category"],
        "question": case["question"],
        "expected_worker": case["expected_worker"],
        "author_trace": authors,
        "matched": case["expected_worker"] in authors,
    }



def test_routing_benchmark():
    async def run_all():
        results = []
        for case in ROUTING_CASES:
            res = await run_routing_check(case)
            results.append(res)
            print(f"\nCategory: {res['category']}")
            print(f"Question: {res['question']}")
            print(f"Expected: {res['expected_worker']}")
            print(f"Trace:    {res['author_trace']}")
            print(f"Passed:   {res['matched']}")
            assert res["matched"], f"Expected {res['expected_worker']} in trace {res['author_trace']}"
        return results

    asyncio.run(run_all())


if __name__ == "__main__":
    async def main():
        print("=== Running Agent Routing Evaluation ===")
        for case in ROUTING_CASES:
            res = await run_routing_check(case)
            print(f"Q: {case['question'][:45]}... -> Trace: {res['author_trace']} | OK: {res['matched']}")

    asyncio.run(main())
