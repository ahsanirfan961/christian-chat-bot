"""LangGraph StateGraph definition — wires the four agent nodes together.

Graph topology:
    START → supervisor
    supervisor → verse_finder | image_gen | END (adversarial)
    verse_finder → output_assembler
    image_gen → END
    output_assembler → END | output_assembler (retry)
"""

from __future__ import annotations

import functools
import logging
from typing import Any

from langgraph.graph import END, StateGraph

from agent.nodes import (
    image_gen_node,
    output_assembler_node,
    supervisor_node,
    verse_finder_node,
)
from agent.state import AgentState

logger = logging.getLogger(__name__)


def _supervisor_router(state: AgentState) -> str:
    """Read ``next_node`` set by the Supervisor and route accordingly."""
    next_node = state.get("next_node", "end")
    logger.info("Router: supervisor → %s", next_node)
    if next_node == "verse_finder":
        return "verse_finder"
    elif next_node == "image_gen":
        return "image_gen"
    else:
        return "end"


def _assembler_router(state: AgentState) -> str:
    """Route output assembler: retry or finish."""
    next_node = state.get("next_node", "end")
    if next_node == "retry_assembler":
        logger.info("Router: output_assembler → RETRY")
        return "retry"
    logger.info("Router: output_assembler → END")
    return "end"


def build_graph(*, chromadb_collection: Any = None) -> StateGraph:
    """Construct and return the (uncompiled) LangGraph StateGraph.

    Parameters
    ----------
    chromadb_collection:
        A live ChromaDB ``Collection`` instance for the Verse Finder's
        semantic topic search.  Injected here so the graph owns no global state.
    """

    # Bind the chromadb_collection into the verse_finder_node via functools.partial
    bound_verse_finder = functools.partial(
        verse_finder_node, chromadb_collection=chromadb_collection
    )

    graph = StateGraph(AgentState)

    # ── Add nodes ──
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("verse_finder", bound_verse_finder)
    graph.add_node("image_gen", image_gen_node)
    graph.add_node("output_assembler", output_assembler_node)

    # ── Entry point ──
    graph.set_entry_point("supervisor")

    # ── Supervisor → conditional routing ──
    graph.add_conditional_edges(
        "supervisor",
        _supervisor_router,
        {
            "verse_finder": "verse_finder",
            "image_gen": "image_gen",
            "end": END,
        },
    )

    # ── verse_finder → output_assembler ──
    graph.add_edge("verse_finder", "output_assembler")

    # ── image_gen → END (image response is self-contained) ──
    graph.add_edge("image_gen", END)

    # ── output_assembler → conditional (retry or end) ──
    graph.add_conditional_edges(
        "output_assembler",
        _assembler_router,
        {
            "retry": "output_assembler",
            "end": END,
        },
    )

    return graph
