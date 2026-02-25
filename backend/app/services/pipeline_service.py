import pandas as pd
import numpy as np
import hashlib
import json
from sklearn.impute import KNNImputer
from typing import Dict, Any, List, Optional
from num2words import num2words
from word2number import w2n

STRICT_MODE = True

class TypeMutationError(Exception):
    pass

class InvalidColumnTypeError(Exception):
    pass

class ReplayConflictError(Exception):
    pass

class ChecksumMismatchError(Exception):
    pass

class DuplicateStepIDError(ValueError):
    pass

class PipelineSchemaError(ValueError):
    pass

class DeterminismMismatchError(Exception):
    pass

def execute_step(df: pd.DataFrame, step: Dict[str, Any], context: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
    # Support both old format (direct dict) and new format (nested in step object)
    operation = step.get("operation")
    params = step.get("params", {})
    
    # Checksum validation if present
    if "parameter_checksum" in step and step["parameter_checksum"]:
        current_checksum = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
        if current_checksum != step["parameter_checksum"]:
            raise ChecksumMismatchError(f"Step {step.get('step_id')} integrity check failed")

    context = context or {}

    # Strict Column Validation
    target_columns = params.get("columns", [])
    if target_columns:
        # Check if columns is a list, if it's None or empty skip
        if isinstance(target_columns, list):
            missing_cols = [c for c in target_columns if c not in df.columns]
            if missing_cols:
                 raise ReplayConflictError(f"Columns {missing_cols} missing for operation '{operation}'")
        elif target_columns is None:
            # Some operations might send None for columns if optional
            pass

    # Capture types before
    types_before = df.dtypes.apply(lambda x: str(x)).to_dict()

    if operation == "drop_missing":
        columns = params.get("columns")
        if columns:
            df = df.dropna(subset=columns)
        else:
            df = df.dropna()
    
    elif operation == "fill_missing":
        columns = params.get("columns")
        value = params.get("value")
        method = params.get("method") # mean, median, mode, constant
        
        for col in columns:
            if method == "constant":
                df[col] = df[col].fillna(value)
            elif method == "mean":
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
            elif method == "median":
                 if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
            elif method == "mode":
                mode_val = df[col].mode()
                if not mode_val.empty:
                    df[col] = df[col].fillna(mode_val[0])

    elif operation == "knn_impute":
        columns = params.get("columns", [])
        n_neighbors = int(params.get("n_neighbors", 5))
        if columns:
            # KNN only works on numeric data. We filter columns to ensure safety.
            numeric_cols = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
            if numeric_cols:
                imputer = KNNImputer(n_neighbors=n_neighbors)
                # KNNImputer returns a numpy array, need to assign back carefully
                imputed_data = imputer.fit_transform(df[numeric_cols])
                df[numeric_cols] = imputed_data

    elif operation == "drop_duplicates":
        subset = params.get("columns", None) # Optional subset of columns to check
        if subset == []: subset = None
        df = df.drop_duplicates(subset=subset)

    elif operation == "text_case":
        columns = params.get("columns", [])
        case_type = params.get("case", "lower") # lower, upper, title
        for col in columns:
            if col in df.columns and pd.api.types.is_string_dtype(df[col]):
                if case_type == "lower":
                    df[col] = df[col].str.lower()
                elif case_type == "upper":
                    df[col] = df[col].str.upper()
                elif case_type == "title":
                    df[col] = df[col].str.title()

    elif operation == "convert_type":
        columns = params.get("columns", [])
        target_type = params.get("type") # numeric, date, string, numeric_to_text, text_to_numeric
        for col in columns:
            if col in df.columns:
                if target_type == "numeric":
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                elif target_type == "date":
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                elif target_type == "string":
                    df[col] = df[col].astype(str)
                elif target_type == "numeric_to_text":
                    # 1 -> "one"
                    if pd.api.types.is_numeric_dtype(df[col]):
                        df[col] = df[col].apply(lambda x: num2words(x) if pd.notnull(x) else x)
                elif target_type == "text_to_numeric":
                    # "one" -> 1
                    # Handle mixed types: if already numeric, keep it. If string, try word_to_num.
                    def convert_mixed(x):
                        if pd.isnull(x): return np.nan
                        if isinstance(x, (int, float)): return x
                        try:
                            # Try simple numeric conversion first (e.g. "123")
                            return float(x)
                        except ValueError:
                            pass
                        try:
                            # Try word to number (e.g. "one hundred")
                            return w2n.word_to_num(str(x))
                        except ValueError:
                            return np.nan # Or keep original? Request implies conversion to numeric, so NaN if fail.

                    df[col] = df[col].apply(convert_mixed)

    elif operation == "round_numeric":
        columns = params.get("columns", [])
        decimals = int(params.get("decimals", 2))
        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].round(decimals)

    elif operation == "regex_filter":
        column = params.get("column")
        pattern = params.get("pattern")
        keep_matches = params.get("keep_matches", True)
        if column and pattern and column in df.columns:
            matches = df[column].astype(str).str.contains(pattern, regex=True, na=False)
            if keep_matches:
                df = df[matches]
            else:
                df = df[~matches]

    elif operation == "normalize":
        # Min-Max Scaling
        columns = params.get("columns", [])
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val != min_val:
                    df[col] = (df[col] - min_val) / (max_val - min_val)
    
    elif operation == "rename_columns":
        mapping = params.get("mapping", {})
        df = df.rename(columns=mapping)
    
    elif operation == "drop_columns":
        columns = params.get("columns", [])
        df = df.drop(columns=columns, errors='ignore')

    elif operation == "filter_rows":
        condition = params.get("condition") # e.g. "age > 30"
        if condition:
            try:
                df = df.query(condition)
            except Exception:
                pass # Ignore invalid queries for now to prevent crash
    
    elif operation == "merge":
        # Supports 'inner', 'left', 'right', 'outer'
        # Expects: secondary_dataset_id, how, left_on, right_on
        secondary_id = params.get("secondary_dataset_id")
        how = params.get("how", "inner")
        left_on = params.get("left_on")
        right_on = params.get("right_on")
        
        if secondary_id and secondary_id in context:
            other_df = context[secondary_id]
            
            # If keys are same, we can use 'on'. If different, left_on/right_on
            if left_on and right_on:
                # Ensure keys exist
                if left_on in df.columns and right_on in other_df.columns:
                    # Rename overlapping columns to avoid collision if not joining on them
                    # Pandas adds suffixes automatically (_x, _y), but let's be explicit if needed?
                    # Default suffixes are fine for now.
                    df = pd.merge(df, other_df, left_on=left_on, right_on=right_on, how=how)
            elif left_on and left_on in df.columns and left_on in other_df.columns:
                 # Assume same key name
                 df = pd.merge(df, other_df, on=left_on, how=how)
                 
    elif operation == "concat":
        # Vertical concatenation (Union)
        secondary_id = params.get("secondary_dataset_id")
        axis = params.get("axis", 0) # 0 for rows, 1 for cols
        
        if secondary_id and secondary_id in context:
            other_df = context[secondary_id]
            df = pd.concat([df, other_df], axis=axis, ignore_index=True)

    # Post-Execution Type Check
    types_after = df.dtypes.apply(lambda x: str(x)).to_dict()
    
    # We allow intentional type conversions
    if operation != "convert_type":
        for col, dtype_pre in types_before.items():
            if col in types_after:
                dtype_post = types_after[col]
                # Allow float->float, int->int, object->object
                # But flag float->object (unless intentional) or int->float (maybe ok for NaNs but risky)
                
                # Critical: Silent mutation float->object (e.g. fillna with string)
                if "float" in dtype_pre and "object" in dtype_post:
                    if STRICT_MODE:
                         raise TypeMutationError(f"Implicit cast forbidden: {col} changed from {dtype_pre} to {dtype_post}")
    
    return df

def execute_pipeline(df: pd.DataFrame, steps: List[Dict[str, Any]], context: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
    # Validate Pipeline Schema
    step_ids = [s.get("step_id") for s in steps if s.get("step_id")]
    if len(step_ids) != len(set(step_ids)):
        raise DuplicateStepIDError("Pipeline contains duplicate step IDs")

    for step in steps:
        # Validate Required Fields
        if "operation" not in step:
            raise PipelineSchemaError("Step missing required field 'operation'")
            
        df = execute_step(df, step, context)
    return df
