# fuzzy_no_alias.py
from rapidfuzz import process, fuzz
import re

# --- original candidate list (exact strings you provided) ---
candidates = [
"black, XL, CHINA","Mint, XL, CHINA","black, L, CHINA","Mint, L, CHINA","black, M, CHINA","Mint, M, CHINA",
"Beige, XXL, CHINA","Orange, XXL, CHINA","CORAL RED, XXL, CHINA","Silver, XL, CHINA","Silver, L, CHINA",
"Silver, M, CHINA","black, XXL, CHINA","Mint, XXL, CHINA","GRAY, XL, CHINA","WHITE, XL, CHINA",
"GRAY, L, CHINA","WHITE, L, CHINA","GRAY, M, CHINA","WHITE, M, CHINA","Silver, XXL, CHINA",
"Dark Grey, XL, CHINA","Dark Grey, L, CHINA","Dark Grey, M, CHINA","GRAY, XXL, CHINA","WHITE, XXL, CHINA",
"Champagne, XL, CHINA","Champagne, L, CHINA","Champagne, M, CHINA","Dark Grey, XXL, CHINA",
"army green, XL, CHINA","army green, L, CHINA","army green, M, CHINA","army green, XXL, CHINA",
"Champagne, XXL, CHINA","Fuchsia, XL, CHINA","Fuchsia, L, CHINA","Fuchsia, M, CHINA","Beige, XL, CHINA",
"Orange, XL, CHINA","CORAL RED, XL, CHINA","Beige, L, CHINA","Orange, L, CHINA","CORAL RED, L, CHINA",
"Beige, M, CHINA","Orange, M, CHINA","CORAL RED, M, CHINA","Fuchsia, XXL, CHINA", 'CN'
]

# --- testcases: (query, expected_original_string) ---
test_cases = [

    ("china",                  "Dark Grey, M, CHINA"),
    ("dark green m china",                "army green, M, CHINA"),
   
]

# --- normalization (no aliasing) ---
def normalize_text(s: str) -> str:
    """
    Lowercase, remove punctuation (except keep spaces), collapse whitespace.
    IMPORTANT: no alias mapping, no synonym substitution.
    """
    if s is None:
        return ""
    s = s.lower()
    # replace punctuation with spaces (commas, hyphens, slashes, etc.)
    s = re.sub(r"[^\w\s]", " ", s)
    # collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s

# Precompute normalized candidate strings (mapping normalized -> list of original strings)
norm_map = {}
for orig in candidates:
    n = normalize_text(orig)
    norm_map.setdefault(n, []).append(orig)
norm_candidates = list(norm_map.keys())

# fuzzy config
SCORER = fuzz.token_set_ratio  # good for multi-token comparisons
LIMIT = 5
THRESH = 80  # demonstration acceptance threshold


def normalized_fuzzy(query):
    """Normalize query and fuzzy against normalized candidate keys (no aliasing)"""
    qn = normalize_text(query)
    res = process.extract(qn, norm_candidates, scorer=SCORER, limit=LIMIT)
    # map back normalized keys to original example strings for readability
    mapped = []
    for norm_key, score, _ in res:
        # pick the first original that had this normalized key
        orig = norm_map.get(norm_key, [norm_key])[0]
        mapped.append((orig, score, norm_key))
    return mapped

# Run tests and print diagnostics
def run_tests():
    total = len(test_cases)
    raw_matches = 0
    norm_matches = 0

    for q, expected in test_cases:
        print("\n" + "-"*70)
        print(f"Query: {q!r}")
        print(f"Expected (original string): {expected!r}\n")

        # Normalized fuzzy (no aliasing)
        norm_res = normalized_fuzzy(q)
        norm_top = norm_res[0] if norm_res else (None, 0, None)
        print("\nNormalized fuzzy top-5 (normalize both sides; no alias maps):")
        for i, (orig, score, norm_key) in enumerate(norm_res, start=1):
            print(f"  {i:02d}. original={orig!r}  score={score}  norm_key={norm_key!r}")
        norm_choice, norm_score, norm_key = norm_top
        norm_ok = (norm_choice == expected)
        print(f" Normalized best: {norm_choice!r} (score={norm_score}) -> {'PASS' if norm_ok else 'FAIL'}")
        if norm_score >= THRESH:
            norm_matches += 1

        # decision by threshold (color-only match lenient heuristic)
        print("\nHeuristic threshold acceptance (score >= {}):".format(THRESH))
        print(f" Norm accepted: {norm_score >= THRESH}")

    print("\n" + "="*70)
    print(f"Normalized top-1 exact-match (no alias): {norm_matches}/{total} = {norm_matches/total:.2%}")
    print("="*70)

if __name__ == "__main__":
    run_tests()
