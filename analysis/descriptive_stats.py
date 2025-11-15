"""
PQC IoT Benchmark - Descriptive Statistics
==========================================

Computes summary statistics for benchmark data:
- Mean, median, std, min, max
- Quartiles (Q1, Q3, IQR)
- Coefficient of variation

Author: PQC-IoT Research Team
Date: March 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import CLEANED_BENCHMARKS_FILE, SUMMARY_STATS_FILE


def load_cleaned_data(filepath: Path = None) -> pd.DataFrame:
    """
    Load cleaned benchmark data.
    
    Args:
        filepath: Path to cleaned CSV file
        
    Returns:
        DataFrame with cleaned benchmark data
    """
    if filepath is None:
        filepath = CLEANED_BENCHMARKS_FILE
    
    print(f"Loading cleaned data from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df):,} rows")
    return df


def compute_statistics(
    df: pd.DataFrame,
    group_cols: List[str] = None,
    value_cols: List[str] = None
) -> pd.DataFrame:
    """
    Compute descriptive statistics for grouped data.
    
    Args:
        df: DataFrame with benchmark data
        group_cols: Columns to group by
        value_cols: Columns to compute statistics for
        
    Returns:
        DataFrame with statistics
    """
    if group_cols is None:
        group_cols = ['algorithm', 'family', 'type', 'security_level', 'device_class']
    
    if value_cols is None:
        value_cols = [
            'keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms',
            'total_time_ms', 'peak_memory_kb', 'energy_mj',
            'pubkey_size_bytes', 'seckey_size_bytes', 'ct_size_bytes'
        ]
    
    # Filter to only existing columns
    value_cols = [c for c in value_cols if c in df.columns]
    group_cols = [c for c in group_cols if c in df.columns]
    
    print(f"\nComputing statistics for {len(value_cols)} metrics...")
    print(f"Grouped by: {group_cols}")
    
    # Define aggregation functions
    def iqr(x):
        return x.quantile(0.75) - x.quantile(0.25)
    
    def cv(x):
        """Coefficient of variation (std / mean)"""
        mean = x.mean()
        if mean == 0:
            return 0
        return x.std() / mean
    
    agg_funcs = {
        'count': 'count',
        'mean': 'mean',
        'median': 'median',
        'std': 'std',
        'min': 'min',
        'max': 'max',
        'q1': lambda x: x.quantile(0.25),
        'q3': lambda x: x.quantile(0.75),
        'iqr': iqr,
        'cv': cv
    }
    
    results = []
    
    for col in value_cols:
        print(f"  Processing: {col}")
        
        # Group and aggregate
        grouped = df.groupby(group_cols)[col].agg(list(agg_funcs.values()))
        grouped.columns = [f"{name}" for name in agg_funcs.keys()]
        grouped = grouped.reset_index()
        grouped['metric'] = col
        
        results.append(grouped)
    
    # Combine all metrics
    stats_df = pd.concat(results, ignore_index=True)
    
    # Reorder columns
    cols = ['metric'] + group_cols + list(agg_funcs.keys())
    stats_df = stats_df[cols]
    
    print(f"\nGenerated statistics for {len(stats_df)} configurations")
    
    return stats_df


def compute_summary_tables(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Generate summary tables for the paper.
    
    Returns:
        Dictionary of summary tables
    """
    print("\nGenerating summary tables for paper...")
    
    tables = {}
    
    # Table I: KEM Algorithm Performance
    kem_df = df[df['type'] == 'kem'].copy()
    if len(kem_df) > 0:
        kem_stats = compute_statistics(
            kem_df,
            group_cols=['algorithm', 'device_class'],
            value_cols=['keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms',
                       'peak_memory_kb', 'energy_mj']
        )
        tables['kem_performance'] = kem_stats
        print(f"  Table I (KEM): {len(kem_stats)} rows")
    
    # Table II: Signature Algorithm Performance
    sig_df = df[df['type'] == 'signature'].copy()
    if len(sig_df) > 0:
        sig_stats = compute_statistics(
            sig_df,
            group_cols=['algorithm', 'device_class'],
            value_cols=['keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms',
                       'peak_memory_kb', 'energy_mj']
        )
        tables['signature_performance'] = sig_stats
        print(f"  Table II (Signature): {len(sig_stats)} rows")
    
    # Table IV: Key and Ciphertext Sizes (static - doesn't vary by device)
    size_cols = ['pubkey_size_bytes', 'seckey_size_bytes', 'ct_size_bytes']
    size_stats = df.groupby(['algorithm', 'family', 'type', 'security_level'])[size_cols].first().reset_index()
    tables['key_sizes'] = size_stats
    print(f"  Table IV (Sizes): {len(size_stats)} rows")
    
    return tables


def pivot_for_comparison(
    stats_df: pd.DataFrame,
    metric: str,
    stat: str = 'mean'
) -> pd.DataFrame:
    """
    Pivot statistics for algorithm x device class comparison.
    
    Args:
        stats_df: Statistics DataFrame
        metric: Metric to pivot (e.g., 'keygen_time_ms')
        stat: Statistic to show (e.g., 'mean', 'median')
        
    Returns:
        Pivoted DataFrame
    """
    metric_df = stats_df[stats_df['metric'] == metric].copy()
    
    pivot = metric_df.pivot_table(
        index='algorithm',
        columns='device_class',
        values=stat,
        aggfunc='first'
    )
    
    # Reorder columns
    class_order = ['Class 0', 'Class 1', 'Class 2']
    pivot = pivot[[c for c in class_order if c in pivot.columns]]
    
    return pivot


def generate_latex_table(
    df: pd.DataFrame,
    caption: str,
    label: str
) -> str:
    """
    Generate LaTeX table from DataFrame.
    
    Args:
        df: DataFrame to convert
        caption: Table caption
        label: Table label for referencing
        
    Returns:
        LaTeX table string
    """
    latex = df.to_latex(
        index=True,
        float_format="%.2f",
        caption=caption,
        label=label,
        position='htbp'
    )
    return latex


def run_descriptive_analysis(
    input_file: Path = None,
    output_file: Path = None
) -> pd.DataFrame:
    """
    Run full descriptive analysis pipeline.
    
    Args:
        input_file: Path to cleaned data
        output_file: Path for statistics output
        
    Returns:
        Statistics DataFrame
    """
    if input_file is None:
        input_file = CLEANED_BENCHMARKS_FILE
    if output_file is None:
        output_file = SUMMARY_STATS_FILE
    
    print("=" * 60)
    print("DESCRIPTIVE STATISTICS ANALYSIS")
    print("=" * 60)
    
    # Load data
    df = load_cleaned_data(input_file)
    
    # Filter successful runs only
    if 'status' in df.columns:
        success_df = df[df['status'] == 'SUCCESS'].copy()
        print(f"Filtering to successful runs: {len(success_df):,} / {len(df):,}")
    else:
        success_df = df
    
    # Compute full statistics
    stats_df = compute_statistics(success_df)
    
    # Save statistics
    output_file.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(output_file, index=False)
    print(f"\n✓ Statistics saved to: {output_file}")
    
    # Generate summary tables
    tables = compute_summary_tables(success_df)
    
    # Save individual tables
    for name, table in tables.items():
        table_file = output_file.parent / f"table_{name}.csv"
        table.to_csv(table_file, index=False)
        print(f"✓ Table saved: {table_file}")
    
    # Print sample pivot tables
    print("\n" + "=" * 60)
    print("SAMPLE COMPARISON: Mean Key Generation Time (ms)")
    print("=" * 60)
    
    keygen_pivot = pivot_for_comparison(stats_df, 'keygen_time_ms', 'mean')
    print(keygen_pivot.round(3).to_string())
    
    print("\n" + "=" * 60)
    print("SAMPLE COMPARISON: Mean Energy Consumption (mJ)")
    print("=" * 60)
    
    energy_pivot = pivot_for_comparison(stats_df, 'energy_mj', 'mean')
    print(energy_pivot.round(4).to_string())
    
    return stats_df


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute descriptive statistics')
    parser.add_argument('--input', type=str, help='Input CSV file')
    parser.add_argument('--output', type=str, help='Output CSV file')
    
    args = parser.parse_args()
    
    input_file = Path(args.input) if args.input else None
    output_file = Path(args.output) if args.output else None
    
    run_descriptive_analysis(input_file, output_file)


if __name__ == "__main__":
    main()
