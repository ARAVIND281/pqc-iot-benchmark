#!/usr/bin/env python3
"""
PQC IoT Benchmark - Pipeline Runner
====================================

Main entry point to run the complete benchmarking and analysis pipeline.

Usage:
    python run_pipeline.py [--stages STAGES] [--skip-benchmarks] [--help]

Options:
    --stages STAGES     Comma-separated list of stages to run
                        (benchmark,clean,analyze,figures,all)
    --skip-benchmarks   Use existing benchmark data (skip benchmarking stage)
    --compile-paper     Compile LaTeX paper after generating figures

Author: PQC-IoT Research Team
Date: March 2026
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'analysis'))


def print_banner(text: str):
    """Print a formatted banner."""
    width = 60
    print("\n" + "=" * width)
    print(f" {text.center(width - 2)} ")
    print("=" * width)


def print_step(step: str):
    """Print a step indicator."""
    print(f"\n>>> {step}")


def run_benchmarks():
    """Execute the benchmarking stage."""
    print_banner("STAGE 1: BENCHMARKING")
    
    from benchmark_runner import run_full_benchmark
    from config import RAW_BENCHMARKS_FILE
    
    print_step("Running benchmarks for all algorithm-device combinations...")
    print("This may take 15-30 minutes depending on system performance.\n")
    
    start_time = time.time()
    df = run_full_benchmark()
    elapsed = time.time() - start_time
    
    print(f"\n✓ Benchmarking complete in {elapsed:.1f} seconds")
    print(f"  Output: {RAW_BENCHMARKS_FILE}")
    print(f"  Total measurements: {len(df)}")
    
    return df


def run_data_cleaning():
    """Execute the data cleaning stage."""
    print_banner("STAGE 2: DATA CLEANING")
    
    from data_cleaning import clean_benchmark_data
    from config import RAW_BENCHMARKS_FILE, CLEANED_BENCHMARKS_FILE
    import pandas as pd
    
    print_step("Loading raw benchmark data...")
    raw_df = pd.read_csv(RAW_BENCHMARKS_FILE)
    print(f"  Loaded: {len(raw_df)} rows")
    
    print_step("Removing warmup iterations and outliers...")
    cleaned_df = clean_benchmark_data(raw_df)
    
    print_step("Saving cleaned data...")
    cleaned_df.to_csv(CLEANED_BENCHMARKS_FILE, index=False)
    
    removed = len(raw_df) - len(cleaned_df)
    print(f"\n✓ Data cleaning complete")
    print(f"  Removed: {removed} rows ({100*removed/len(raw_df):.1f}%)")
    print(f"  Output: {CLEANED_BENCHMARKS_FILE}")
    
    return cleaned_df


def run_analysis():
    """Execute the analysis stage."""
    print_banner("STAGE 3: STATISTICAL ANALYSIS")
    
    import pandas as pd
    from config import (
        CLEANED_BENCHMARKS_FILE, SUMMARY_STATS_FILE,
        ANOVA_RESULTS_FILE, TUKEY_RESULTS_FILE,
        CORRELATION_MATRIX_FILE, TOPSIS_RANKINGS_FILE,
        FEASIBILITY_MATRIX_FILE
    )
    
    print_step("Loading cleaned data...")
    df = pd.read_csv(CLEANED_BENCHMARKS_FILE)
    
    # Descriptive Statistics
    print_step("Computing descriptive statistics...")
    from descriptive_stats import compute_statistics
    stats_df = compute_statistics(df)
    stats_df.to_csv(SUMMARY_STATS_FILE, index=False)
    print(f"  Saved: {SUMMARY_STATS_FILE}")
    
    # ANOVA
    print_step("Running ANOVA tests...")
    from statistical_tests import run_anova, run_tukey_hsd
    anova_results = run_anova(df)
    anova_results.to_csv(ANOVA_RESULTS_FILE, index=False)
    print(f"  Saved: {ANOVA_RESULTS_FILE}")
    
    # Tukey HSD
    print_step("Running Tukey HSD post-hoc tests...")
    tukey_results = run_tukey_hsd(df)
    tukey_results.to_csv(TUKEY_RESULTS_FILE, index=False)
    print(f"  Saved: {TUKEY_RESULTS_FILE}")
    
    # Correlation Analysis
    print_step("Computing correlation matrix...")
    from correlation_analysis import compute_correlation_matrix
    corr_df = compute_correlation_matrix(df)
    corr_df.to_csv(CORRELATION_MATRIX_FILE)
    print(f"  Saved: {CORRELATION_MATRIX_FILE}")
    
    # TOPSIS Ranking
    print_step("Running TOPSIS multi-criteria analysis...")
    from topsis_ranking import run_topsis, create_feasibility_matrix
    
    # Prepare data for TOPSIS
    topsis_data = df.groupby(['algorithm', 'device_class']).agg({
        'total_time_ms': 'mean',
        'peak_memory_kb': 'mean',
        'energy_mj': 'mean'
    }).reset_index()
    
    topsis_results = run_topsis(topsis_data)
    topsis_results.to_csv(TOPSIS_RANKINGS_FILE, index=False)
    print(f"  Saved: {TOPSIS_RANKINGS_FILE}")
    
    # Feasibility Matrix
    print_step("Creating feasibility matrix...")
    feasibility = create_feasibility_matrix(df)
    feasibility.to_csv(FEASIBILITY_MATRIX_FILE, index=False)
    print(f"  Saved: {FEASIBILITY_MATRIX_FILE}")
    
    print("\n✓ Statistical analysis complete")


def run_figure_generation():
    """Execute the figure generation stage."""
    print_banner("STAGE 4: FIGURE GENERATION")
    
    from generate_figures import generate_all_figures
    
    print_step("Generating all figures...")
    generate_all_figures()
    
    print("\n✓ Figure generation complete")


def compile_paper():
    """Compile the LaTeX paper."""
    print_banner("STAGE 5: LATEX COMPILATION")
    
    paper_dir = PROJECT_ROOT / 'paper'
    
    print_step("Compiling LaTeX paper...")
    
    # Run pdflatex twice for references
    for i in range(2):
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', 'main.tex'],
            cwd=paper_dir,
            capture_output=True
        )
        
        if result.returncode != 0:
            print(f"Warning: pdflatex pass {i+1} returned non-zero")
    
    # Run bibtex
    subprocess.run(['bibtex', 'main'], cwd=paper_dir, capture_output=True)
    
    # Run pdflatex again
    subprocess.run(
        ['pdflatex', '-interaction=nonstopmode', 'main.tex'],
        cwd=paper_dir,
        capture_output=True
    )
    
    pdf_path = paper_dir / 'main.pdf'
    if pdf_path.exists():
        print(f"\n✓ Paper compiled successfully")
        print(f"  Output: {pdf_path}")
    else:
        print("\n✗ Paper compilation may have failed. Check paper/main.log")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='PQC IoT Benchmark Pipeline Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--stages', type=str, default='all',
        help='Comma-separated stages: benchmark,clean,analyze,figures,paper,all'
    )
    parser.add_argument(
        '--skip-benchmarks', action='store_true',
        help='Skip benchmarking stage (use existing data)'
    )
    parser.add_argument(
        '--compile-paper', action='store_true',
        help='Compile LaTeX paper'
    )
    
    args = parser.parse_args()
    
    print_banner("PQC IoT BENCHMARK PIPELINE")
    print(f"Project root: {PROJECT_ROOT}")
    
    stages = args.stages.lower().split(',')
    
    start_time = time.time()
    
    try:
        # Stage 1: Benchmarking
        if 'all' in stages or 'benchmark' in stages:
            if args.skip_benchmarks:
                print("\n>>> Skipping benchmarks (using existing data)")
            else:
                run_benchmarks()
        
        # Stage 2: Data Cleaning
        if 'all' in stages or 'clean' in stages:
            run_data_cleaning()
        
        # Stage 3: Analysis
        if 'all' in stages or 'analyze' in stages:
            run_analysis()
        
        # Stage 4: Figures
        if 'all' in stages or 'figures' in stages:
            run_figure_generation()
        
        # Stage 5: Paper compilation
        if 'paper' in stages or args.compile_paper:
            compile_paper()
        
        elapsed = time.time() - start_time
        print_banner("PIPELINE COMPLETE")
        print(f"Total time: {elapsed:.1f} seconds")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("  Make sure you run stages in order: benchmark -> clean -> analyze -> figures")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
