"""
Linkage matcher v1 — tuned to what audit_flattened_data.py actually found in
the Synthetic Denver data, not generic assumptions.

Design decisions, and why:
  - Blocking uses TWO independent passes (soundex(family_name) and phone
    last-4), then takes the UNION of candidate pairs. Single-key blocking
    would miss real matches when that one key is corrupted (e.g. the
    birth_date transposition seen in the audit) — union blocking is the
    standard record-linkage fix for this.
  - birth_date is scored, not filtered — a transposed-digit birthdate should
    lower confidence, not eliminate the candidate outright.
  - given_name comparison handles dropped tokens (e.g. "Joseph Tomas" vs
    "Joseph") via token subset check, falling back to fuzzy similarity for
    actual spelling variants.
  - city/address get a light regex cleanup pass (strip "###", "UNIT####")
    BEFORE fuzzy comparison — that junk is structural noise, not spelling
    variance, and would otherwise just dilute the similarity score.

Usage:
    python linkage_matcher_v1.py ./flattened
"""

import re
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

SITE_FILES = ["CH.csv", "DH.csv", "GotR.csv", "HFC.csv", "KP.csv"]

# ---- Weights: phone and family_name are the most reliable per the audit,
# birth_date is informative but known to have transposition errors, so it
# gets real weight but not veto power. Tune these once you see score
# distributions on real data — these are a reasonable starting point, not
# a final answer. ----
WEIGHTS = {
    "family_name": 0.25,
    "given_name": 0.20,
    "birth_date": 0.20,
    "phone": 0.20,
    "address": 0.15,
}

AUTO_LINK_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.60


def clean_city(city: str) -> str:
    if pd.isna(city):
        return ""
    city = re.sub(r"^#+", "", city)                    # strip leading ### junk
    city = re.sub(r"^UNIT\s*\d+\s*", "", city, flags=re.I)  # strip "UNIT1316 " prefix
    return city.strip()


def soundex(name: str) -> str:
    """Minimal soundex for blocking. Good enough as a blocking key —
    doesn't need to be perfect, just needs to group likely-same-name rows."""
    if not name:
        return ""
    name = name.upper()
    codes = {**dict.fromkeys("BFPV", "1"), **dict.fromkeys("CGJKQSXZ", "2"),
             **dict.fromkeys("DT", "3"), "L": "4", **dict.fromkeys("MN", "5"), "R": "6"}
    first = name[0]
    tail = "".join(codes.get(c, "") for c in name[1:])
    # collapse consecutive duplicates
    out = first
    for c in tail:
        if c != out[-1]:
            out += c
    return (out + "000")[:4]


def phone_last4(phone: str) -> str:
    if pd.isna(phone):
        return ""
    digits = re.sub(r"\D", "", phone)
    return digits[-4:] if len(digits) >= 4 else digits


import unicodedata

PLACEHOLDER_PATTERNS = re.compile(
    r"^(::\w+::|baby\s*(girl|boy)|infant|unknown|unnamed|newborn)\b", re.I
)
TITLE_PREFIX = re.compile(r"^(mr|mrs|ms|miss|dr|prof)\.?\s+", re.I)


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def clean_name(name: str) -> str:
    """Strip garbage characters ([[, commas, etc.) but keep hyphens/apostrophes,
    which are meaningful in names like Chacon-Maestas or O'Brien."""
    if pd.isna(name):
        return ""
    name = strip_accents(name)
    name = TITLE_PREFIX.sub("", name.strip())
    name = re.sub(r"[^a-zA-Z\-'\s]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def is_placeholder(name: str) -> bool:
    """Catches template placeholders (::firstname::) and real-world newborn
    placeholder names (Baby Girl, Unnamed) — both mean 'this field carries
    no identity signal', not 'this is a mismatched name'."""
    if pd.isna(name) or not name.strip():
        return True
    return bool(PLACEHOLDER_PATTERNS.match(name.strip()))


def name_similarity(a: str, b: str) -> float | None:
    """Handles real failure modes found in this data:
      - dropped tokens ("Joseph Tomas" vs "Joseph")
      - hyphenated names split differently ("Chacon-Maestas" vs "Maestas")
      - truncation ("Knowlton" vs "Knowl")
      - mid-word space insertion ("Carliegh" vs "Car leigh")
      - accented characters ("Domínguez" vs "Dominguez")
      - title prefixes ("Ms Francesca" vs "Francesca")
    Returns None (not 0.0) for placeholder values — the caller should treat
    that as 'no signal', not 'confirmed mismatch', and reweight accordingly."""
    if is_placeholder(a) or is_placeholder(b):
        return None

    a, b = clean_name(a), clean_name(b)
    if not a or not b:
        return None

    a_norm = a.replace("-", " ")
    b_norm = b.replace("-", " ")

    token_set_score = fuzz.token_set_ratio(a_norm, b_norm) / 100.0
    partial_score = fuzz.partial_ratio(a_norm, b_norm) / 100.0
    nospace_score = fuzz.ratio(a_norm.replace(" ", ""), b_norm.replace(" ", "")) / 100.0

    return max(token_set_score, partial_score, nospace_score)


def date_similarity(a: str, b: str) -> float:
    if pd.isna(a) or pd.isna(b):
        return 0.0
    if a == b:
        return 1.0
    return fuzz.ratio(a, b) / 100.0  # catches single-digit transposition as a near-match


def score_pair(row_a: pd.Series, row_b: pd.Series) -> float:
    raw_scores = {
        "family_name": name_similarity(row_a.family_name, row_b.family_name),
        "given_name": name_similarity(row_a.given_name, row_b.given_name),
        "birth_date": date_similarity(row_a.birth_date, row_b.birth_date),
        "phone": 1.0 if row_a.phone == row_b.phone else 0.0,
        "address": fuzz.ratio(
            f"{row_a.address_line} {clean_city(row_a.city)}",
            f"{row_b.address_line} {clean_city(row_b.city)}",
        ) / 100.0,
    }
    # placeholder fields (given_name/family_name only) return None -> drop
    # that field and renormalize weights across the remaining fields, rather
    # than scoring it as a confirmed 0.0 mismatch
    active = {k: v for k, v in raw_scores.items() if v is not None}
    weight_total = sum(WEIGHTS[k] for k in active)
    return sum(active[k] * WEIGHTS[k] for k in active) / weight_total


def build_blocks(df: pd.DataFrame) -> set:
    """Union of two independent blocking passes -> candidate row-index pairs."""
    df = df.copy()
    df["_soundex"] = df.family_name.fillna("").apply(
        lambda n: soundex(clean_name(n).replace("-", " ").split(" ")[-1])
    )
    df["_phone4"] = df.phone.fillna("").apply(phone_last4)

    candidates = set()
    for key_col in ["_soundex", "_phone4"]:
        for name, group in df.groupby(key_col):
            if key_col == "_phone4" and name == "":
                continue
            idxs = group.index.tolist()
            if len(idxs) > 1:
                for i, j in combinations(idxs, 2):
                    candidates.add((min(i, j), max(i, j)))
    return candidates


def main():
    if len(sys.argv) != 2:
        print("Usage: python linkage_matcher_v1.py <folder with site CSVs>")
        sys.exit(1)

    folder = Path(sys.argv[1])
    frames = []
    for fname in SITE_FILES:
        path = folder / fname
        if path.exists():
            df = pd.read_csv(path, dtype=str)
            frames.append(df)

    all_data = pd.concat(frames, ignore_index=True).reset_index(drop=True)
    # only cross-site pairs matter for this demo — same-site duplicates are a different problem
    print(f"Loaded {len(all_data)} records across {all_data.site.nunique()} sites")

    print("Building candidate blocks...")
    candidates = build_blocks(all_data)
    print(f"{len(candidates)} candidate pairs after blocking")

    results = []
    for i, j in candidates:
        row_a, row_b = all_data.loc[i], all_data.loc[j]
        if row_a.site == row_b.site:
            continue  # only cross-site matches are the target for this demo
        score = score_pair(row_a, row_b)
        results.append({
            "idx_a": i, "idx_b": j,
            "site_a": row_a.site, "site_b": row_b.site,
            "name_a": f"{row_a.given_name} {row_a.family_name}",
            "name_b": f"{row_b.given_name} {row_b.family_name}",
            "score": round(score, 3),
            "true_match": row_a.link_id_ground_truth == row_b.link_id_ground_truth,
        })

    results_df = pd.DataFrame(results).sort_values("score", ascending=False)

    auto = results_df[results_df.score >= AUTO_LINK_THRESHOLD]
    review = results_df[(results_df.score >= REVIEW_THRESHOLD) & (results_df.score < AUTO_LINK_THRESHOLD)]
    rejected = results_df[results_df.score < REVIEW_THRESHOLD]

    print(f"\nAuto-link (>= {AUTO_LINK_THRESHOLD}): {len(auto)} pairs")
    print(f"Manual review ({REVIEW_THRESHOLD}-{AUTO_LINK_THRESHOLD}): {len(review)} pairs")
    print(f"Rejected (< {REVIEW_THRESHOLD}): {len(rejected)} pairs")

    if "true_match" in results_df.columns:
        true_positives = auto.true_match.sum()
        false_positives = len(auto) - true_positives
        total_true_matches = results_df.true_match.sum()
        precision = true_positives / len(auto) if len(auto) else 0
        recall = true_positives / total_true_matches if total_true_matches else 0
        print(f"\n--- Against ground truth (auto-link tier only) ---")
        print(f"Precision: {precision:.3f}  Recall: {recall:.3f}")
        print(f"True positives: {true_positives}, False positives: {false_positives}")
        print(f"Total true cross-site matches available: {total_true_matches}")

        missed = results_df[(results_df.true_match) & (results_df.score < AUTO_LINK_THRESHOLD)]
        if len(missed) > 0:
            print(f"\n{len(missed)} true matches scored below auto-link threshold — examples:")
            print(missed[["name_a", "name_b", "score"]].head(5).to_string(index=False))

        false_pos_rows = auto[~auto.true_match]
        if len(false_pos_rows) > 0:
            print(f"\n{len(false_pos_rows)} false positives in auto-link tier — examples:")
            print(false_pos_rows[["name_a", "name_b", "score"]].head(10).to_string(index=False))

    results_df.to_csv(folder / "linkage_results.csv", index=False)
    print(f"\nFull results written to {folder / 'linkage_results.csv'}")


if __name__ == "__main__":
    main()