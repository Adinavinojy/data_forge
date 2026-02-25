import pandas as pd
import json
from app.services.dataset_service import check_quality_alerts
from app.services.pipeline_service import execute_step

def test_mixed_type_handling():
    print("--- Loading Mixed Type Dataset ---")
    df = pd.read_csv("tests/data/mixed_type_dataset.csv")
    print("Original Data:\n", df)
    
    print("\n--- Checking Quality Alerts ---")
    alerts = check_quality_alerts(df)
    print("Alerts Detected:", json.dumps(alerts, indent=2))
    
    # We expect alerts for 'age_mixed' (mostly numeric) and 'score_mixed' (mostly worded)
    
    print("\n--- Executing Auto-Conversion (Text to Numeric) for 'age_mixed' ---")
    step_age = {
        "operation": "convert_type",
        "params": {
            "columns": ["age_mixed"],
            "type": "text_to_numeric"
        }
    }
    df = execute_step(df, step_age)
    print("After Age Conversion:\n", df['age_mixed'])
    
    print("\n--- Executing Auto-Conversion (Text to Numeric) for 'score_mixed' ---")
    step_score = {
        "operation": "convert_type",
        "params": {
            "columns": ["score_mixed"],
            "type": "text_to_numeric"
        }
    }
    df = execute_step(df, step_score)
    print("After Score Conversion:\n", df['score_mixed'])
    
    # Verification
    is_age_numeric = pd.api.types.is_numeric_dtype(df['age_mixed'])
    is_score_numeric = pd.api.types.is_numeric_dtype(df['score_mixed'])
    
    if is_age_numeric and is_score_numeric:
        print("\n✅ SUCCESS: Both columns successfully converted to numeric!")
    else:
        print("\n❌ FAILURE: Conversion incomplete.")

if __name__ == "__main__":
    test_mixed_type_handling()
