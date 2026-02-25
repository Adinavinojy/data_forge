import requests
import json
import os
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
EMAIL = "adinavinoji@gmail.com"
PASSWORD = "hello"
DATASET_PATH = "tests/data/test_dataset.csv"

def log(msg, color="white"):
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "white": "\033[0m"
    }
    print(f"{colors.get(color, '')}{msg}{colors['white']}")

def test_pipeline():
    session = requests.Session()

    # 1. Login
    log("1. Logging in...", "blue")
    res = session.post(f"{BASE_URL}/auth/login/access-token", data={
        "username": EMAIL,
        "password": PASSWORD
    })
    if res.status_code != 200:
        log(f"Login failed: {res.text}", "red")
        sys.exit(1)
    
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("Login successful!", "green")

    # 2. Upload Dataset
    log("2. Uploading dataset...", "blue")
    with open(DATASET_PATH, "rb") as f:
        files = {"file": f}
        res = session.post(f"{BASE_URL}/datasets/upload", files=files, headers=headers)
    
    if res.status_code != 200:
        log(f"Upload failed: {res.text}", "red")
        sys.exit(1)
    
    dataset_id = res.json()["dataset"]["id"]
    log(f"Dataset uploaded! ID: {dataset_id}", "green")

    # 3. Add Pipeline Steps (Simulating Interactive Workspace)
    log("3. Adding Pipeline Steps...", "blue")

    steps = [
        # 3.1 Drop Duplicates
        {
            "op": "drop_duplicates", 
            "params": {"columns": []}, # Global
            "desc": "Removing duplicates"
        },
        # 3.2 Fill Missing (Mean) for Salary
        {
            "op": "fill_missing",
            "params": {"columns": ["salary"], "method": "mean"},
            "desc": "Filling missing salary with mean"
        },
        # 3.3 Text Case Lower for Name
        {
            "op": "text_case",
            "params": {"columns": ["name"], "case": "lower"},
            "desc": "Converting name to lowercase"
        },
        # 3.4 Convert Score to Numeric
        {
            "op": "convert_type",
            "params": {"columns": ["score_str"], "type": "numeric"},
            "desc": "Converting score_str to numeric"
        },
        # 3.5 Normalize Salary
        {
            "op": "normalize",
            "params": {"columns": ["salary"]},
            "desc": "Normalizing salary"
        },
        # 3.6 KNN Impute Age
        {
            "op": "knn_impute",
            "params": {"columns": ["age"], "n_neighbors": 3},
            "desc": "Imputing Age with KNN"
        },
        # 3.7 Filter Rows (Age > 20)
        {
            "op": "filter_rows",
            "params": {"condition": "age > 20"},
            "desc": "Filtering rows where age > 20"
        }
    ]

    for i, step in enumerate(steps):
        log(f"  Step {i+1}: {step['desc']}...", "blue")
        res = session.post(
            f"{BASE_URL}/pipelines/interactive/{dataset_id}/steps",
            json={"operation": step["op"], "params": step["params"]},
            headers=headers
        )
        
        if res.status_code != 200:
            log(f"  Step failed: {res.text}", "red")
            sys.exit(1)
        
        data = res.json()
        row_count = data["row_count"]
        log(f"  Success! Rows remaining: {row_count}", "green")

    # 4. Verify Preview
    log("4. Verifying final preview...", "blue")
    res = session.get(f"{BASE_URL}/pipelines/interactive/{dataset_id}", headers=headers)
    preview = res.json()["preview"]
    if len(preview) > 0:
        log("Preview data received correctly", "green")
        print(json.dumps(preview[0], indent=2))
    else:
        log("Preview is empty!", "red")

    # 5. Export
    log("5. Exporting dataset...", "blue")
    # We need to send the steps again for export endpoint as currently designed
    # Or rely on the saved state if we update the export endpoint to use draft pipeline
    # The current export endpoint takes steps in body.
    
    # Let's fetch the current steps from the interactive endpoint first to be sure
    current_steps_res = session.get(f"{BASE_URL}/pipelines/interactive/{dataset_id}", headers=headers)
    saved_steps = current_steps_res.json()["steps"]
    
    # Transform to schema expected by export endpoint (list of objects with operation, params)
    # The saved_steps are already in that format mostly, just need to ensure keys match
    export_steps = []
    for s in saved_steps:
        export_steps.append({
            "operation": s["operation"],
            "params": s["params"]
        })

    res = session.post(
        f"{BASE_URL}/datasets/{dataset_id}/export",
        json=export_steps,
        params={"export_format": "csv"},
        headers=headers
    )

    if res.status_code != 200:
        log(f"Export failed: {res.text}", "red")
        sys.exit(1)
    
    download_url = res.json()["download_url"]
    log(f"Export successful! Download URL: {download_url}", "green")

    # 6. Download File
    log("6. Downloading file...", "blue")
    res = session.get(f"http://127.0.0.1:8000{download_url}", headers=headers)
    if res.status_code == 200:
        log("File downloaded successfully!", "green")
        log(f"Content Preview:\n{res.text[:200]}...", "white")
    else:
        log("Download failed", "red")

if __name__ == "__main__":
    test_pipeline()
