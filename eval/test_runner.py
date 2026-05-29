"""Automated test runner for the Christianity AI Assistant.

Iterates through eval_dataset.json and asserts expected system behaviour
for each of the 10 tricky test scenarios.

Usage:
    python eval/test_runner.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.graph import build_graph
from agent.tools import init_chromadb

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("eval")


def load_dataset() -> list[dict]:
    """Load the eval dataset from JSON."""
    dataset_path = Path(__file__).parent / "eval_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_single_test(
    graph,
    test_case: dict,
    session_prefix: str = "eval",
) -> dict:
    """Run a single test case and return results."""
    test_id = test_case["id"]
    category = test_case["category"]
    query = test_case["query"]

    logger.info("═══ TEST %d: %s ═══", test_id, category)
    logger.info("Query: %s", query)

    session_id = f"{session_prefix}-{test_id}"

    initial_state = {
        "messages": [HumanMessage(content=query)],
        "next_node": "",
        "denomination": "general",
        "is_controversial": False,
        "image_url": "",
        "retrieved_verses": [],
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": session_id}}

    try:
        result = await graph.ainvoke(initial_state, config=config)

        # Extract AI response
        ai_messages = [
            m for m in result.get("messages", [])
            if hasattr(m, "type") and m.type == "ai"
        ]
        response = ai_messages[-1].content if ai_messages else ""
        image_url = result.get("image_url", "")
        has_verses = bool(result.get("retrieved_verses", []))

        # Run follow-up if present (multi-turn test)
        followup_response = ""
        if test_case.get("followup_query"):
            followup_state = {
                "messages": [HumanMessage(content=test_case["followup_query"])],
                "next_node": "",
                "denomination": result.get("denomination", "general"),
                "is_controversial": False,
                "image_url": "",
                "retrieved_verses": [],
                "retry_count": 0,
            }
            followup_result = await graph.ainvoke(followup_state, config=config)
            followup_ai = [
                m for m in followup_result.get("messages", [])
                if hasattr(m, "type") and m.type == "ai"
            ]
            followup_response = followup_ai[-1].content if followup_ai else ""
            response = followup_response  # Use followup for assertions

        # ── Assertions ──
        passed = True
        failures = []

        # Check assert_contains
        for term in test_case.get("assert_contains", []):
            if term.lower() not in response.lower():
                passed = False
                failures.append(f"Expected response to contain '{term}'")

        # Check assert_not_contains
        for term in test_case.get("assert_not_contains", []):
            if term.lower() in response.lower():
                passed = False
                failures.append(f"Response should NOT contain '{term}'")

        # Check image expectation
        if test_case.get("should_have_image"):
            if not image_url:
                passed = False
                failures.append("Expected image_url but none returned")

        # Check rejection expectation
        if test_case.get("should_be_rejected"):
            rejection_indicators = ["unable", "cannot", "won't", "can't", "sorry"]
            if not any(ind in response.lower() for ind in rejection_indicators):
                passed = False
                failures.append("Expected adversarial rejection but got normal response")

        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info("%s — Test %d (%s)", status, test_id, category)
        if failures:
            for f in failures:
                logger.warning("  ↳ %s", f)

        logger.info("Response preview: %s", response[:200])
        if image_url:
            logger.info("Image URL: present (%d chars)", len(image_url))

        return {
            "id": test_id,
            "category": category,
            "passed": passed,
            "failures": failures,
            "response_preview": response[:300],
            "has_image": bool(image_url),
            "has_verses": has_verses,
        }

    except Exception as exc:
        logger.exception("Test %d failed with exception", test_id)
        return {
            "id": test_id,
            "category": category,
            "passed": False,
            "failures": [f"Exception: {str(exc)}"],
            "response_preview": "",
            "has_image": False,
            "has_verses": False,
        }


async def main():
    """Run all tests."""
    dataset = load_dataset()
    logger.info("Loaded %d test cases", len(dataset))

    # Initialise infrastructure
    collection = init_chromadb()
    graph_builder = build_graph(chromadb_collection=collection)

    db_path = str(Path(__file__).parent.parent / "eval_checkpoints.db")
    saver = AsyncSqliteSaver.from_conn_string(db_path)
    await saver.asetup()

    graph = graph_builder.compile(checkpointer=saver)

    # Run all tests
    results = []
    for tc in dataset:
        result = await run_single_test(graph, tc)
        results.append(result)
        print()  # Visual separator

    # ── Summary ──
    print("\n" + "═" * 60)
    print("EVALUATION SUMMARY")
    print("═" * 60)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    for r in results:
        status = "✅" if r["passed"] else "❌"
        print(f"  {status} Test {r['id']:2d} ({r['category']:20s})")
        if r["failures"]:
            for f in r["failures"]:
                print(f"       ↳ {f}")

    print(f"\nResults: {passed}/{total} passed, {failed} failed")
    print("═" * 60)

    # Clean up
    try:
        os.unlink(db_path)
    except OSError:
        pass

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
