"""AgentState schema — the memory payload passed between LangGraph nodes."""

from __future__ import annotations

import operator
from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Shared state flowing through every node in the graph.

    Attributes:
        messages: Conversational history (append-only via ``operator.add``).
        next_node: Routing directive set by the Supervisor
                   (e.g. ``"verse_finder"``, ``"image_gen"``, ``"output_assembler"``, ``"end"``).
        denomination: User's declared denomination context
                      (``"catholic"``, ``"protestant"``, ``"orthodox"``, ``"general"``).
        is_controversial: Whether the topic requires multi-perspective formatting.
        image_url: Payload URL / base64 data-URI from the Image Gen agent.
        retrieved_verses: Exact text payloads retrieved from API.Bible.
        retry_count: Guards against infinite output-assembler reflection loops (cap = 2).
    """

    messages: Annotated[List[BaseMessage], operator.add]
    next_node: str
    denomination: str
    is_controversial: bool
    image_url: str
    retrieved_verses: List[dict]
    retry_count: int
