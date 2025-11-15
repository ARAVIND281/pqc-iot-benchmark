"""
PQC IoT Benchmark - Correlation Analysis
========================================

Computes Pearson correlation matrix between all metrics
to identify trade-offs and relationships.

Author: PQC-IoT Research Team
Date: March 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import (
    SUMMARY_STATS_FILE, CORRELATION_MATRIX_FILE, FIGURES_DIR
)


def load_summary_stats(filepath: Path = None) -> pd.DataFrame:
    """Load summary statistics data."""
    if filepath is None:
        filepath = SUMMARY_STATS_FILE
    
    print(f"Loading summary statistics from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df):,} rows")
    return df


def prepare_correlation_data(stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for correlation analysis.
    
    Pivots the summary statistics to have one row per configuration
    and columns for each metric's mean value.
    
    Args:
        stats_df: Summary statistics DataFrame
        
    Returns:
        DataFrame with metrics as columns
    """
    # Filter to mean values only
    mean_df = stats_df[['algorithm', 'device_class', 'metric', 'mean']].copy()
    
    # Pivot to wide format
    pivot_df = mean_df.pivot_table(
        index=['algorithm', 'device_class'],
        columns='metric',
        values='mean'
    ).reset_index()
    
    print(f"Prepared correlation data: {len(pivot_df)} configurations")
    return pivot_df


def compute_correlation_matrix(
    df: pd.DataFrame,
    metrics: List[str] = None
) -> pd.DataFrame:
    """
    Compute Pearson correlation matrix.
    
    Args:
        df: DataFrame with metrics as columns
        metrics: List of metric columns to include
        
    Returns:
        Correlation matrix DataFrame
    """
    if metrics is None:
        # Default metrics to analyze
        metrics = [
            'keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms',
            'total_time_ms', 'peak_memory_kb', 'energy_mj',
            'pubkey_size_bytes', 'seckey_size_bytes', 'ct_size_bytes'
        ]
    
    # Filter to available metrics
    available_metrics = [m for m in metrics if m in df.columns]
    
    if len(available_metrics) < 2:
        print("Warning: Less than 2 metrics available for correlation")
        return pd.DataFrame()
    
    # Compute correlation matrix
    corr_matrix = df[available_metrics].corr(method='pearson')
    
    print(f"\nComputed correlation matrix for {len(available_metrics)} metrics")
    
    return corr_matrix


def identify_significant_correlations(
    corr_matrix: pd.DataFrame,
    threshold: float = 0.7
) -> Dict[str, List[Tuple[str, str, float]]]:
    """
    Identify strong positive and negative correlations.
    
    Args:
        corr_matrix: Correlation matrix
        threshold: Absolute correlation threshold
        
    Returns:
        Dictionary with 'positive' and 'negative' correlation lists
    """
    positive = []
    negative = []
    
    for i, row_metric in enumerate(corr_matrix.index):
        for j, col_metric in enumerate(corr_matrix.columns):
            if i >= j:  # Skip diagonal and lower triangle
                continue
            
            corr = corr_matrix.loc[row_metric, col_metric]
            
            if corr >= threshold:
                positive.append((row_metric, col_metric, corr))
            elif corr <= -threshold:
                negative.append((row_metric, col_metric, corr))
    
    # Sort by absolute correlation
    positive.sort(key=lambda x: -x[2])
    negative.sort(key=lambda x: x[2])
    
    return {
        'positive': positive,
        'negative': negative
    }


def print_correlation_insights(
    corr_matrix: pd.DataFrame,
    significant: Dict[str, List]
) -> None:
    """Print insights from correlation analysis."""
    print("\n" + "=" * 60)
    print("CORRELATION ANALYSIS INSIGHTS")
    print("=" * 60)
    
    # Print matrix
    print("\nCorrelation Matrix (Pearson):")
    print("-" * 60)
    
    # Format for better readability
    formatted = corr_matrix.round(3)
    print(formatted.to_string())
    
    # Print significant correlations
    print("\n" + "-" * 60)
    print("Strong Positive Correlations (r ≥ 0.7):")
    if significant['positive']:
        for metric1, metric2, corr in significant['positive']:
            print(f"  {metric1} ↔ {metric2}: r = {corr:.3f}")
    else:
        print("  None found")
    
    print("\nStrong Negative Correlations (r ≤ -0.7):")
    if significant['negative']:
        for metric1, metric2, corr in significant['negative']:
            print(f"  {metric1} ↔ {metric2}: r = {corr:.3f}")
    else:
        print("  None found")
    
    # Trade-off analysis
    print("\n" + "-" * 60)
    print("Key Trade-offs Identified:")
    
    # Check for speed vs size trade-offs
    time_cols = ['keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms', 'total_time_ms']
    size_cols = ['pubkey_size_bytes', 'seckey_size_bytes', 'ct_size_bytes']
    
    for time_col in time_cols:
        for size_col in size_cols:
            if time_col in corr_matrix.index and size_col in corr_matrix.columns:
                corr = corr_matrix.loc[time_col, size_col]
                if abs(corr) >= 0.5:
                    direction = "positive" if corr > 0 else "negative"
                    print(f"  {time_col} vs {size_col}: {direction} (r = {corr:.3f})")


def run_correlation_analysis(
    input_file: Path = None,
    output_file: Path = None
) -> pd.DataFrame:
    """
    Run full correlation analysis pipeline.
    
    Args:
        input_file: Path to summary statistics
        output_file: Path for correlation matrix output
        
    Returns:
        Correlation matrix DataFrame
    """
    if input_file is None:
        input_file = SUMMARY_STATS_FILE
    if output_file is None:
        output_file = CORRELATION_MATRIX_FILE
    
    print("=" * 60)
    print("CORRELATION ANALYSIS")
    print("=" * 60)
    
    # Load summary statistics
    stats_df = load_summary_stats(input_file)
    
    # Prepare data
    corr_data = prepare_correlation_data(stats_df)
    
    # Compute correlation matrix
    corr_matrix = compute_correlation_matrix(corr_data)
    
    if len(corr_matrix) == 0:
        print("Error: Could not compute correlation matrix")
        return pd.DataFrame()
    
    # Save correlation matrix
    output_file.parent.mkdir(parents=True, exist_ok=True)
    corr_matrix.to_csv(output_file)
    print(f"\n✓ Correlation matrix saved to: {output_file}")
    
    # Identify significant correlations
    significant = identify_significant_correlations(corr_matrix)
    
    # Print insights
    print_correlation_insights(corr_matrix, significant)
    
    return corr_matrix


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run correlation analysis')
    parser.add_argument('--input', type=str, help='Input statistics file')
    parser.add_argument('--output', type=str, help='Output correlation matrix file')
    
    args = parser.parse_args()
    
    input_file = Path(args.input) if args.input else None
    output_file = Path(args.output) if args.output else None
    
    run_correlation_analysis(input_file, output_file)


if __name__ == "__main__":
    main()
