"""Bible API & ChromaDB connector — deterministic, non-LLM execution functions.

Every function here is pure Python / HTTP — the LLM is never invoked for
actual verse lookup.  This is the heart of the anti-hallucination strategy.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

import chromadb
import httpx

from agent.seed_data import SEED_DATA

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# API.Bible constants
# ──────────────────────────────────────────────────────────────────────
API_BIBLE_BASE = "https://rest.api.bible/v1"

# Mapping of common book names → API.Bible 3-letter abbreviation
BOOK_ABBREV: dict[str, str] = {
    "genesis": "GEN", "gen": "GEN",
    "exodus": "EXO", "exo": "EXO", "ex": "EXO",
    "leviticus": "LEV", "lev": "LEV",
    "numbers": "NUM", "num": "NUM",
    "deuteronomy": "DEU", "deu": "DEU", "deut": "DEU",
    "joshua": "JOS", "jos": "JOS", "josh": "JOS",
    "judges": "JDG", "jdg": "JDG", "judg": "JDG",
    "ruth": "RUT", "rut": "RUT",
    "1 samuel": "1SA", "1samuel": "1SA", "1 sam": "1SA", "1sam": "1SA",
    "2 samuel": "2SA", "2samuel": "2SA", "2 sam": "2SA", "2sam": "2SA",
    "1 kings": "1KI", "1kings": "1KI", "1 kgs": "1KI",
    "2 kings": "2KI", "2kings": "2KI", "2 kgs": "2KI",
    "1 chronicles": "1CH", "1chronicles": "1CH", "1 chr": "1CH",
    "2 chronicles": "2CH", "2chronicles": "2CH", "2 chr": "2CH",
    "ezra": "EZR", "ezr": "EZR",
    "nehemiah": "NEH", "neh": "NEH",
    "esther": "EST", "est": "EST",
    "job": "JOB",
    "psalms": "PSA", "psalm": "PSA", "psa": "PSA", "ps": "PSA",
    "proverbs": "PRO", "pro": "PRO", "prov": "PRO",
    "ecclesiastes": "ECC", "ecc": "ECC", "eccl": "ECC",
    "song of solomon": "SNG", "song of songs": "SNG", "sng": "SNG",
    "isaiah": "ISA", "isa": "ISA",
    "jeremiah": "JER", "jer": "JER",
    "lamentations": "LAM", "lam": "LAM",
    "ezekiel": "EZK", "ezk": "EZK", "eze": "EZK",
    "daniel": "DAN", "dan": "DAN",
    "hosea": "HOS", "hos": "HOS",
    "joel": "JOL", "jol": "JOL",
    "amos": "AMO", "amo": "AMO",
    "obadiah": "OBA", "oba": "OBA",
    "jonah": "JON", "jon": "JON",
    "micah": "MIC", "mic": "MIC",
    "nahum": "NAM", "nam": "NAM",
    "habakkuk": "HAB", "hab": "HAB",
    "zephaniah": "ZEP", "zep": "ZEP",
    "haggai": "HAG", "hag": "HAG",
    "zechariah": "ZEC", "zec": "ZEC", "zech": "ZEC",
    "malachi": "MAL", "mal": "MAL",
    "matthew": "MAT", "mat": "MAT", "matt": "MAT",
    "mark": "MRK", "mrk": "MRK",
    "luke": "LUK", "luk": "LUK",
    "john": "JHN", "jhn": "JHN",
    "acts": "ACT", "act": "ACT",
    "romans": "ROM", "rom": "ROM",
    "1 corinthians": "1CO", "1corinthians": "1CO", "1 cor": "1CO", "1cor": "1CO",
    "2 corinthians": "2CO", "2corinthians": "2CO", "2 cor": "2CO", "2cor": "2CO",
    "galatians": "GAL", "gal": "GAL",
    "ephesians": "EPH", "eph": "EPH",
    "philippians": "PHP", "php": "PHP", "phil": "PHP",
    "colossians": "COL", "col": "COL",
    "1 thessalonians": "1TH", "1thessalonians": "1TH", "1 thess": "1TH", "1thess": "1TH",
    "2 thessalonians": "2TH", "2thessalonians": "2TH", "2 thess": "2TH", "2thess": "2TH",
    "1 timothy": "1TI", "1timothy": "1TI", "1 tim": "1TI", "1tim": "1TI",
    "2 timothy": "2TI", "2timothy": "2TI", "2 tim": "2TI", "2tim": "2TI",
    "titus": "TIT", "tit": "TIT",
    "philemon": "PHM", "phm": "PHM",
    "hebrews": "HEB", "heb": "HEB",
    "james": "JAS", "jas": "JAS",
    "1 peter": "1PE", "1peter": "1PE", "1 pet": "1PE", "1pet": "1PE",
    "2 peter": "2PE", "2peter": "2PE", "2 pet": "2PE", "2pet": "2PE",
    "1 john": "1JN", "1john": "1JN", "1 jn": "1JN", "1jn": "1JN",
    "2 john": "2JN", "2john": "2JN", "2 jn": "2JN",
    "3 john": "3JN", "3john": "3JN", "3 jn": "3JN",
    "jude": "JUD", "jud": "JUD",
    "revelation": "REV", "rev": "REV", "revelations": "REV",
    # Deuterocanonical
    "sirach": "SIR", "sir": "SIR",
    "wisdom": "WIS", "wis": "WIS",
    "1 maccabees": "1MA", "1maccabees": "1MA", "1 macc": "1MA",
    "2 maccabees": "2MA", "2maccabees": "2MA", "2 macc": "2MA",
    "tobit": "TOB", "tob": "TOB",
    "judith": "JDT", "jdt": "JDT",
    "baruch": "BAR", "bar": "BAR",
}


def parse_verse_reference(text: str) -> Optional[str]:
    """Convert a human verse reference to API.Bible passage-ID format.

    Examples
    --------
    >>> parse_verse_reference("John 3:16")
    'JHN.3.16'
    >>> parse_verse_reference("1 Corinthians 13:4-8")
    '1CO.13.4-1CO.13.8'
    >>> parse_verse_reference("Psalm 23")
    'PSA.23'
    >>> parse_verse_reference("Hezekiah 3:2")  # Fake book
    None
    """
    text = text.strip()

    # Pattern: optional number prefix + book + chapter + optional :verse(-verse)
    pattern = r"^(\d?\s*[A-Za-z ]+?)\s+(\d+)(?::(\d+))?(?:\s*[-–]\s*(\d+))?$"
    match = re.match(pattern, text)
    if not match:
        return None

    book_raw = match.group(1).strip().lower()
    chapter = match.group(2)
    verse_start = match.group(3)
    verse_end = match.group(4)

    abbrev = BOOK_ABBREV.get(book_raw)
    if not abbrev:
        return None

    if verse_start and verse_end:
        return f"{abbrev}.{chapter}.{verse_start}-{abbrev}.{chapter}.{verse_end}"
    elif verse_start:
        return f"{abbrev}.{chapter}.{verse_start}"
    else:
        return f"{abbrev}.{chapter}"


# ──────────────────────────────────────────────────────────────────────
# API.Bible HTTP calls
# ──────────────────────────────────────────────────────────────────────

async def fetch_passage(
    bible_id: str,
    passage_id: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> dict | None:
    """Retrieve exact verse text from API.Bible.

    Returns
    -------
    dict with keys ``reference``, ``text``, ``passage_id``; or None on error.
    """
    api_key = os.getenv("API_BIBLE_KEY", "")
    url = f"{API_BIBLE_BASE}/bibles/{bible_id}/passages/{passage_id}"
    headers = {"api-key": api_key}
    params = {
        "content-type": "text",
        "include-notes": "false",
        "include-titles": "false",
        "include-chapter-numbers": "false",
        "include-verse-numbers": "true",
        "include-verse-spans": "false",
    }

    _client = client or httpx.AsyncClient(timeout=15)
    close_after = client is None
    try:
        resp = await _client.get(url, headers=headers, params=params)
        if resp.status_code == 404:
            logger.warning("Passage not found: %s", passage_id)
            return None
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "reference": data.get("reference", passage_id),
            "text": data.get("content", "").strip(),
            "passage_id": passage_id,
        }
    except httpx.HTTPStatusError as exc:
        logger.error("API.Bible error %s: %s", exc.response.status_code, exc)
        return None
    except Exception as exc:
        logger.error("API.Bible request failed: %s", exc)
        return None
    finally:
        if close_after:
            await _client.aclose()


async def search_bible(
    bible_id: str,
    query: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    """Keyword search on API.Bible, returning up to 5 verse results.

    Each result dict has ``reference``, ``text``, ``passage_id``.
    """
    api_key = os.getenv("API_BIBLE_KEY", "")
    url = f"{API_BIBLE_BASE}/bibles/{bible_id}/search"
    headers = {"api-key": api_key}
    params = {"query": query, "limit": 5}

    _client = client or httpx.AsyncClient(timeout=15)
    close_after = client is None
    try:
        resp = await _client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        verses = data.get("verses", [])
        results = []
        for v in verses[:5]:
            results.append({
                "reference": v.get("reference", ""),
                "text": v.get("text", "").strip(),
                "passage_id": v.get("id", ""),
            })
        return results
    except Exception as exc:
        logger.error("API.Bible search failed: %s", exc)
        return []
    finally:
        if close_after:
            await _client.aclose()


# ──────────────────────────────────────────────────────────────────────
# ChromaDB (local semantic topic search)
# ──────────────────────────────────────────────────────────────────────

def init_chromadb() -> chromadb.Collection:
    """Create an in-memory ChromaDB collection and seed it with topic data.

    Uses ChromaDB's default ``all-MiniLM-L6-v2`` embedding model so no
    external API call is needed for the embedding step.
    """
    client = chromadb.EphemeralClient()

    # Delete if exists (idempotent re-init on server restart)
    try:
        client.delete_collection("bible_topics")
    except Exception:
        pass

    collection = client.create_collection(
        name="bible_topics",
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    documents = []
    metadatas = []
    for i, entry in enumerate(SEED_DATA):
        ids.append(f"topic_{i}")
        documents.append(f"{entry['topic']}: {entry['description']}")
        metadatas.append({
            "topic": entry["topic"],
            "verses": ",".join(entry["verses"]),
        })

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("ChromaDB seeded with %d topic entries", len(ids))
    return collection


def search_topics(
    collection: chromadb.Collection,
    query: str,
    n_results: int = 3,
) -> list[dict]:
    """Semantic search returning the top-N matching topics with their verse IDs.

    Returns list of dicts: ``{"topic": str, "verses": list[str], "score": float}``.
    """
    results = collection.query(query_texts=[query], n_results=n_results)

    output = []
    if results and results["metadatas"]:
        for meta, distance in zip(
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({
                "topic": meta["topic"],
                "verses": meta["verses"].split(","),
                "score": 1 - distance,  # cosine distance → similarity
            })
    return output
