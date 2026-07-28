"""
Audits the flattened Synthetic Denver CSVs before building the matcher.
Answers the questions that actually determine your matching strategy:
  - How many patients are linked across sites (your ground-truth signal)?
  - Which fields are reliable enough to block/match on?
  - What does real-world messiness actually look like in this data?

Usage:
    python audit_flattened_data.py ./flattened
"""

import sys
from pathlib import Path
import pandas as pd

SITE_FILES = ["CH.csv", "DH.csv", "GotR.csv", "HFC.csv", "KP.csv"]


def main():
    if len(sys.argv) != 2:
        print("Usage: python audit_flattened_data.py <folder with site CSVs>")
        sys.exit(1)

    folder = Path(sys.argv[1])
    frames = []
    for fname in SITE_FILES:
        path = folder / fname
        if not path.exists():
            print(f"[warn] {path} not found, skipping")
            continue
        df = pd.read_csv(path, dtype=str)
        frames.append(df)
        print(f"{fname}: {len(df)} rows")

    all_data = pd.concat(frames, ignore_index=True)
    print(f"\nTotal records across all sites: {len(all_data)}")

    # --- 1. Null rates on key matching fields ---
    print("\n--- Null rates on key fields (lower = more reliable to match on) ---")
    for col in ["link_id_ground_truth", "given_name", "family_name", "birth_date",
                "phone", "address_line", "city", "zip"]:
        if col in all_data.columns:
            null_pct = all_data[col].isna().mean() * 100
            print(f"  {col}: {null_pct:.1f}% null")

    # --- 2. Cross-site linkage signal: how many link_ids appear in >1 site? ---
    if "link_id_ground_truth" in all_data.columns:
        valid = all_data.dropna(subset=["link_id_ground_truth"])
        site_counts = valid.groupby("link_id_ground_truth")["site"].nunique()
        multi_site = site_counts[site_counts > 1]
        print(f"\n--- Cross-site linkage signal ---")
        print(f"  Unique link_ids with a value: {valid['link_id_ground_truth'].nunique()}")
        print(f"  link_ids appearing in more than one site: {len(multi_site)}")
        print(f"  (these are your real cross-system matching targets)")

        record_counts = valid.groupby("link_id_ground_truth").size()
        multi_record = record_counts[record_counts > 1]
        print(f"  link_ids with more than one record total: {len(multi_record)}")

        # --- 3. Show one real example of a multi-record identity, to see actual messiness ---
        if len(multi_record) > 0:
            example_id = multi_record.index[0]
            example_rows = all_data[all_data["link_id_ground_truth"] == example_id]
            print(f"\n--- Example: link_id_ground_truth = {example_id} ---")
            cols_to_show = ["site", "given_name", "family_name", "birth_date",
                             "phone", "address_line", "city", "zip"]
            cols_present = [c for c in cols_to_show if c in example_rows.columns]
            print(example_rows[cols_present].to_string(index=False))
    else:
        print("\n[warn] link_id_ground_truth column not found — check the flattening script's "
              "identifier.system matching against a real file.")

    # --- 4. Spot check for the "###Boulder" style formatting artifacts ---
    if "city" in all_data.columns:
        weird_cities = all_data[all_data["city"].str.contains(r"[^a-zA-Z\s\-\.]", na=False, regex=True)]
        print(f"\n--- Rows with unusual characters in city field: {len(weird_cities)} ---")
        if len(weird_cities) > 0:
            print(weird_cities[["site", "city"]].drop_duplicates().head(10).to_string(index=False))


if __name__ == "__main__":
    main()