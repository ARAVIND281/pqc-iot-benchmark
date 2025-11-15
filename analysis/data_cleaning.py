"""
PQC IoT Benchmark - Data Cleaning
=================================

Cleans and validates benchmark data:
- Removes warmup iterations
- Detects and removes outliers using IQR method
- Validates data integrity

Author: PQC-IoT Research Team
Date: March 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import (
    RAW_BENCHMARKS_FILE, CLEANED_BENCHMARKS_FILE,
    WARMUP_ITERATIONS, ALGORITHMS, DEVICE_CLASSES
)


def load_raw_data(filepath: Path = None) -> pd.DataFrame:
    """
    Load raw benchmark data from CSV.
    
    Args:
        filepath: Path to raw CSV file (default: from config)
        
    Returns:
        DataFrame with raw benchmark data
    """
    if filepath is None:
        filepath = RAW_BENCHMARKS_FILE
    
    print(f"Loading raw data from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df):,} rows")
    return df


def remove_warmup_iterations(
    df: pd.DataFrame,
    warmup_count: int = WARMUP_ITERATIONS
) -> pd.DataFrame:
    """
    Remove warmup iterations from each configuration.
    
    Args:
        df: DataFrame with benchmark data
        warmup_count: Number of warmup iterations to remove
        
    Returns:
        DataFrame with warmup iterations removed
    """
    print(f"\nRemoving first {warmup_count} warmup iterations per configuration...")
    
    # Group by algorithm and device class, then filter
    groups = df.groupby(['algorithm', 'device_class'])
    
    cleaned_dfs = []
    for (algo, device), group in groups:
        # Keep only iterations after warmup
        cleaned = group[group['iteration'] > warmup_count].copy()
        cleaned_dfs.append(cleaned)
    
    result = pd.concat(cleaned_dfs, ignore_index=True)
    
    removed = len(df) - len(result)
    print(f"Removed {removed:,} warmup iterations ({removed/len(df)*100:.1f}%)")
    print(f"Remaining: {len(result):,} rows")
    
    return result


def detect_outliers_iqr(
    df: pd.DataFrame,
    columns: list,
    multiplier: float = 1.5
) -> pd.DataFrame:
    """
    Detect outliers using IQR method.
    
    Args:
        df: DataFrame with benchmark data
        columns: Columns to check for outliers
        multiplier: IQR multiplier (default: 1.5 for standard outliers)
        
    Returns:
        Boolean mask where True indicates an outlier row
    """
    outlier_mask = pd.Series(False, index=df.index)
    
    for col in columns:
        if col not in df.columns:
            continue
            
        # Calculate IQR per configuration (algorithm + device class)
        groups = df.groupby(['algorithm', 'device_class'])[col]
        
        Q1 = groups.transform('quantile', 0.25)
        Q3 = groups.transform('quantile', 0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_mask = outlier_mask | col_outliers
    
    return outlier_mask


def remove_outliers(
    df: pd.DataFrame,
    multiplier: float = 1.5
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Remove outliers from benchmark data using IQR method.
    
    Args:
        df: DataFrame with benchmark data
        multiplier: IQR multiplier for outlier detection
        
    Returns:
        Tuple of (cleaned DataFrame, outlier statistics)
    """
    print(f"\nDetecting outliers using IQR method (multiplier={multiplier})...")
    
    # Columns to check for outliers
    numeric_columns = [
        'keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms',
        'total_time_ms', 'peak_memory_kb', 'energy_mj'
    ]
    
    # Only check columns that exist
    columns_to_check = [c for c in numeric_columns if c in df.columns]
    
    # Detect outliers
    outlier_mask = detect_outliers_iqr(df, columns_to_check, multiplier)
    
    # Remove outliers
    cleaned_df = df[~outlier_mask].copy()
    
    # Calculate statistics
    total_outliers = outlier_mask.sum()
    outlier_pct = total_outliers / len(df) * 100
    
    # Per-configuration outlier counts
    outlier_df = df[outlier_mask]
    outliers_by_config = outlier_df.groupby(['algorithm', 'device_class']).size().to_dict()
    
    stats = {
        'total_rows': len(df),
        'outliers_removed': total_outliers,
        'outlier_percentage': outlier_pct,
        'remaining_rows': len(cleaned_df),
        'outliers_by_config': outliers_by_config
    }
    
    print(f"Outliers detected: {total_outliers:,} ({outlier_pct:.2f}%)")
    print(f"Remaining rows: {len(cleaned_df):,}")
    
    if outlier_pct > 5:
        print("⚠ Warning: Outlier percentage exceeds 5% - check data quality")
    
    return cleaned_df, stats


def validate_data(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate data integrity.
    
    Checks:
    - No negative values in timing/memory columns
    - No NaN values
    - All expected configurations present
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, validation_results)
    """
    print("\nValidating data integrity...")
    
    issues = []
    
    # Check for NaN values
    nan_counts = df.isnull().sum()
    nan_cols = nan_counts[nan_counts > 0]
    if len(nan_cols) > 0:
        issues.append(f"NaN values found in columns: {dict(nan_cols)}")
    
    # Check for negative values in numeric columns
    numeric_columns = [
        'keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms',
        'total_time_ms', 'peak_memory_kb', 'energy_mj'
    ]
    for col in numeric_columns:
        if col in df.columns:
            negative_count = (df[col] < 0).sum()
            # Allow -1 for failed operations
            real_negative = ((df[col] < 0) & (df[col] != -1)).sum()
            if real_negative > 0:
                issues.append(f"Unexpected negative values in {col}: {real_negative}")
    
    # Check expected configurations
    expected_algos = set(a.name for a in ALGORITHMS)
    found_algos = set(df['algorithm'].unique())
    missing_algos = expected_algos - found_algos
    if missing_algos:
        issues.append(f"Missing algorithms: {missing_algos}")
    
    expected_classes = set(d.name for d in DEVICE_CLASSES)
    found_classes = set(df['device_class'].unique())
    missing_classes = expected_classes - found_classes
    if missing_classes:
        issues.append(f"Missing device classes: {missing_classes}")
    
    # Count successful vs failed
    if 'status' in df.columns:
        status_counts = df['status'].value_counts().to_dict()
    else:
        status_counts = {}
    
    is_valid = len(issues) == 0
    
    results = {
        'is_valid': is_valid,
        'issues': issues,
        'row_count': len(df),
        'algorithms_found': list(found_algos),
        'device_classes_found': list(found_classes),
        'status_counts': status_counts
    }
    
    if is_valid:
        print("✓ Data validation passed")
    else:
        print("✗ Data validation failed:")
        for issue in issues:
            print(f"  - {issue}")
    
    return is_valid, results


def clean_data(
    input_file: Path = None,
    output_file: Path = None,
    remove_warmup: bool = True,
    remove_outliers_flag: bool = True
) -> pd.DataFrame:
    """
    Full data cleaning pipeline.
    
    Args:
        input_file: Path to raw data file
        output_file: Path for cleaned data output
        remove_warmup: Whether to remove warmup iterations
        remove_outliers_flag: Whether to remove outliers
        
    Returns:
        Cleaned DataFrame
    """
    if input_file is None:
        input_file = RAW_BENCHMARKS_FILE
    if output_file is None:
        output_file = CLEANED_BENCHMARKS_FILE
    
    print("=" * 60)
    print("DATA CLEANING PIPELINE")
    print("=" * 60)
    
    # Load raw data
    df = load_raw_data(input_file)
    
    # Remove warmup iterations
    if remove_warmup:
        df = remove_warmup_iterations(df)
    
    # Remove outliers
    if remove_outliers_flag:
        df, outlier_stats = remove_outliers(df)
    
    # Validate
    is_valid, validation_results = validate_data(df)
    
    # Save cleaned data
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"\n✓ Cleaned data saved to: {output_file}")
    print(f"  Final row count: {len(df):,}")
    
    return df


def main():
    """Main entry point for data cleaning."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean PQC benchmark data')
    parser.add_argument('--input', type=str, help='Input CSV file')
    parser.add_argument('--output', type=str, help='Output CSV file')
    parser.add_argument('--no-warmup', action='store_true', 
                       help='Skip warmup removal')
    parser.add_argument('--no-outliers', action='store_true',
                       help='Skip outlier removal')
    
    args = parser.parse_args()
    
    input_file = Path(args.input) if args.input else None
    output_file = Path(args.output) if args.output else None
    
    clean_data(
        input_file=input_file,
        output_file=output_file,
        remove_warmup=not args.no_warmup,
        remove_outliers_flag=not args.no_outliers
    )


if __name__ == "__main__":
    main()
