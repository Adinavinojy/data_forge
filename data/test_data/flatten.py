"""
Flattens Synthetic Denver FHIR patient bundles (one JSON file per patient,
per site folder) into a single flat CSV per site.

Usage:
    python flatten.py "C:\\path\\to\\Synthetic Denver" ./output

Dynamically detects and processes all subfolders inside the input folder.
Skips hospitalInformation*.json and practitionerInformation*.json in each folder
— those are Synthea's org/provider reference files, not patients.
"""

import json
import sys
from pathlib import Path
import pandas as pd

SKIP_PREFIXES = ("hospitalInformation", "practitionerInformation")


def flatten_one_bundle(bundle_path: Path, site_name: str) -> dict | None:
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [skip] {bundle_path.name}: failed to parse ({e})")
        return None

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") != "Patient":
            continue

        record_id = resource.get("id")
        link_id = None
        for ident in resource.get("identifier", []):
            system = ident.get("system", "")
            if "link_id" in system:
                link_id = ident.get("value")
            # keep the raw system too, in case naming differs slightly
            elif "codi.mitre.org" in system and link_id is None:
                pass  # the plain codi.mitre.org id is the per-record id, not link_id

        name = (resource.get("name") or [{}])[0]
        given = " ".join(name.get("given", []))
        family = name.get("family", "")

        address = (resource.get("address") or [{}])[0]

        telecom = {t.get("system"): t.get("value") for t in resource.get("telecom", [])}

        return {
            "record_id": record_id,
            "link_id_ground_truth": link_id,  # exclude from matching input; join back only for scoring
            "site": site_name,
            "given_name": given,
            "family_name": family,
            "birth_date": resource.get("birthDate"),
            "gender": resource.get("gender"),
            "address_line": " ".join(address.get("line", [])),
            "city": address.get("city"),
            "state": address.get("state"),
            "zip": address.get("postalCode"),
            "phone": telecom.get("phone"),
            "email": telecom.get("email"),
            "source_file": bundle_path.name,
        }
    return None  # no Patient resource found in this bundle


def flatten_site(site_dir: Path) -> pd.DataFrame:
    rows = []
    json_files = [
        f for f in site_dir.glob("*.json")
        if not f.name.startswith(SKIP_PREFIXES)
    ]
    print(f"{site_dir.name}: {len(json_files)} patient bundle files found")

    for f in json_files:
        row = flatten_one_bundle(f, site_dir.name)
        if row is not None:
            rows.append(row)

    df = pd.DataFrame(rows)
    print(f"{site_dir.name}: {len(df)} patient records flattened")
    return df


def main():
    if len(sys.argv) != 3:
        print("Usage: python flatten.py <path to 'Synthetic Denver' folder> <output folder>")
        sys.exit(1)

    root = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    if not root.exists() or not root.is_dir():
        print(f"Error: Input directory '{root}' does not exist or is not a directory.")
        sys.exit(1)

    # Find all subdirectories in the root folder
    site_dirs = [d for d in root.iterdir() if d.is_dir()]
    if not site_dirs:
        print(f"No subdirectories found in '{root}'")
        sys.exit(0)

    for site_dir in site_dirs:
        df = flatten_site(site_dir)
        if df.empty:
            print(f"  [info] No patient data found in {site_dir.name}, skipping CSV write")
            continue
        out_path = out_dir / f"{site_dir.name}.csv"
        df.to_csv(out_path, index=False)
        print(f"  -> wrote {out_path}\n")

    print("Done. Load each site's CSV as a separate 'source system' in the linkage demo.")
    print("Remember: keep link_id_ground_truth OUT of the matcher's inputs — use it only")
    print("afterward to score precision/recall against your matching results.")


if __name__ == "__main__":
    main()