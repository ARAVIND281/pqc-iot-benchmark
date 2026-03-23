# 🛡️ PQC IoT Benchmark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Paper Status](https://img.shields.io/badge/Paper-Submitted-success)](#)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-100%25-brightgreen)](#)

> **Performance Benchmarking of Post-Quantum Cryptographic Algorithms on Resource-Constrained IoT Devices: A Data-Driven Comparative Analysis**

A comprehensive, data-driven computational framework for evaluating NIST-standardized Post-Quantum Cryptographic (PQC) algorithms under severe, simulated Internet of Things (IoT) resource constraints (RFC 7228 device classes).

---

## 🎯 Abstract & Research Question
*Which NIST-standardized post-quantum algorithm offers the optimal trade-off between security resilience, computational overhead, memory footprint, and energy consumption for highly constrained IoT devices?*

This repository answers this by simulating device classes (ranging from 16MHz/10KB RAM microcontrollers up to 120MHz/250KB RAM edge gateways) and benchmarking **5 PQC families** (Kyber, Dilithium, FALCON, SPHINCS+, NTRU). It provides an automated, end-to-end pipeline that handles raw cryptography benchmark execution, IQR-based data cleaning, ANOVA statistical testing, multi-criteria decision analysis (TOPSIS), and IEEE-ready LaTeX visualizations.

---

## ✨ Key Contributions
1. **Comprehensive Scope:** Evaluates 14 distinct parameter sets across 5 primary PQC algorithms on 3 specific IoT device tiers.
2. **Multi-Criteria Ranking (TOPSIS):** First application of TOPSIS decision analysis applied to PQC selection for contextual IoT deployment.
3. **Data Science Integration:** Built-in Python pipelines that automatically conduct descriptive statistics, correlation matrices, and variance testing on benchmark runs.
4. **Reproducible Research:** One-click methodology using a built-in `Makefile` to go from source code to compiled IEEE manuscript.

---

## 🛠️ Algorithms Benchmarked

| Algorithm Family | Type | NIST Standard | Parameter Sets Tested |
|------------------|------|---------------|-----------------------|
| **CRYSTALS-Kyber** | KEM | FIPS 203 | Kyber-512, Kyber-768, Kyber-1024 |
| **CRYSTALS-Dilithium** | Signature | FIPS 204 | Dilithium2, Dilithium3, Dilithium5 |
| **FALCON** | Signature | Round 4 | FALCON-512, FALCON-1024 |
| **SPHINCS+** | Signature | FIPS 205 | SPHINCS+-128s, SPHINCS+-192s, 256s |
| **NTRU** | KEM | Round 3 | NTRU-HPS-2048-509, 677, 821 |

---

## 💻 Installation & Usage

### 1. Requirements & Setup
We provide a unified `Makefile` for streamlined execution. Ensure you have `python3` and `pdflatex` installed on your host system.

```bash
git clone https://github.com/yourusername/pqc-iot-benchmark.git
cd pqc-iot-benchmark

# Initialize the virtual environment and install dependencies
make setup
```

### 2. Execution Pipeline
You can run the entire benchmarking and analysis pipeline sequentially via the `Makefile`:

```bash
# 1. Run 1,000 algorithmic iterations across all IoT device parameters
make benchmark

# 2. Run IQR outlier cleaning, ANOVA testing, and TOPSIS rankings
#    This also outputs 19 IEEE-ready .png graphs to the figures/ directory
make analyze

# 3. Compile the final LaTeX manuscript into PDF
make paper
```

If you prefer to clean the environment (purging compiled scripts and `.aux` LaTeX builds):
```bash
make clean
```

---

## 📁 Repository Architecture

* 📂 **`src/`** *— Core Execution Framework*
  * 📄 `config.py` — Master configuration, tuning parameters, and TOPSIS weighting.
  * 📄 `benchmark_runner.py` — Main execution engine (Simulated or via liboqs).
  * 📄 `constraint_simulator.py` — Applies precise RFC 7228 memory and cycle capping.
  * 📄 `energy_model.py` — Granular Joule/Watt estimation based on Cortex-M processors.
* 📂 **`analysis/`** *— Data Science Pipeline*
  * 📄 `data_cleaning.py` — IQR outlier truncation and dataset validation.
  * 📄 `descriptive_stats.py` — Generation of Mean, Median, and Q1-Q3 summaries.
  * 📄 `topsis_ranking.py` — Multi-criteria algorithmic decision ranking matrix.
  * 📄 `generate_figures.py` — Matplotlib/Seaborn graphic production routines.
* 📂 **`data/`** *— Structured Evaluation Results*
  * 📁 `raw/` — Pre-cleaning CSV benchmark performance logs.
  * 📁 `processed/` — Post-cleaning, curated CSV records.
  * 📁 `results/` — Final statistical, ANOVA, and feasibility matrices.
* 📂 **`figures/`** *— Auto-generated IEEE-ready visualizations (.png).*
* 📂 **`paper/`** *— Final IEEE Manuscript Components*
  * 📄 `main.tex` — LaTeX Source Code.
  * 📄 `references.bib` — Project bibliography.
* 📄 **`Makefile`** — One-click commands for streamlined, reproducible execution.
* 📄 **`run_pipeline.py`** — Primary Python orchestration entry point linking all computational stages.

---

## 📊 Evaluation Metrics
The pipeline natively monitors and evaluates:
- **Latencies (ms):** Key Generation, Encapsulation/Signing, Decapsulation/Verification
- **Hardware Footprint:** Peak RAM Memory Usage (KB)
- **Transmission Sizing:** Public/Secret Key Size (bytes), Ciphertext/Signature Size (bytes)
- **Power Usage:** Estimated Energy constraints (mJ)

---

## 📚 Citation

If you utilize this benchmarking framework in your own academic work, please cite our paper:

```bibtex
@article{pqc_iot_benchmark_2026,
  author={Your Name and Co-Authors},
  title={Performance Benchmarking of Post-Quantum Cryptographic Algorithms on Resource-Constrained IoT Devices: A Data-Driven Comparative Analysis},
  journal={IEEE Access},
  year={2026},
  publisher={IEEE}
}
```

## ⚖️ License
This project is open-sourced under the **MIT License**.
