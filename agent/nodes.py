"""Agent node functions — the four core processing units of the graph.

Each function takes the current ``AgentState`` and returns a partial state
update dict.  The Supervisor orchestrates routing; the others are specialists.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Literal, Optional, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from agent.prompts import (
    ADVERSARIAL_REJECTION_MESSAGE,
    IMAGE_SAFETY_PROMPT,
    OUTPUT_ASSEMBLER_PROMPT,
    SUPERVISOR_SYSTEM_PROMPT,
    VERSE_NOT_FOUND_MESSAGE,
)
from agent.state import AgentState
from agent.tools import fetch_passage, parse_verse_reference, search_bible, search_topics
from agent.validators import validate_scripture_quotes

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Shared LLM factory
# ──────────────────────────────────────────────────────────────────────

def _get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """Return a ChatOpenAI instance pointed at OpenRouter / Gemini 2.5 Flash."""
    return ChatOpenAI(
        model="google/gemini-2.5-flash",
        openai_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temperature,
        max_tokens=2048,
    )


# ──────────────────────────────────────────────────────────────────────
# Pydantic schemas for structured output
# ──────────────────────────────────────────────────────────────────────

class SupervisorDecision(BaseModel):
    """The Supervisor's routing decision."""

    intent: Literal["qa", "image", "adversarial", "web_search"] = Field(
        description="Classified intent of the user message"
    )
    denomination: str = Field(
        default="general",
        description="User's denomination context: catholic, protestant, orthodox, or general",
    )
    is_controversial: bool = Field(
        default=False,
        description="Whether the topic is debated across denominations",
    )
    search_keywords: Optional[List[str]] = Field(
        default=None,
        description="2-3 search keywords for abstract concept queries",
    )
    verse_reference: Optional[str] = Field(
        default=None,
        description="Explicit verse reference like 'John 3:16'",
    )


# ══════════════════════════════════════════════════════════════════════
# NODE 1 — Supervisor (Intent Router + Input Guardrail)
# ══════════════════════════════════════════════════════════════════════

async def supervisor_node(state: AgentState) -> dict:
    """Classify intent, extract metadata, and set ``next_node``."""
    logger.info("━━━ SUPERVISOR NODE ━━━")

    llm = _get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(SupervisorDecision)

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        *state["messages"],
    ]

    try:
        decision: SupervisorDecision = await structured_llm.ainvoke(messages)
    except Exception as exc:
        logger.error("Supervisor structured output failed: %s", exc)
        # Fallback to qa intent
        decision = SupervisorDecision(intent="qa", denomination="general")

    logger.info(
        "Supervisor decision: intent=%s, denomination=%s, controversial=%s",
        decision.intent,
        decision.denomination,
        decision.is_controversial,
    )

    # ── Route based on intent ──
    if decision.intent == "adversarial":
        logger.info("⛔ Adversarial input detected — rejecting.")
        return {
            "next_node": "end",
            "denomination": decision.denomination,
            "is_controversial": False,
            "messages": [AIMessage(content=ADVERSARIAL_REJECTION_MESSAGE)],
            "retrieved_verses": [],
            "image_url": "",
        }

    if decision.intent == "image":
        logger.info("🎨 Routing to Image Gen Agent")
        return {
            "next_node": "image_gen",
            "denomination": decision.denomination,
            "is_controversial": False,
            "retrieved_verses": [],
            "image_url": "",
        }

    if decision.intent == "web_search":
        logger.info("🌐 Routing to Web Search Agent")
        search_params = {
            "verse_reference": decision.verse_reference,
            "search_keywords": decision.search_keywords,
        }
        return {
            "next_node": "web_search",
            "denomination": decision.denomination,
            "is_controversial": decision.is_controversial,
            "retrieved_verses": [],
            "web_context": [],
            "image_url": "",
            "messages": [
                SystemMessage(
                    content=f"[SEARCH_PARAMS]{json.dumps(search_params)}[/SEARCH_PARAMS]"
                )
            ],
        }

    # intent == "qa"
    logger.info("📖 Routing to Verse Finder Agent")

    # Pack the search parameters into state for the Verse Finder
    # We pass them as a JSON blob in a system message so the verse_finder can read them
    search_params = {
        "verse_reference": decision.verse_reference,
        "search_keywords": decision.search_keywords,
    }
    return {
        "next_node": "verse_finder",
        "denomination": decision.denomination,
        "is_controversial": decision.is_controversial,
        "retrieved_verses": [],
        "image_url": "",
        "messages": [
            SystemMessage(
                content=f"[SEARCH_PARAMS]{json.dumps(search_params)}[/SEARCH_PARAMS]"
            )
        ],
    }


# ══════════════════════════════════════════════════════════════════════
# NODE 2 — Verse Finder (Deterministic Retrieval)
# ══════════════════════════════════════════════════════════════════════

async def verse_finder_node(state: AgentState, *, chromadb_collection=None) -> dict:
    """Retrieve exact verse text via API.Bible — NO LLM generation here."""
    logger.info("━━━ VERSE FINDER NODE ━━━")

    bible_id = os.getenv("DEFAULT_BIBLE_ID", "de4e12af7f28f599-02")

    # Extract search params from the last system message
    search_params = {"verse_reference": None, "search_keywords": None}
    for msg in reversed(state["messages"]):
        if hasattr(msg, "content") and "[SEARCH_PARAMS]" in msg.content:
            try:
                raw = msg.content.split("[SEARCH_PARAMS]")[1].split("[/SEARCH_PARAMS]")[0]
                search_params = json.loads(raw)
            except (IndexError, json.JSONDecodeError):
                pass
            break

    retrieved: list[dict] = []

    # ── Path A: Explicit verse reference ──
    if search_params.get("verse_reference"):
        ref = search_params["verse_reference"]
        logger.info("Looking up explicit reference: %s", ref)
        passage_id = parse_verse_reference(ref)

        if passage_id is None:
            logger.warning("Could not parse reference '%s' — likely fake book", ref)
            return {
                "next_node": "output_assembler",
                "retrieved_verses": [],
                "messages": [
                    SystemMessage(content=f"[VERSE_STATUS]not_found[/VERSE_STATUS]")
                ],
            }

        result = await fetch_passage(bible_id, passage_id)
        if result and result.get("text"):
            retrieved.append(result)
            logger.info("✅ Found: %s", result["reference"])
        else:
            logger.warning("API.Bible returned no result for %s", passage_id)
            return {
                "next_node": "output_assembler",
                "retrieved_verses": [],
                "messages": [
                    SystemMessage(content=f"[VERSE_STATUS]not_found[/VERSE_STATUS]")
                ],
            }

    # ── Path B: Keyword / topic search ──
    elif search_params.get("search_keywords"):
        keywords = search_params["search_keywords"]
        query = " ".join(keywords)
        logger.info("Searching for keywords: %s", keywords)

        # Step 1: ChromaDB semantic search for relevant verse references
        if chromadb_collection is not None:
            topics = search_topics(chromadb_collection, query, n_results=3)
            logger.info("ChromaDB matched topics: %s", [t["topic"] for t in topics])

            # Collect unique verse IDs from topic matches
            verse_ids: list[str] = []
            for t in topics:
                for vid in t["verses"]:
                    if vid not in verse_ids:
                        verse_ids.append(vid)

            # Step 2: Fetch exact text from API.Bible for top matches
            for vid in verse_ids[:5]:  # cap at 5 API calls
                result = await fetch_passage(bible_id, vid)
                if result and result.get("text"):
                    retrieved.append(result)
                    logger.info("✅ Fetched: %s", result["reference"])

        # Fallback: direct API.Bible keyword search
        if not retrieved:
            logger.info("Falling back to API.Bible keyword search")
            results = await search_bible(bible_id, query)
            retrieved.extend(results)

    # ── Path C: No search params — try keyword search from the user message ──
    else:
        # Extract the last human message for a keyword search
        user_msg = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_msg = msg.content
                break

        if user_msg and chromadb_collection is not None:
            topics = search_topics(chromadb_collection, user_msg, n_results=2)
            verse_ids = []
            for t in topics:
                for vid in t["verses"]:
                    if vid not in verse_ids:
                        verse_ids.append(vid)
            for vid in verse_ids[:4]:
                result = await fetch_passage(bible_id, vid)
                if result and result.get("text"):
                    retrieved.append(result)

        if not retrieved and user_msg:
            results = await search_bible(bible_id, user_msg[:100])
            retrieved.extend(results)

    logger.info("Total verses retrieved: %d", len(retrieved))

    status = "found" if retrieved else "not_found"
    return {
        "next_node": "output_assembler",
        "retrieved_verses": retrieved,
        "messages": [
            SystemMessage(content=f"[VERSE_STATUS]{status}[/VERSE_STATUS]")
        ],
    }


# ══════════════════════════════════════════════════════════════════════
# NODE 3 — Image Generation Agent
# ══════════════════════════════════════════════════════════════════════

async def image_gen_node(state: AgentState) -> dict:
    """Generate a Christian-themed image via OpenRouter's nano-banana model."""
    logger.info("━━━ IMAGE GEN NODE ━━━")

    # Step 1: Sanitise the prompt via Gemini 2.5 Flash
    llm = _get_llm(temperature=0.5)

    # Get the user's original request
    user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_msg = msg.content
            break

    safety_messages = [
        SystemMessage(content=IMAGE_SAFETY_PROMPT),
        HumanMessage(content=f"User's image request: {user_msg}"),
    ]

    try:
        safe_prompt_resp = await llm.ainvoke(safety_messages)
        safe_prompt = safe_prompt_resp.content.strip()
    except Exception as exc:
        logger.error("Image prompt sanitisation failed: %s", exc)
        safe_prompt = (
            "A peaceful Christian scene in stained glass art style, "
            "respectful, reverent, family-friendly"
        )

    logger.info("Sanitised image prompt: %s", safe_prompt)

    # Step 2: Call OpenRouter with nano-banana (Gemini 2.5 Flash Image)
    import httpx

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    image_url = ""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "google/gemini-2.5-flash-preview-image-generation",
                    "messages": [
                        {"role": "user", "content": safe_prompt}
                    ],
                    "modalities": ["image", "text"],
                },
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract image from response
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")

                # Check for multipart content (list of parts)
                if isinstance(content, list):
                    for part in content:
                        if part.get("type") == "image_url":
                            image_url = part.get("image_url", {}).get("url", "")
                            break
                elif isinstance(content, str) and content.startswith("data:image"):
                    image_url = content

            logger.info("Image generated: %s", "✅ success" if image_url else "❌ no image in response")

    except Exception as exc:
        logger.error("Image generation failed: %s", exc)

    # Build response message
    if image_url:
        response_text = f"Here is your Christian-themed image based on your request:\n\n*Prompt used: {safe_prompt}*"
    else:
        response_text = (
            "I apologize, but I was unable to generate the image at this time. "
            "Please try again with a different description."
        )

    return {
        "next_node": "end",
        "image_url": image_url,
        "messages": [AIMessage(content=response_text)],
    }


# ══════════════════════════════════════════════════════════════════════
# NODE 4 — Web Search Agent
# ══════════════════════════════════════════════════════════════════════

async def web_search_node(state: AgentState) -> dict:
    """Search the web for contemporary or historical Christian context using DuckDuckGo."""
    logger.info("━━━ WEB SEARCH NODE ━━━")
    
    # Extract search params
    search_params = {"search_keywords": None}
    for msg in reversed(state["messages"]):
        if hasattr(msg, "content") and "[SEARCH_PARAMS]" in msg.content:
            try:
                raw = msg.content.split("[SEARCH_PARAMS]")[1].split("[/SEARCH_PARAMS]")[0]
                search_params = json.loads(raw)
            except (IndexError, json.JSONDecodeError):
                pass
            break
            
    query = ""
    if search_params.get("search_keywords"):
        query = " ".join(search_params["search_keywords"])
    else:
        # Fallback to user message
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                query = msg.content
                break
                
    if not query:
        query = "Christian theology"
        
    logger.info("Web search query: %s", query)
    
    web_context = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
            for r in results:
                web_context.append(f"[{r.get('title', '')}]({r.get('href', '')}): {r.get('body', '')}")
        logger.info("Web search returned %d results", len(web_context))
    except Exception as exc:
        logger.error("Web search failed: %s", exc)
        
    return {
        "next_node": "output_assembler",
        "web_context": web_context,
    }

# ══════════════════════════════════════════════════════════════════════
# NODE 5 — Output Assembler + Guardrail
# ══════════════════════════════════════════════════════════════════════

async def output_assembler_node(state: AgentState) -> dict:
    """Synthesise the final response using ONLY retrieved context."""
    logger.info("━━━ OUTPUT ASSEMBLER NODE ━━━")

    retrieved = state.get("retrieved_verses", [])
    denomination = state.get("denomination", "general")
    is_controversial = state.get("is_controversial", False)
    retry_count = state.get("retry_count", 0)

    # ── Check for "not found" status ──
    for msg in reversed(state["messages"]):
        if hasattr(msg, "content") and "[VERSE_STATUS]not_found[/VERSE_STATUS]" in msg.content:
            logger.info("Verse not found — returning fallback message")
            return {
                "next_node": "end",
                "messages": [AIMessage(content=VERSE_NOT_FOUND_MESSAGE)],
                "retry_count": 0,
            }

    # ── Build retrieved context string ──
    if retrieved:
        context_lines = []
        for v in retrieved:
            context_lines.append(
                f"**{v.get('reference', 'Unknown')}**: \"{v.get('text', '')}\""
            )
        retrieved_context = "\n".join(context_lines)
    else:
        retrieved_context = "(No verses retrieved — answer from general theological knowledge only. Do NOT quote specific verses.)"

    # ── Build web context string ──
    web_ctx_list = state.get("web_context", [])
    web_context_str = "\n\n".join(web_ctx_list) if web_ctx_list else "(No web search context retrieved.)"

    # ── Build the prompt ──
    system_content = OUTPUT_ASSEMBLER_PROMPT.format(
        retrieved_context=retrieved_context,
        web_context=web_context_str,
        denomination=denomination,
        is_controversial=str(is_controversial),
    )

    # Get the original user question
    user_msg = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_msg = msg.content

    llm = _get_llm(temperature=0.4)
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_msg),
    ]

    try:
        response = await llm.ainvoke(messages)
        response_text = response.content.strip()
    except Exception as exc:
        logger.error("Output assembly LLM call failed: %s", exc)
        response_text = (
            "I'm sorry, I encountered an error while preparing your answer. "
            "Please try asking again."
        )
        return {
            "next_node": "end",
            "messages": [AIMessage(content=response_text)],
            "retry_count": 0,
        }

    # ── Guardrail: substring validation ──
    if retrieved:
        is_valid, cleaned_text = validate_scripture_quotes(response_text, retrieved)
        if not is_valid:
            logger.warning("⚠️ Guardrail FAILED (attempt %d/2)", retry_count + 1)
            if retry_count < 2:
                # Retry with stronger instruction
                return {
                    "next_node": "retry_assembler",
                    "retry_count": retry_count + 1,
                    "messages": [
                        SystemMessage(
                            content="[GUARDRAIL_RETRY] Your previous response contained "
                            "quoted text that did not match the retrieved verses. "
                            "Use ONLY the exact text from the retrieved context."
                        )
                    ],
                }
            else:
                logger.warning("⚠️ Guardrail exhausted retries — using redacted version")
                response_text = cleaned_text + (
                    "\n\n*⚠️ Note: Some verse quotations could not be verified "
                    "against the source text and have been redacted for accuracy.*"
                )
        else:
            logger.info("✅ Guardrail PASSED")

    return {
        "next_node": "end",
        "messages": [AIMessage(content=response_text)],
        "retry_count": 0,
    }
