"""
PQC IoT Benchmark - Configuration
=================================

Central configuration file defining all parameters, algorithm specifications,
device class constraints, and benchmark settings. No magic numbers elsewhere.

Author: PQC-IoT Research Team
Date: March 2026
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple

# =============================================================================
# PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
PAPER_DIR = PROJECT_ROOT / "paper"

# Ensure directories exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =============================================================================
# BENCHMARK PARAMETERS
# =============================================================================

NUM_ITERATIONS = 1000          # Number of iterations per configuration
WARMUP_ITERATIONS = 50         # Warmup iterations to discard
SIGNIFICANCE_LEVEL = 0.05     # Alpha for statistical tests
RANDOM_SEED = 42              # For reproducibility
NOISE_STD_PERCENT = 5.0       # Standard deviation for simulation noise (%)

# =============================================================================
# TOPSIS WEIGHTS (Multi-Criteria Decision Analysis)
# =============================================================================

TOPSIS_WEIGHTS = {
    'total_time': 0.25,        # Combined keygen + encaps + decaps time
    'memory': 0.25,            # Peak memory usage
    'energy': 0.20,            # Estimated energy consumption
    'key_size': 0.15,          # Combined public + secret key size
    'ct_size': 0.15            # Ciphertext/signature size
}

# =============================================================================
# ALGORITHM DEFINITIONS
# =============================================================================

@dataclass
class AlgorithmSpec:
    """Specification for a PQC algorithm parameter set."""
    name: str                   # Human-readable name
    family: str                 # Algorithm family (Kyber, Dilithium, etc.)
    type: str                   # 'kem' or 'signature'
    security_level: int         # NIST security level (1, 2, 3, 5)
    liboqs_name: str           # Name in liboqs library
    # Reference performance data from pqm4 (ARM Cortex-M4 @ 24MHz)
    keygen_cycles: int         # Key generation cycles (thousands)
    encaps_sign_cycles: int    # Encapsulation/signing cycles (thousands)
    decaps_verify_cycles: int  # Decapsulation/verification cycles (thousands)
    pubkey_bytes: int          # Public key size
    seckey_bytes: int          # Secret key size
    ct_sig_bytes: int          # Ciphertext/signature size


# KEM Algorithms
KYBER_512 = AlgorithmSpec(
    name="Kyber-512",
    family="CRYSTALS-Kyber",
    type="kem",
    security_level=1,
    liboqs_name="Kyber512",
    keygen_cycles=514,
    encaps_sign_cycles=649,
    decaps_verify_cycles=586,
    pubkey_bytes=800,
    seckey_bytes=1632,
    ct_sig_bytes=768
)

KYBER_768 = AlgorithmSpec(
    name="Kyber-768",
    family="CRYSTALS-Kyber",
    type="kem",
    security_level=3,
    liboqs_name="Kyber768",
    keygen_cycles=893,
    encaps_sign_cycles=1117,
    decaps_verify_cycles=1019,
    pubkey_bytes=1184,
    seckey_bytes=2400,
    ct_sig_bytes=1088
)

KYBER_1024 = AlgorithmSpec(
    name="Kyber-1024",
    family="CRYSTALS-Kyber",
    type="kem",
    security_level=5,
    liboqs_name="Kyber1024",
    keygen_cycles=1347,
    encaps_sign_cycles=1598,
    decaps_verify_cycles=1480,
    pubkey_bytes=1568,
    seckey_bytes=3168,
    ct_sig_bytes=1568
)

NTRU_HPS_2048_509 = AlgorithmSpec(
    name="NTRU-HPS-2048-509",
    family="NTRU",
    type="kem",
    security_level=1,
    liboqs_name="NTRU-HPS-2048-509",
    keygen_cycles=119933,
    encaps_sign_cycles=45498,
    decaps_verify_cycles=69338,
    pubkey_bytes=699,
    seckey_bytes=935,
    ct_sig_bytes=699
)

NTRU_HPS_2048_677 = AlgorithmSpec(
    name="NTRU-HPS-2048-677",
    family="NTRU",
    type="kem",
    security_level=3,
    liboqs_name="NTRU-HPS-2048-677",
    keygen_cycles=186557,
    encaps_sign_cycles=67438,
    decaps_verify_cycles=105552,
    pubkey_bytes=930,
    seckey_bytes=1234,
    ct_sig_bytes=930
)

NTRU_HPS_4096_821 = AlgorithmSpec(
    name="NTRU-HPS-4096-821",
    family="NTRU",
    type="kem",
    security_level=5,
    liboqs_name="NTRU-HPS-4096-821",
    keygen_cycles=256485,
    encaps_sign_cycles=103832,
    decaps_verify_cycles=136916,
    pubkey_bytes=1230,
    seckey_bytes=1590,
    ct_sig_bytes=1230
)

# Signature Algorithms
DILITHIUM2 = AlgorithmSpec(
    name="Dilithium2",
    family="CRYSTALS-Dilithium",
    type="signature",
    security_level=2,
    liboqs_name="Dilithium2",
    keygen_cycles=1188,
    encaps_sign_cycles=4679,
    decaps_verify_cycles=1222,
    pubkey_bytes=1312,
    seckey_bytes=2528,
    ct_sig_bytes=2420
)

DILITHIUM3 = AlgorithmSpec(
    name="Dilithium3",
    family="CRYSTALS-Dilithium",
    type="signature",
    security_level=3,
    liboqs_name="Dilithium3",
    keygen_cycles=1995,
    encaps_sign_cycles=7060,
    decaps_verify_cycles=1957,
    pubkey_bytes=1952,
    seckey_bytes=4000,
    ct_sig_bytes=3293
)

DILITHIUM5 = AlgorithmSpec(
    name="Dilithium5",
    family="CRYSTALS-Dilithium",
    type="signature",
    security_level=5,
    liboqs_name="Dilithium5",
    keygen_cycles=2818,
    encaps_sign_cycles=7580,
    decaps_verify_cycles=3078,
    pubkey_bytes=2592,
    seckey_bytes=4864,
    ct_sig_bytes=4595
)

FALCON_512 = AlgorithmSpec(
    name="FALCON-512",
    family="FALCON",
    type="signature",
    security_level=1,
    liboqs_name="Falcon-512",
    keygen_cycles=54403,
    encaps_sign_cycles=40963,
    decaps_verify_cycles=625,
    pubkey_bytes=897,
    seckey_bytes=1281,
    ct_sig_bytes=666
)

FALCON_1024 = AlgorithmSpec(
    name="FALCON-1024",
    family="FALCON",
    type="signature",
    security_level=5,
    liboqs_name="Falcon-1024",
    keygen_cycles=148994,
    encaps_sign_cycles=83498,
    decaps_verify_cycles=1273,
    pubkey_bytes=1793,
    seckey_bytes=2305,
    ct_sig_bytes=1280
)

SPHINCS_128S = AlgorithmSpec(
    name="SPHINCS+-128s",
    family="SPHINCS+",
    type="signature",
    security_level=1,
    liboqs_name="SPHINCS+-SHA2-128s-simple",
    keygen_cycles=3796236,
    encaps_sign_cycles=52459060,
    decaps_verify_cycles=3870916,
    pubkey_bytes=32,
    seckey_bytes=64,
    ct_sig_bytes=7856
)

SPHINCS_192S = AlgorithmSpec(
    name="SPHINCS+-192s",
    family="SPHINCS+",
    type="signature",
    security_level=3,
    liboqs_name="SPHINCS+-SHA2-192s-simple",
    keygen_cycles=4519344,
    encaps_sign_cycles=68384288,
    decaps_verify_cycles=3879260,
    pubkey_bytes=48,
    seckey_bytes=96,
    ct_sig_bytes=16224
)

SPHINCS_256S = AlgorithmSpec(
    name="SPHINCS+-256s",
    family="SPHINCS+",
    type="signature",
    security_level=5,
    liboqs_name="SPHINCS+-SHA2-256s-simple",
    keygen_cycles=10975456,
    encaps_sign_cycles=160478208,
    decaps_verify_cycles=11478076,
    pubkey_bytes=64,
    seckey_bytes=128,
    ct_sig_bytes=29792
)

# All algorithms list
ALGORITHMS: List[AlgorithmSpec] = [
    # KEMs
    KYBER_512, KYBER_768, KYBER_1024,
    NTRU_HPS_2048_509, NTRU_HPS_2048_677, NTRU_HPS_4096_821,
    # Signatures
    DILITHIUM2, DILITHIUM3, DILITHIUM5,
    FALCON_512, FALCON_1024,
    SPHINCS_128S, SPHINCS_192S, SPHINCS_256S
]

# Group algorithms by type
KEM_ALGORITHMS = [a for a in ALGORITHMS if a.type == "kem"]
SIGNATURE_ALGORITHMS = [a for a in ALGORITHMS if a.type == "signature"]

# Algorithm lookup by name
ALGORITHM_BY_NAME: Dict[str, AlgorithmSpec] = {a.name: a for a in ALGORITHMS}

# =============================================================================
# DEVICE CLASS DEFINITIONS (RFC 7228)
# =============================================================================

@dataclass
class DeviceClass:
    """Specification for an IoT device class per RFC 7228."""
    name: str                   # Class 0, Class 1, Class 2
    ram_kb: int                 # Available RAM in KB
    flash_kb: int               # Available Flash/ROM in KB
    cpu_mhz: int                # CPU frequency in MHz
    processor: str              # Processor model
    voltage_v: float            # Operating voltage
    current_ma: float           # Current draw in mA
    cpi: float                  # Cycles per instruction
    cpu_cycles_budget: int      # Maximum CPU cycles per operation
    energy_budget_mj: float     # Maximum energy per operation (mJ)
    time_cap_ms: int            # Maximum time per operation (ms)
    example_devices: str        # Example real-world devices


DEVICE_CLASS_0 = DeviceClass(
    name="Class 0",
    ram_kb=10,
    flash_kb=100,
    cpu_mhz=16,
    processor="ARM Cortex-M0",
    voltage_v=1.8,
    current_ma=4.0,
    cpi=1.6,
    cpu_cycles_budget=1_000_000,      # 1M cycles
    energy_budget_mj=0.1,
    time_cap_ms=500,
    example_devices="Sensor tags, RFID"
)

DEVICE_CLASS_1 = DeviceClass(
    name="Class 1",
    ram_kb=50,
    flash_kb=250,
    cpu_mhz=48,
    processor="ARM Cortex-M3",
    voltage_v=3.3,
    current_ma=12.0,
    cpi=1.25,
    cpu_cycles_budget=10_000_000,     # 10M cycles
    energy_budget_mj=1.0,
    time_cap_ms=2000,
    example_devices="Smart locks, wearables"
)

DEVICE_CLASS_2 = DeviceClass(
    name="Class 2",
    ram_kb=250,
    flash_kb=1000,
    cpu_mhz=120,
    processor="ARM Cortex-M4",
    voltage_v=3.3,
    current_ma=30.0,
    cpi=1.0,
    cpu_cycles_budget=100_000_000,    # 100M cycles
    energy_budget_mj=10.0,
    time_cap_ms=10000,
    example_devices="Gateways, cameras, RPi"
)

DEVICE_CLASSES: List[DeviceClass] = [DEVICE_CLASS_0, DEVICE_CLASS_1, DEVICE_CLASS_2]

# Device class lookup by name
DEVICE_CLASS_BY_NAME: Dict[str, DeviceClass] = {d.name: d for d in DEVICE_CLASSES}

# =============================================================================
# OUTPUT FILE NAMES
# =============================================================================

# Raw data
RAW_BENCHMARKS_FILE = RAW_DATA_DIR / "benchmarks_raw.csv"

# Processed data
CLEANED_BENCHMARKS_FILE = PROCESSED_DATA_DIR / "benchmarks_cleaned.csv"

# Results
SUMMARY_STATS_FILE = RESULTS_DIR / "summary_statistics.csv"
ANOVA_RESULTS_FILE = RESULTS_DIR / "anova_results.csv"
TUKEY_RESULTS_FILE = RESULTS_DIR / "tukey_results.csv"
CORRELATION_MATRIX_FILE = RESULTS_DIR / "correlation_matrix.csv"
TOPSIS_RANKINGS_FILE = RESULTS_DIR / "topsis_rankings.csv"
FEASIBILITY_MATRIX_FILE = RESULTS_DIR / "feasibility_matrix.csv"

# Figures
FIGURE_FILES = {
    'fig1_framework': FIGURES_DIR / "fig1_framework.png",
    'fig2_keygen_time': FIGURES_DIR / "fig2_keygen_time.png",
    'fig3_encaps_time': FIGURES_DIR / "fig3_encaps_time.png",
    'fig4_decaps_time': FIGURES_DIR / "fig4_decaps_time.png",
    'fig5_memory': FIGURES_DIR / "fig5_memory.png",
    'fig6_boxplot': FIGURES_DIR / "fig6_boxplot.png",
    'fig7_correlation': FIGURES_DIR / "fig7_correlation.png",
    'fig8_radar': FIGURES_DIR / "fig8_radar.png",
    'fig9_feasibility': FIGURES_DIR / "fig9_feasibility.png",
    'fig10_topsis': FIGURES_DIR / "fig10_topsis.png",
    'fig11_tradeoff': FIGURES_DIR / "fig11_tradeoff.png",
    'fig12_energy': FIGURES_DIR / "fig12_energy.png",
    'fig15_migration_cost': FIGURES_DIR / "fig15_migration_cost.png",
    'fig16_memory_cascade': FIGURES_DIR / "fig16_memory_cascade.png",
    'fig17_tls_components': FIGURES_DIR / "fig17_tls_components.png",
    'fig18_energy_breakdown': FIGURES_DIR / "fig18_energy_breakdown.png",
    'fig19_topsis_sensitivity': FIGURES_DIR / "fig19_topsis_sensitivity.png"
}

# =============================================================================
# VISUALIZATION SETTINGS
# =============================================================================

# Color palette for algorithms (colorblind-friendly)
ALGORITHM_COLORS = {
    'CRYSTALS-Kyber': '#1f77b4',    # Blue
    'NTRU': '#ff7f0e',               # Orange
    'CRYSTALS-Dilithium': '#2ca02c', # Green
    'FALCON': '#d62728',             # Red
    'SPHINCS+': '#9467bd'            # Purple
}

# Color palette for device classes
DEVICE_CLASS_COLORS = {
    'Class 0': '#e74c3c',  # Red (most constrained)
    'Class 1': '#f39c12',  # Orange
    'Class 2': '#27ae60'   # Green (least constrained)
}

# Feasibility colors
FEASIBILITY_COLORS = {
    'FEASIBLE': '#27ae60',    # Green
    'MARGINAL': '#f39c12',    # Yellow/Orange
    'INFEASIBLE': '#e74c3c'   # Red
}

# Figure settings
FIGURE_DPI = 300
FIGURE_SIZE_SINGLE = (8, 6)
FIGURE_SIZE_DOUBLE = (12, 6)
FONT_SIZE_TITLE = 14
FONT_SIZE_LABEL = 12
FONT_SIZE_TICK = 10

# =============================================================================
# CSV COLUMN NAMES
# =============================================================================

BENCHMARK_COLUMNS = [
    'timestamp',
    'algorithm',
    'family',
    'type',
    'security_level',
    'device_class',
    'iteration',
    'keygen_time_ms',
    'encaps_time_ms',
    'decaps_time_ms',
    'total_time_ms',
    'peak_memory_kb',
    'pubkey_size_bytes',
    'seckey_size_bytes',
    'ct_size_bytes',
    'energy_mj',
    'status'  # SUCCESS or FAILED
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_total_configurations() -> int:
    """Calculate total number of benchmark configurations."""
    return len(ALGORITHMS) * len(DEVICE_CLASSES)


def get_total_iterations() -> int:
    """Calculate total number of benchmark iterations."""
    return get_total_configurations() * NUM_ITERATIONS


def print_config_summary():
    """Print a summary of the benchmark configuration."""
    print("=" * 60)
    print("PQC IoT Benchmark Configuration Summary")
    print("=" * 60)
    print(f"\nAlgorithms: {len(ALGORITHMS)}")
    for algo in ALGORITHMS:
        print(f"  - {algo.name} ({algo.family}, {algo.type}, Level {algo.security_level})")
    
    print(f"\nDevice Classes: {len(DEVICE_CLASSES)}")
    for dc in DEVICE_CLASSES:
        print(f"  - {dc.name}: {dc.ram_kb}KB RAM, {dc.cpu_mhz}MHz, {dc.example_devices}")
    
    print(f"\nBenchmark Parameters:")
    print(f"  - Iterations per config: {NUM_ITERATIONS}")
    print(f"  - Warmup iterations: {WARMUP_ITERATIONS}")
    print(f"  - Total configurations: {get_total_configurations()}")
    print(f"  - Total iterations: {get_total_iterations():,}")
    
    print(f"\nTOPSIS Weights:")
    for metric, weight in TOPSIS_WEIGHTS.items():
        print(f"  - {metric}: {weight:.2f}")
    
    print("=" * 60)


if __name__ == "__main__":
    print_config_summary()
