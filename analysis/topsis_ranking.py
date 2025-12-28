"""
PQC IoT Benchmark - TOPSIS Ranking
=================================

Applies TOPSIS (Technique for Order of Preference by Similarity
to Ideal Solution) for multi-criteria algorithm ranking.

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
    SUMMARY_STATS_FILE, TOPSIS_RANKINGS_FILE, FEASIBILITY_MATRIX_FILE,
    TOPSIS_WEIGHTS, DEVICE_CLASSES
)


def load_summary_stats(filepath: Path = None) -> pd.DataFrame:
    """Load summary statistics data."""
    if filepath is None:
        filepath = SUMMARY_STATS_FILE
    
    print(f"Loading summary statistics from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df):,} rows")
    return df


def prepare_decision_matrix(stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare decision matrix for TOPSIS analysis.
    
    Each row is a configuration (algorithm + device class),
    each column is a criterion (metric).
    
    Args:
        stats_df: Summary statistics DataFrame
        
    Returns:
        Decision matrix DataFrame
    """
    # Define criteria columns based on TOPSIS weights
    # Map weight keys to actual metric names
    criteria_mapping = {
        'total_time': 'total_time_ms',
        'memory': 'peak_memory_kb',
        'energy': 'energy_mj',
        'key_size': ['pubkey_size_bytes', 'seckey_size_bytes'],  # Combined
        'ct_size': 'ct_size_bytes'
    }
    
    # Filter to mean values
    mean_df = stats_df[['algorithm', 'device_class', 'metric', 'mean']].copy()
    
    # Pivot to wide format
    pivot_df = mean_df.pivot_table(
        index=['algorithm', 'device_class'],
        columns='metric',
        values='mean'
    ).reset_index()
    
    # Create combined key_size column if individual columns exist
    if 'pubkey_size_bytes' in pivot_df.columns and 'seckey_size_bytes' in pivot_df.columns:
        pivot_df['key_size_bytes'] = pivot_df['pubkey_size_bytes'] + pivot_df['seckey_size_bytes']
    
    print(f"Decision matrix: {len(pivot_df)} alternatives x {len(pivot_df.columns)-2} criteria")
    
    return pivot_df


def normalize_matrix(
    decision_matrix: pd.DataFrame,
    criteria: List[str]
) -> pd.DataFrame:
    """
    Normalize decision matrix using vector normalization.
    
    r_ij = x_ij / sqrt(sum(x_ij^2))
    
    Args:
        decision_matrix: Raw decision matrix
        criteria: List of criterion column names
        
    Returns:
        Normalized decision matrix
    """
    normalized = decision_matrix.copy()
    
    for criterion in criteria:
        if criterion not in normalized.columns:
            continue
        
        # Vector normalization
        sum_sq = np.sqrt((normalized[criterion] ** 2).sum())
        if sum_sq > 0:
            normalized[criterion] = normalized[criterion] / sum_sq
    
    return normalized


def apply_weights(
    normalized_matrix: pd.DataFrame,
    criteria: List[str],
    weights: Dict[str, float]
) -> pd.DataFrame:
    """
    Apply weights to normalized matrix.
    
    v_ij = w_j * r_ij
    
    Args:
        normalized_matrix: Normalized decision matrix
        criteria: List of criterion column names
        weights: Dictionary of criterion weights
        
    Returns:
        Weighted normalized matrix
    """
    weighted = normalized_matrix.copy()
    
    # Map criteria to weights
    criteria_to_weight = {
        'total_time_ms': weights.get('total_time', 0.25),
        'peak_memory_kb': weights.get('memory', 0.25),
        'energy_mj': weights.get('energy', 0.20),
        'key_size_bytes': weights.get('key_size', 0.15),
        'ct_size_bytes': weights.get('ct_size', 0.15)
    }
    
    for criterion in criteria:
        if criterion in weighted.columns and criterion in criteria_to_weight:
            weighted[criterion] = weighted[criterion] * criteria_to_weight[criterion]
    
    return weighted


def determine_ideal_solutions(
    weighted_matrix: pd.DataFrame,
    criteria: List[str],
    beneficial: List[str] = None
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Determine ideal best (A+) and ideal worst (A-) solutions.
    
    For cost criteria (lower is better): A+ = min, A- = max
    For benefit criteria (higher is better): A+ = max, A- = min
    
    In this benchmark, all metrics are cost criteria (lower is better).
    
    Args:
        weighted_matrix: Weighted normalized matrix
        criteria: List of criterion columns
        beneficial: List of beneficial criteria (higher is better)
        
    Returns:
        Tuple of (ideal_best, ideal_worst) dictionaries
    """
    if beneficial is None:
        beneficial = []  # All criteria are cost criteria
    
    ideal_best = {}
    ideal_worst = {}
    
    for criterion in criteria:
        if criterion not in weighted_matrix.columns:
            continue
        
        if criterion in beneficial:
            # Benefit criterion: higher is better
            ideal_best[criterion] = weighted_matrix[criterion].max()
            ideal_worst[criterion] = weighted_matrix[criterion].min()
        else:
            # Cost criterion: lower is better
            ideal_best[criterion] = weighted_matrix[criterion].min()
            ideal_worst[criterion] = weighted_matrix[criterion].max()
    
    return ideal_best, ideal_worst


def calculate_distances(
    weighted_matrix: pd.DataFrame,
    criteria: List[str],
    ideal_best: Dict[str, float],
    ideal_worst: Dict[str, float]
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Euclidean distances from ideal best and worst.
    
    Args:
        weighted_matrix: Weighted normalized matrix
        criteria: List of criterion columns
        ideal_best: Ideal best values
        ideal_worst: Ideal worst values
        
    Returns:
        Tuple of (distance_to_best, distance_to_worst) Series
    """
    # Filter criteria to available columns
    available_criteria = [c for c in criteria if c in weighted_matrix.columns and c in ideal_best]
    
    # Calculate squared differences
    diff_best_sq = pd.DataFrame()
    diff_worst_sq = pd.DataFrame()
    
    for criterion in available_criteria:
        diff_best_sq[criterion] = (weighted_matrix[criterion] - ideal_best[criterion]) ** 2
        diff_worst_sq[criterion] = (weighted_matrix[criterion] - ideal_worst[criterion]) ** 2
    
    # Euclidean distance
    distance_best = np.sqrt(diff_best_sq.sum(axis=1))
    distance_worst = np.sqrt(diff_worst_sq.sum(axis=1))
    
    return distance_best, distance_worst


def calculate_closeness(
    distance_best: pd.Series,
    distance_worst: pd.Series
) -> pd.Series:
    """
    Calculate closeness coefficient.
    
    C_i = D_i- / (D_i+ + D_i-)
    
    Higher closeness = better alternative (closer to ideal best)
    
    Args:
        distance_best: Distance to ideal best
        distance_worst: Distance to ideal worst
        
    Returns:
        Closeness coefficient Series
    """
    denominator = distance_best + distance_worst
    
    # Avoid division by zero
    closeness = np.where(
        denominator > 0,
        distance_worst / denominator,
        0.5  # Equal distance case
    )
    
    return pd.Series(closeness)


def run_topsis(
    stats_df: pd.DataFrame,
    weights: Dict[str, float] = None
) -> pd.DataFrame:
    """
    Run TOPSIS analysis on benchmark data.
    
    Args:
        stats_df: Summary statistics DataFrame
        weights: Criterion weights (default: from config)
        
    Returns:
        DataFrame with TOPSIS rankings
    """
    if weights is None:
        weights = TOPSIS_WEIGHTS
    
    print("\nRunning TOPSIS Analysis")
    print(f"Weights: {weights}")
    
    # Step 1: Prepare decision matrix
    decision_matrix = prepare_decision_matrix(stats_df)
    
    # Define criteria columns
    criteria = ['total_time_ms', 'peak_memory_kb', 'energy_mj', 
                'key_size_bytes', 'ct_size_bytes']
    criteria = [c for c in criteria if c in decision_matrix.columns]
    
    print(f"Criteria: {criteria}")
    
    results = []
    
    # Run TOPSIS per device class
    for device_class in decision_matrix['device_class'].unique():
        print(f"\n{device_class}:")
        
        class_df = decision_matrix[decision_matrix['device_class'] == device_class].copy()
        
        # Step 2: Normalize
        normalized = normalize_matrix(class_df, criteria)
        
        # Step 3: Apply weights
        weighted = apply_weights(normalized, criteria, weights)
        
        # Step 4: Determine ideal solutions
        ideal_best, ideal_worst = determine_ideal_solutions(weighted, criteria)
        
        # Step 5: Calculate distances
        dist_best, dist_worst = calculate_distances(weighted, criteria, ideal_best, ideal_worst)
        
        # Step 6: Calculate closeness coefficient
        closeness = calculate_closeness(dist_best, dist_worst)
        
        # Build results
        class_results = class_df[['algorithm', 'device_class']].copy()
        class_results['distance_best'] = dist_best.values
        class_results['distance_worst'] = dist_worst.values
        class_results['closeness'] = closeness.values
        class_results['rank'] = class_results['closeness'].rank(ascending=False).astype(int)
        
        results.append(class_results)
        
        # Print top 3
        top3 = class_results.nsmallest(3, 'rank')
        for _, row in top3.iterrows():
            print(f"  #{int(row['rank'])}: {row['algorithm']} (C = {row['closeness']:.4f})")
    
    # Combine results
    rankings_df = pd.concat(results, ignore_index=True)
    
    return rankings_df


def create_feasibility_matrix(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create feasibility matrix (Algorithm x Device Class).
    
    Classifies each algorithm as FEASIBLE, MARGINAL, or INFEASIBLE
    based on whether it meets device class constraints.
    
    Args:
        df: Cleaned benchmark data or summary stats DataFrame
        
    Returns:
        Feasibility matrix DataFrame
    """
    print("\nCreating feasibility matrix...")
    
    # Check if this is raw/cleaned data or summary stats
    if 'metric' in df.columns and 'mean' in df.columns:
        # It's summary stats - use prepare_decision_matrix
        decision_matrix = prepare_decision_matrix(df)
    else:
        # It's raw/cleaned data - aggregate directly
        decision_matrix = df.groupby(['algorithm', 'device_class']).agg({
            'total_time_ms': 'mean',
            'peak_memory_kb': 'mean',
            'energy_mj': 'mean'
        }).reset_index()
    
    # Device class constraints
    constraints = {
        'Class 0': {'memory_kb': 10, 'time_ms': 500, 'energy_mj': 0.1},
        'Class 1': {'memory_kb': 50, 'time_ms': 2000, 'energy_mj': 1.0},
        'Class 2': {'memory_kb': 250, 'time_ms': 10000, 'energy_mj': 10.0}
    }
    
    feasibility = []
    
    for _, row in decision_matrix.iterrows():
        algo = row['algorithm']
        device_class = row['device_class']
        
        if device_class not in constraints:
            continue
        
        constraint = constraints[device_class]
        
        # Check each constraint
        memory_ok = row.get('peak_memory_kb', 0) <= constraint['memory_kb']
        time_ok = row.get('total_time_ms', 0) <= constraint['time_ms']
        energy_ok = row.get('energy_mj', 0) <= constraint['energy_mj']
        
        # Calculate ratios for marginal classification
        memory_ratio = row.get('peak_memory_kb', 0) / constraint['memory_kb']
        time_ratio = row.get('total_time_ms', 0) / constraint['time_ms']
        energy_ratio = row.get('energy_mj', 0) / constraint['energy_mj']
        
        max_ratio = max(memory_ratio, time_ratio, energy_ratio)
        
        if max_ratio > 1.0:
            status = 'INFEASIBLE'
        elif max_ratio > 0.7:
            status = 'MARGINAL'
        else:
            status = 'FEASIBLE'
        
        feasibility.append({
            'algorithm': algo,
            'device_class': device_class,
            'memory_ratio': memory_ratio,
            'time_ratio': time_ratio,
            'energy_ratio': energy_ratio,
            'max_ratio': max_ratio,
            'status': status
        })
    
    feasibility_df = pd.DataFrame(feasibility)
    
    # Print summary
    print("\nFeasibility Summary:")
    for device_class in feasibility_df['device_class'].unique():
        class_df = feasibility_df[feasibility_df['device_class'] == device_class]
        counts = class_df['status'].value_counts().to_dict()
        print(f"  {device_class}: {counts}")
    
    return feasibility_df


def run_topsis_analysis(
    input_file: Path = None,
    rankings_output: Path = None,
    feasibility_output: Path = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run full TOPSIS analysis pipeline.
    
    Args:
        input_file: Path to summary statistics
        rankings_output: Path for rankings output
        feasibility_output: Path for feasibility matrix output
        
    Returns:
        Tuple of (rankings DataFrame, feasibility DataFrame)
    """
    if input_file is None:
        input_file = SUMMARY_STATS_FILE
    if rankings_output is None:
        rankings_output = TOPSIS_RANKINGS_FILE
    if feasibility_output is None:
        feasibility_output = FEASIBILITY_MATRIX_FILE
    
    print("=" * 60)
    print("TOPSIS MULTI-CRITERIA DECISION ANALYSIS")
    print("=" * 60)
    
    # Load data
    stats_df = load_summary_stats(input_file)
    
    # Run TOPSIS
    rankings_df = run_topsis(stats_df)
    
    # Create feasibility matrix
    feasibility_df = create_feasibility_matrix(stats_df)
    
    # Save results
    rankings_output.parent.mkdir(parents=True, exist_ok=True)
    rankings_df.to_csv(rankings_output, index=False)
    print(f"\n✓ TOPSIS rankings saved to: {rankings_output}")
    
    feasibility_df.to_csv(feasibility_output, index=False)
    print(f"✓ Feasibility matrix saved to: {feasibility_output}")
    
    # Print final rankings
    print("\n" + "=" * 60)
    print("FINAL ALGORITHM RECOMMENDATIONS")
    print("=" * 60)
    
    for device_class in rankings_df['device_class'].unique():
        class_rankings = rankings_df[rankings_df['device_class'] == device_class]
        class_feasibility = feasibility_df[feasibility_df['device_class'] == device_class]
        
        # Get top feasible algorithm
        feasible_algos = class_feasibility[class_feasibility['status'].isin(['FEASIBLE', 'MARGINAL'])]['algorithm'].tolist()
        
        print(f"\n{device_class}:")
        
        if not feasible_algos:
            print("  ⚠ No feasible algorithms for this device class")
            continue
        
        # Find best feasible option by TOPSIS ranking
        feasible_rankings = class_rankings[class_rankings['algorithm'].isin(feasible_algos)].nsmallest(3, 'rank')
        
        for _, row in feasible_rankings.iterrows():
            algo_feas = class_feasibility[class_feasibility['algorithm'] == row['algorithm']]['status'].values[0]
            print(f"  #{int(row['rank'])}: {row['algorithm']} (C={row['closeness']:.4f}, {algo_feas})")
    
    return rankings_df, feasibility_df


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run TOPSIS analysis')
    parser.add_argument('--input', type=str, help='Input statistics file')
    parser.add_argument('--rankings-output', type=str, help='Rankings output file')
    parser.add_argument('--feasibility-output', type=str, help='Feasibility output file')
    
    args = parser.parse_args()
    
    input_file = Path(args.input) if args.input else None
    rankings_output = Path(args.rankings_output) if args.rankings_output else None
    feasibility_output = Path(args.feasibility_output) if args.feasibility_output else None
    
    run_topsis_analysis(input_file, rankings_output, feasibility_output)


if __name__ == "__main__":
    main()
