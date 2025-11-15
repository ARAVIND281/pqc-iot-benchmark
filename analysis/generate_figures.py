"""
PQC IoT Benchmark - Figure Generation
=====================================

Generates all publication-quality figures for the IEEE paper.

Author: PQC-IoT Research Team
Date: March 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import (
    SUMMARY_STATS_FILE, CORRELATION_MATRIX_FILE, TOPSIS_RANKINGS_FILE,
    FEASIBILITY_MATRIX_FILE, CLEANED_BENCHMARKS_FILE, FIGURES_DIR,
    FIGURE_DPI, FIGURE_SIZE_SINGLE, FIGURE_SIZE_DOUBLE,
    FONT_SIZE_TITLE, FONT_SIZE_LABEL, FONT_SIZE_TICK,
    ALGORITHM_COLORS, DEVICE_CLASS_COLORS, FEASIBILITY_COLORS,
    FIGURE_FILES
)

# Set matplotlib style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['figure.dpi'] = FIGURE_DPI


def load_data() -> Dict[str, pd.DataFrame]:
    """Load all required data files."""
    data = {}
    
    for name, path in [
        ('summary', SUMMARY_STATS_FILE),
        ('correlation', CORRELATION_MATRIX_FILE),
        ('topsis', TOPSIS_RANKINGS_FILE),
        ('feasibility', FEASIBILITY_MATRIX_FILE),
        ('cleaned', CLEANED_BENCHMARKS_FILE)
    ]:
        if path.exists():
            data[name] = pd.read_csv(path)
            print(f"✓ Loaded {name}: {len(data[name])} rows")
        else:
            print(f"✗ Missing: {path}")
    
    return data


def fig1_framework_architecture():
    """
    Figure 1: Benchmarking framework architecture diagram.
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Colors
    colors = {
        'input': '#e3f2fd',
        'process': '#fff3e0',
        'output': '#e8f5e9',
        'arrow': '#546e7a'
    }
    
    # Draw boxes
    boxes = [
        # Input layer
        {'x': 0.5, 'y': 6.5, 'w': 2.5, 'h': 1, 'text': 'PQC Algorithms\n(liboqs/pqm4)', 'color': colors['input']},
        {'x': 3.5, 'y': 6.5, 'w': 2.5, 'h': 1, 'text': 'Device Classes\n(RFC 7228)', 'color': colors['input']},
        {'x': 6.5, 'y': 6.5, 'w': 2.5, 'h': 1, 'text': 'Benchmark Config\n(config.py)', 'color': colors['input']},
        
        # Processing layer
        {'x': 2, 'y': 4.5, 'w': 6, 'h': 1.2, 'text': 'Benchmark Runner\n(1000 iterations × 45 configurations)', 'color': colors['process']},
        
        # Analysis layer
        {'x': 0.5, 'y': 2.5, 'w': 2.2, 'h': 1, 'text': 'Data Cleaning\n(IQR outliers)', 'color': colors['process']},
        {'x': 2.9, 'y': 2.5, 'w': 2.2, 'h': 1, 'text': 'Statistics\n(ANOVA)', 'color': colors['process']},
        {'x': 5.3, 'y': 2.5, 'w': 2.2, 'h': 1, 'text': 'TOPSIS\nRanking', 'color': colors['process']},
        {'x': 7.7, 'y': 2.5, 'w': 1.8, 'h': 1, 'text': 'Figures', 'color': colors['process']},
        
        # Output layer
        {'x': 2.5, 'y': 0.5, 'w': 5, 'h': 1, 'text': 'IEEE Paper (8-12 pages)\nTables + Figures + Analysis', 'color': colors['output']}
    ]
    
    for box in boxes:
        rect = FancyBboxPatch(
            (box['x'], box['y']), box['w'], box['h'],
            boxstyle="round,pad=0.05,rounding_size=0.1",
            facecolor=box['color'], edgecolor='#333', linewidth=1.5
        )
        ax.add_patch(rect)
        ax.text(box['x'] + box['w']/2, box['y'] + box['h']/2, box['text'],
               ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw arrows
    arrow_props = dict(arrowstyle='->', color=colors['arrow'], lw=2)
    
    # Input to benchmark
    for x in [1.75, 4.75, 7.75]:
        ax.annotate('', xy=(5, 5.7), xytext=(x, 6.5),
                   arrowprops=arrow_props)
    
    # Benchmark to analysis
    ax.annotate('', xy=(5, 4.5), xytext=(5, 3.7),
               arrowprops=dict(arrowstyle='->', color=colors['arrow'], lw=2, 
                              connectionstyle='arc3'))
    
    # Analysis to output
    for x in [1.6, 4.0, 6.4, 8.6]:
        ax.annotate('', xy=(5, 1.5), xytext=(x, 2.5),
                   arrowprops=arrow_props)
    
    ax.set_title('Figure 1: PQC IoT Benchmarking Framework Architecture',
                fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig1_framework'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated: fig1_framework.png")


def fig2_keygen_time(data: Dict[str, pd.DataFrame]):
    """Figure 2: Key generation time comparison."""
    _generate_time_comparison_chart(
        data, 'keygen_time_ms', 'Key Generation Time',
        FIGURE_FILES['fig2_keygen_time'], 'fig2_keygen_time.png'
    )


def fig3_encaps_time(data: Dict[str, pd.DataFrame]):
    """Figure 3: Encapsulation/signing time comparison."""
    _generate_time_comparison_chart(
        data, 'encaps_time_ms', 'Encapsulation/Signing Time',
        FIGURE_FILES['fig3_encaps_time'], 'fig3_encaps_time.png'
    )


def fig4_decaps_time(data: Dict[str, pd.DataFrame]):
    """Figure 4: Decapsulation/verification time comparison."""
    _generate_time_comparison_chart(
        data, 'decaps_time_ms', 'Decapsulation/Verification Time',
        FIGURE_FILES['fig4_decaps_time'], 'fig4_decaps_time.png'
    )


def _generate_time_comparison_chart(
    data: Dict[str, pd.DataFrame],
    metric: str,
    title_suffix: str,
    output_path: Path,
    filename: str
):
    """Generate grouped bar chart for time metrics."""
    if 'summary' not in data:
        print(f"✗ Skipping {filename}: summary data not available")
        return
    
    df = data['summary']
    metric_df = df[df['metric'] == metric].copy()
    
    if len(metric_df) == 0:
        print(f"✗ Skipping {filename}: no data for {metric}")
        return
    
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_DOUBLE)
    
    # Prepare data for grouped bar chart
    algorithms = metric_df['algorithm'].unique()
    device_classes = ['Class 0', 'Class 1', 'Class 2']
    
    x = np.arange(len(algorithms))
    width = 0.25
    
    for i, dc in enumerate(device_classes):
        dc_data = metric_df[metric_df['device_class'] == dc]
        values = []
        errors = []
        for algo in algorithms:
            algo_data = dc_data[dc_data['algorithm'] == algo]
            if len(algo_data) > 0:
                values.append(algo_data['mean'].values[0])
                errors.append(algo_data['std'].values[0])
            else:
                values.append(0)
                errors.append(0)
        
        bars = ax.bar(x + i*width, values, width, label=dc,
                     color=DEVICE_CLASS_COLORS[dc], yerr=errors, capsize=3)
    
    ax.set_xlabel('Algorithm', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel(f'{title_suffix} (ms)', fontsize=FONT_SIZE_LABEL)
    ax.set_title(f'Figure: {title_suffix} by Algorithm and Device Class',
                fontsize=FONT_SIZE_TITLE)
    ax.set_xticks(x + width)
    ax.set_xticklabels(algorithms, rotation=45, ha='right', fontsize=FONT_SIZE_TICK)
    ax.legend(title='Device Class', loc='upper right')
    ax.set_yscale('log')  # Log scale for better visibility
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated: {filename}")


def fig5_memory(data: Dict[str, pd.DataFrame]):
    """Figure 5: Memory usage breakdown."""
    if 'summary' not in data:
        print("✗ Skipping fig5: summary data not available")
        return
    
    df = data['summary']
    
    # Get memory data
    memory_df = df[df['metric'] == 'peak_memory_kb'].copy()
    
    if len(memory_df) == 0:
        print("✗ Skipping fig5: no memory data")
        return
    
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_DOUBLE)
    
    # Pivot for heatmap-style visualization
    algorithms = memory_df['algorithm'].unique()
    device_classes = ['Class 0', 'Class 1', 'Class 2']
    
    x = np.arange(len(algorithms))
    width = 0.25
    
    for i, dc in enumerate(device_classes):
        dc_data = memory_df[memory_df['device_class'] == dc]
        values = [dc_data[dc_data['algorithm'] == a]['mean'].values[0] 
                 if len(dc_data[dc_data['algorithm'] == a]) > 0 else 0 
                 for a in algorithms]
        
        ax.bar(x + i*width, values, width, label=dc,
              color=DEVICE_CLASS_COLORS[dc])
    
    ax.set_xlabel('Algorithm', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('Peak Memory Usage (KB)', fontsize=FONT_SIZE_LABEL)
    ax.set_title('Figure 5: Peak Memory Usage by Algorithm', fontsize=FONT_SIZE_TITLE)
    ax.set_xticks(x + width)
    ax.set_xticklabels(algorithms, rotation=45, ha='right', fontsize=FONT_SIZE_TICK)
    ax.legend(title='Device Class')
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig5_memory'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print("✓ Generated: fig5_memory.png")


def fig6_boxplot(data: Dict[str, pd.DataFrame]):
    """Figure 6: Box plots of execution time distributions."""
    if 'cleaned' not in data:
        print("✗ Skipping fig6: cleaned data not available")
        return
    
    df = data['cleaned']
    
    # Filter to successful runs
    if 'status' in df.columns:
        df = df[df['status'] == 'SUCCESS']
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for i, dc in enumerate(['Class 0', 'Class 1', 'Class 2']):
        dc_df = df[df['device_class'] == dc]
        
        if len(dc_df) == 0:
            continue
        
        # Create box plot
        dc_df.boxplot(column='total_time_ms', by='algorithm', ax=axes[i],
                     rot=45, fontsize=8)
        axes[i].set_title(dc, fontsize=FONT_SIZE_LABEL)
        axes[i].set_xlabel('')
        axes[i].set_ylabel('Total Time (ms)' if i == 0 else '')
        axes[i].set_yscale('log')
    
    fig.suptitle('Figure 6: Distribution of Total Execution Time', 
                fontsize=FONT_SIZE_TITLE, y=1.02)
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig6_boxplot'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print("✓ Generated: fig6_boxplot.png")


def fig7_correlation(data: Dict[str, pd.DataFrame]):
    """Figure 7: Correlation heatmap."""
    if 'correlation' not in data:
        print("✗ Skipping fig7: correlation data not available")
        return
    
    corr_df = data['correlation']
    
    # Set index if needed
    if 'Unnamed: 0' in corr_df.columns:
        corr_df = corr_df.set_index('Unnamed: 0')
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create heatmap
    sns.heatmap(corr_df.astype(float), annot=True, fmt='.2f', cmap='RdBu_r',
               center=0, vmin=-1, vmax=1, ax=ax,
               annot_kws={'size': 9},
               cbar_kws={'label': 'Pearson Correlation'})
    
    ax.set_title('Figure 7: Correlation Matrix of Performance Metrics',
                fontsize=FONT_SIZE_TITLE)
    
    # Rotate labels
    plt.xticks(rotation=45, ha='right', fontsize=FONT_SIZE_TICK)
    plt.yticks(rotation=0, fontsize=FONT_SIZE_TICK)
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig7_correlation'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print("✓ Generated: fig7_correlation.png")


def fig8_radar(data: Dict[str, pd.DataFrame]):
    """Figure 8: Radar chart for multi-dimensional comparison."""
    if 'summary' not in data:
        print("✗ Skipping fig8: summary data not available")
        return
    
    df = data['summary']
    
    # Select metrics for radar chart
    metrics = ['keygen_time_ms', 'encaps_time_ms', 'decaps_time_ms', 
               'peak_memory_kb', 'energy_mj']
    
    # Filter to Class 2 for cleaner visualization
    df_class2 = df[df['device_class'] == 'Class 2']
    
    # Get algorithms
    algorithms = df_class2['algorithm'].unique()[:6]  # Limit to 6 for readability
    
    # Prepare data
    values_dict = {}
    for algo in algorithms:
        algo_data = df_class2[df_class2['algorithm'] == algo]
        values = []
        for metric in metrics:
            metric_data = algo_data[algo_data['metric'] == metric]
            if len(metric_data) > 0:
                values.append(metric_data['mean'].values[0])
            else:
                values.append(0)
        values_dict[algo] = values
    
    # Normalize values (0-1 scale)
    max_values = np.max(list(values_dict.values()), axis=0)
    for algo in values_dict:
        values_dict[algo] = [v/m if m > 0 else 0 for v, m in zip(values_dict[algo], max_values)]
    
    # Create radar chart
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
    
    angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle
    
    colors = plt.cm.Set2(np.linspace(0, 1, len(algorithms)))
    
    for i, algo in enumerate(algorithms):
        values = values_dict[algo] + values_dict[algo][:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=algo, color=colors[i])
        ax.fill(angles, values, alpha=0.1, color=colors[i])
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=FONT_SIZE_TICK)
    ax.set_title('Figure 8: Multi-dimensional Algorithm Comparison (Class 2)',
                fontsize=FONT_SIZE_TITLE, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig8_radar'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print("✓ Generated: fig8_radar.png")


def fig9_feasibility(data: Dict[str, pd.DataFrame]):
    """Figure 9: Feasibility matrix heatmap."""
    if 'feasibility' not in data:
        print("✗ Skipping fig9: feasibility data not available")
        return
    
    df = data['feasibility']
    
    # Create pivot table
    pivot = df.pivot_table(
        index='algorithm',
        columns='device_class',
        values='status',
        aggfunc='first'
    )
    
    # Map status to numeric for heatmap
    status_map = {'FEASIBLE': 2, 'MARGINAL': 1, 'INFEASIBLE': 0}
    numeric_pivot = pivot.replace(status_map)
    
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # Create heatmap
    cmap = plt.cm.colors.ListedColormap(['#e74c3c', '#f39c12', '#27ae60'])
    
    im = ax.imshow(numeric_pivot.values, cmap=cmap, aspect='auto', vmin=0, vmax=2)
    
    # Add text annotations
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            text = pivot.iloc[i, j]
            color = 'white' if text == 'INFEASIBLE' else 'black'
            ax.text(j, i, text, ha='center', va='center', fontsize=10, color=color)
    
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=FONT_SIZE_TICK)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=FONT_SIZE_TICK)
    
    ax.set_xlabel('Device Class', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('Algorithm', fontsize=FONT_SIZE_LABEL)
    ax.set_title('Figure 9: Algorithm Feasibility Matrix', fontsize=FONT_SIZE_TITLE)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor='#27ae60', label='FEASIBLE'),
        mpatches.Patch(facecolor='#f39c12', label='MARGINAL'),
        mpatches.Patch(facecolor='#e74c3c', label='INFEASIBLE')
    ]
    ax.legend(handles=legend_elements, loc='upper center', 
             bbox_to_anchor=(0.5, -0.05), ncol=3)
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig9_feasibility'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print("✓ Generated: fig9_feasibility.png")


def fig10_topsis(data: Dict[str, pd.DataFrame]):
    """Figure 10: TOPSIS ranking bar chart."""
    if 'topsis' not in data:
        print("✗ Skipping fig10: topsis data not available")
        return
    
    df = data['topsis']
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for i, dc in enumerate(['Class 0', 'Class 1', 'Class 2']):
        dc_df = df[df['device_class'] == dc].sort_values('closeness', ascending=True)
        
        if len(dc_df) == 0:
            continue
        
        colors = [FEASIBILITY_COLORS.get('FEASIBLE', '#27ae60') 
                 if c > 0.5 else FEASIBILITY_COLORS.get('INFEASIBLE', '#e74c3c')
                 for c in dc_df['closeness']]
        
        axes[i].barh(dc_df['algorithm'], dc_df['closeness'], color=colors)
        axes[i].set_xlabel('TOPSIS Closeness Coefficient', fontsize=FONT_SIZE_LABEL)
        axes[i].set_title(dc, fontsize=FONT_SIZE_LABEL)
        axes[i].set_xlim(0, 1)
        axes[i].tick_params(axis='y', labelsize=8)
    
    fig.suptitle('Figure 10: TOPSIS Algorithm Rankings by Device Class',
                fontsize=FONT_SIZE_TITLE, y=1.02)
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig10_topsis'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print("✓ Generated: fig10_topsis.png")


def fig11_tradeoff(data: Dict[str, pd.DataFrame]):
    """Figure 11: Speed vs Memory trade-off scatter plot."""
    if 'summary' not in data:
        print("✗ Skipping fig11: summary data not available")
        return
    
    df = data['summary']
    
    # Get mean values for time and memory
    time_df = df[df['metric'] == 'total_time_ms'][['algorithm', 'device_class', 'mean']].copy()
    time_df = time_df.rename(columns={'mean': 'time_ms'})
    
    memory_df = df[df['metric'] == 'peak_memory_kb'][['algorithm', 'device_class', 'mean']].copy()
    memory_df = memory_df.rename(columns={'mean': 'memory_kb'})
    
    merged = pd.merge(time_df, memory_df, on=['algorithm', 'device_class'])
    
    # Get family info
    family_df = df[['algorithm', 'family']].drop_duplicates()
    merged = pd.merge(merged, family_df, on='algorithm')
    
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_DOUBLE)
    
    # Plot by family
    families = merged['family'].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(families)))
    
    for i, family in enumerate(families):
        family_data = merged[merged['family'] == family]
        ax.scatter(family_data['time_ms'], family_data['memory_kb'],
                  label=family, color=colors[i], s=100, alpha=0.7)
        
        # Add algorithm labels
        for _, row in family_data.iterrows():
            ax.annotate(row['algorithm'], (row['time_ms'], row['memory_kb']),
                       fontsize=7, alpha=0.8, xytext=(5, 5),
                       textcoords='offset points')
    
    ax.set_xlabel('Total Execution Time (ms)', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('Peak Memory Usage (KB)', fontsize=FONT_SIZE_LABEL)
    ax.set_title('Figure 11: Speed vs Memory Trade-off', fontsize=FONT_SIZE_TITLE)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(title='Algorithm Family')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig11_tradeoff'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print("✓ Generated: fig11_tradeoff.png")


def fig12_energy(data: Dict[str, pd.DataFrame]):
    """Figure 12: Energy consumption comparison."""
    if 'summary' not in data:
        print("✗ Skipping fig12: summary data not available")
        return
    
    df = data['summary']
    energy_df = df[df['metric'] == 'energy_mj'].copy()
    
    if len(energy_df) == 0:
        print("✗ Skipping fig12: no energy data")
        return
    
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_DOUBLE)
    
    algorithms = energy_df['algorithm'].unique()
    device_classes = ['Class 0', 'Class 1', 'Class 2']
    
    x = np.arange(len(algorithms))
    width = 0.25
    
    for i, dc in enumerate(device_classes):
        dc_data = energy_df[energy_df['device_class'] == dc]
        values = [dc_data[dc_data['algorithm'] == a]['mean'].values[0]
                 if len(dc_data[dc_data['algorithm'] == a]) > 0 else 0
                 for a in algorithms]
        
        ax.bar(x + i*width, values, width, label=dc,
              color=DEVICE_CLASS_COLORS[dc])
    
    ax.set_xlabel('Algorithm', fontsize=FONT_SIZE_LABEL)
    ax.set_ylabel('Energy Consumption (mJ)', fontsize=FONT_SIZE_LABEL)
    ax.set_title('Figure 12: Energy Consumption by Algorithm and Device Class',
                fontsize=FONT_SIZE_TITLE)
    ax.set_xticks(x + width)
    ax.set_xticklabels(algorithms, rotation=45, ha='right', fontsize=FONT_SIZE_TICK)
    ax.set_yscale('log')
    ax.legend(title='Device Class')
    
    plt.tight_layout()
    plt.savefig(FIGURE_FILES['fig12_energy'], dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print("✓ Generated: fig12_energy.png")


def generate_all_figures():
    """Generate all 12 figures."""
    print("=" * 60)
    print("GENERATING ALL FIGURES")
    print("=" * 60)
    
    # Ensure output directory exists
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\nLoading data files...")
    data = load_data()
    
    # Generate each figure
    print("\nGenerating figures...")
    
    fig1_framework_architecture()
    fig2_keygen_time(data)
    fig3_encaps_time(data)
    fig4_decaps_time(data)
    fig5_memory(data)
    fig6_boxplot(data)
    fig7_correlation(data)
    fig8_radar(data)
    fig9_feasibility(data)
    fig10_topsis(data)
    fig11_tradeoff(data)
    fig12_energy(data)
    
    print("\n" + "=" * 60)
    print("FIGURE GENERATION COMPLETE")
    print(f"Output directory: {FIGURES_DIR}")
    print("=" * 60)


def main():
    """Main entry point."""
    generate_all_figures()


if __name__ == "__main__":
    main()
