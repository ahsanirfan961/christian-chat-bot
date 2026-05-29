"""Quick smoke test for validators and ChromaDB."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.validators import validate_scripture_quotes
from agent.tools import init_chromadb, search_topics

# ── Validator tests ──
print("=== Validator Tests ===")

# Test 1: Valid quote
verses = [{"text": "For God so loved the world that he gave his only begotten Son"}]
ok, text = validate_scripture_quotes(
    'Jesus said: "For God so loved the world that he gave his only begotten Son"',
    verses,
)
print(f"Test 1 (valid quote): passed={ok}")

# Test 2: Fabricated quote
ok2, text2 = validate_scripture_quotes(
    'The Bible says: "Money is the root of all happiness"',
    verses,
)
print(f"Test 2 (fake quote): passed={ok2}")
print(f"  Cleaned: {text2}")

# Test 3: No quotes in output
ok3, text3 = validate_scripture_quotes("God loves you very much.", verses)
print(f"Test 3 (no quotes): passed={ok3}")

# Test 4: Empty verses
ok4, text4 = validate_scripture_quotes(
    'It says "something"', []
)
print(f"Test 4 (empty verses + quote): passed={ok4}")

# ── ChromaDB tests ──
print("\n=== ChromaDB Tests ===")
coll = init_chromadb()
results = search_topics(coll, "feeling lost and alone")
print(f"Query 'feeling lost': {[r['topic'] for r in results]}")

results2 = search_topics(coll, "what is love")
print(f"Query 'what is love': {[r['topic'] for r in results2]}")

results3 = search_topics(coll, "how to pray")
print(f"Query 'how to pray': {[r['topic'] for r in results3]}")

results4 = search_topics(coll, "is baptism necessary")
print(f"Query 'baptism': {[r['topic'] for r in results4]}")

print("\n✅ All smoke tests complete!")
