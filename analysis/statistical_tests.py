"""
PQC IoT Benchmark - Statistical Tests
=====================================

Performs statistical significance testing:
- One-way ANOVA for each metric across algorithms
- Post-hoc Tukey HSD tests for pairwise comparisons

Author: PQC-IoT Research Team
Date: March 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import (
    CLEANED_BENCHMARKS_FILE, ANOVA_RESULTS_FILE, TUKEY_RESULTS_FILE,
    SIGNIFICANCE_LEVEL
)


def load_cleaned_data(filepath: Path = None) -> pd.DataFrame:
    """Load cleaned benchmark data."""
    if filepath is None:
        filepath = CLEANED_BENCHMARKS_FILE
    
    print(f"Loading data from: {filepath}")
    df = pd.read_csv(filepath)
    
    # Filter to successful runs
    if 'status' in df.columns:
        df = df[df['status'] == 'SUCCESS']
    
    print(f"Loaded {len(df):,} successful benchmark runs")
    return df


def run_anova(
    df: pd.DataFrame,
    metric: str,
    group_col: str = 'algorithm'
) -> Dict[str, Any]:
    """
    Run one-way ANOVA for a metric across groups.
    
    Args:
        df: DataFrame with benchmark data
        metric: Column name for the metric to test
        group_col: Column name for grouping
        
    Returns:
        Dictionary with ANOVA results
    """
    # Get groups
    groups = df.groupby(group_col)[metric].apply(list).to_dict()
    group_names = list(groups.keys())
    
    if len(group_names) < 2:
        return {
            'metric': metric,
            'group_col': group_col,
            'n_groups': len(group_names),
            'f_statistic': np.nan,
            'p_value': np.nan,
            'significant': False,
            'error': 'Less than 2 groups'
        }
    
    # Perform ANOVA
    try:
        f_stat, p_value = stats.f_oneway(*[groups[g] for g in group_names])
        
        return {
            'metric': metric,
            'group_col': group_col,
            'n_groups': len(group_names),
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < SIGNIFICANCE_LEVEL,
            'error': None
        }
    except Exception as e:
        return {
            'metric': metric,
            'group_col': group_col,
            'n_groups': len(group_names),
            'f_statistic': np.nan,
            'p_value': np.nan,
            'significant': False,
            'error': str(e)
        }


def run_tukey_hsd(
    df: pd.DataFrame,
    metric: str,
    group_col: str = 'algorithm'
) -> pd.DataFrame:
    """
    Run Tukey HSD post-hoc test for pairwise comparisons.
    
    Args:
        df: DataFrame with benchmark data
        metric: Column name for the metric to test
        group_col: Column name for grouping
        
    Returns:
        DataFrame with Tukey HSD results
    """
    try:
        tukey_result = pairwise_tukeyhsd(
            endog=df[metric],
            groups=df[group_col],
            alpha=SIGNIFICANCE_LEVEL
        )
        
        # Convert to DataFrame
        results_df = pd.DataFrame({
            'group1': tukey_result.groupsunique[tukey_result.pairindices[:, 0]],
            'group2': tukey_result.groupsunique[tukey_result.pairindices[:, 1]],
            'meandiff': tukey_result.meandiffs,
            'p_adj': tukey_result.pvalues,
            'lower': tukey_result.confint[:, 0],
            'upper': tukey_result.confint[:, 1],
            'reject': tukey_result.reject
        })
        
        results_df['metric'] = metric
        results_df['group_col'] = group_col
        
        return results_df
        
    except Exception as e:
        print(f"  Warning: Tukey HSD failed for {metric}: {e}")
        return pd.DataFrame()


def run_statistical_tests(
    df: pd.DataFrame,
    metrics: List[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run all statistical tests for benchmark data.
    
    Args:
        df: DataFrame with benchmark data
        metrics: List of metrics to test
        
    Returns:
        Tuple of (ANOVA results, Tukey results)
    """
    if metrics is None:
        metrics = [
            'keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms',
            'total_time_ms', 'peak_memory_kb', 'energy_mj'
        ]
    
    # Filter to available metrics
    metrics = [m for m in metrics if m in df.columns]
    
    device_classes = df['device_class'].unique()
    
    print(f"\nRunning statistical tests:")
    print(f"  Metrics: {len(metrics)}")
    print(f"  Device classes: {list(device_classes)}")
    print(f"  Significance level: α = {SIGNIFICANCE_LEVEL}")
    
    anova_results = []
    tukey_results = []
    
    for device_class in device_classes:
        print(f"\n{device_class}:")
        class_df = df[df['device_class'] == device_class]
        
        for metric in metrics:
            # Run ANOVA
            anova_result = run_anova(class_df, metric)
            anova_result['device_class'] = device_class
            anova_results.append(anova_result)
            
            sig = "✓" if anova_result['significant'] else "✗"
            print(f"  {metric}: F={anova_result['f_statistic']:.2f}, "
                  f"p={anova_result['p_value']:.4f} {sig}")
            
            # Run Tukey HSD if ANOVA is significant
            if anova_result['significant']:
                tukey_df = run_tukey_hsd(class_df, metric)
                if len(tukey_df) > 0:
                    tukey_df['device_class'] = device_class
                    tukey_results.append(tukey_df)
    
    # Combine results
    anova_df = pd.DataFrame(anova_results)
    tukey_df = pd.concat(tukey_results, ignore_index=True) if tukey_results else pd.DataFrame()
    
    return anova_df, tukey_df


def summarize_anova_results(anova_df: pd.DataFrame) -> None:
    """Print summary of ANOVA results."""
    print("\n" + "=" * 60)
    print("ANOVA RESULTS SUMMARY")
    print("=" * 60)
    
    # Count significant results
    sig_count = anova_df['significant'].sum()
    total = len(anova_df)
    
    print(f"\nSignificant results: {sig_count}/{total} ({sig_count/total*100:.1f}%)")
    
    # Group by device class
    for device_class in anova_df['device_class'].unique():
        class_df = anova_df[anova_df['device_class'] == device_class]
        sig_metrics = class_df[class_df['significant']]['metric'].tolist()
        
        print(f"\n{device_class}:")
        if sig_metrics:
            print(f"  Significant differences found in: {', '.join(sig_metrics)}")
        else:
            print(f"  No significant differences found")


def summarize_tukey_results(tukey_df: pd.DataFrame) -> None:
    """Print summary of Tukey HSD results."""
    if len(tukey_df) == 0:
        print("\nNo Tukey HSD results (no significant ANOVA results)")
        return
    
    print("\n" + "=" * 60)
    print("SIGNIFICANT PAIRWISE DIFFERENCES (Tukey HSD)")
    print("=" * 60)
    
    # Filter to significant differences
    sig_df = tukey_df[tukey_df['reject'] == True]
    
    if len(sig_df) == 0:
        print("\nNo significant pairwise differences found")
        return
    
    for device_class in sig_df['device_class'].unique():
        print(f"\n{device_class}:")
        class_df = sig_df[sig_df['device_class'] == device_class]
        
        for metric in class_df['metric'].unique():
            metric_df = class_df[class_df['metric'] == metric]
            print(f"\n  {metric}:")
            
            for _, row in metric_df.iterrows():
                direction = ">" if row['meandiff'] > 0 else "<"
                print(f"    {row['group1']} {direction} {row['group2']} "
                      f"(diff={row['meandiff']:.3f}, p={row['p_adj']:.4f})")


def run_analysis(
    input_file: Path = None,
    anova_output: Path = None,
    tukey_output: Path = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run full statistical analysis pipeline.
    
    Args:
        input_file: Path to cleaned data
        anova_output: Path for ANOVA results
        tukey_output: Path for Tukey results
        
    Returns:
        Tuple of (ANOVA DataFrame, Tukey DataFrame)
    """
    if input_file is None:
        input_file = CLEANED_BENCHMARKS_FILE
    if anova_output is None:
        anova_output = ANOVA_RESULTS_FILE
    if tukey_output is None:
        tukey_output = TUKEY_RESULTS_FILE
    
    print("=" * 60)
    print("STATISTICAL SIGNIFICANCE TESTING")
    print("=" * 60)
    
    # Load data
    df = load_cleaned_data(input_file)
    
    # Run tests
    anova_df, tukey_df = run_statistical_tests(df)
    
    # Save results
    anova_output.parent.mkdir(parents=True, exist_ok=True)
    anova_df.to_csv(anova_output, index=False)
    print(f"\n✓ ANOVA results saved to: {anova_output}")
    
    if len(tukey_df) > 0:
        tukey_df.to_csv(tukey_output, index=False)
        print(f"✓ Tukey HSD results saved to: {tukey_output}")
    
    # Print summaries
    summarize_anova_results(anova_df)
    summarize_tukey_results(tukey_df)
    
    return anova_df, tukey_df


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical tests')
    parser.add_argument('--input', type=str, help='Input CSV file')
    parser.add_argument('--anova-output', type=str, help='ANOVA output file')
    parser.add_argument('--tukey-output', type=str, help='Tukey output file')
    
    args = parser.parse_args()
    
    input_file = Path(args.input) if args.input else None
    anova_output = Path(args.anova_output) if args.anova_output else None
    tukey_output = Path(args.tukey_output) if args.tukey_output else None
    
    run_analysis(input_file, anova_output, tukey_output)


if __name__ == "__main__":
    main()
