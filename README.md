# PQC-IoT-Benchmark

## Performance Benchmarking of Post-Quantum Cryptographic Algorithms on Resource-Constrained IoT Devices

A comprehensive, data-driven benchmarking framework for evaluating NIST-standardized Post-Quantum Cryptographic (PQC) algorithms under simulated IoT resource constraints.

### Research Question

> Which NIST-standardized post-quantum cryptographic algorithm offers the optimal trade-off between security strength, computational overhead, memory footprint, and energy consumption for each class of resource-constrained IoT device?

### Algorithms Benchmarked

| Algorithm | Type | NIST Standard | Parameter Sets |
|-----------|------|---------------|----------------|
| CRYSTALS-Kyber | KEM | FIPS 203 | Kyber-512, Kyber-768, Kyber-1024 |
| CRYSTALS-Dilithium | Signature | FIPS 204 | Dilithium2, Dilithium3, Dilithium5 |
| FALCON | Signature | Round 4 | FALCON-512, FALCON-1024 |
| SPHINCS+ | Signature | FIPS 205 | SPHINCS+-128s, SPHINCS+-192s, SPHINCS+-256s |
| NTRU | KEM | Round 3 | NTRU-HPS-2048-509, NTRU-HPS-2048-677, NTRU-HPS-4096-821 |

### IoT Device Classes (RFC 7228)

| Class | RAM | CPU | Example Devices |
|-------|-----|-----|-----------------|
| Class 0 | <10 KB | 16 MHz | Sensor tags, RFID |
| Class 1 | ~50 KB | 48 MHz | Smart locks, wearables |
| Class 2 | ~250 KB | 120 MHz | Gateways, cameras |

### Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run benchmarks
python src/benchmark_runner.py

# Run analysis pipeline
python analysis/data_cleaning.py
python analysis/descriptive_stats.py
python analysis/statistical_tests.py
python analysis/correlation_analysis.py
python analysis/topsis_ranking.py

# Generate figures
python analysis/generate_figures.py

# Compile paper (requires LaTeX)
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

### Project Structure

```
pqc-iot-benchmark/
├── src/                    # Core benchmark code
│   ├── config.py           # All parameters and constants
│   ├── benchmark_runner.py # Main benchmark execution
│   ├── constraint_simulator.py # IoT constraint simulation
│   └── energy_model.py     # Energy estimation
├── analysis/               # Data analysis pipeline
│   ├── data_cleaning.py    # Outlier removal, validation
│   ├── descriptive_stats.py # Summary statistics
│   ├── statistical_tests.py # ANOVA, Tukey HSD
│   ├── correlation_analysis.py # Pearson correlation
│   ├── topsis_ranking.py   # Multi-criteria ranking
│   └── generate_figures.py # All visualizations
├── data/                   # Benchmark data
│   ├── raw/                # Raw benchmark CSVs
│   ├── processed/          # Cleaned data
│   └── results/            # Analysis outputs
├── figures/                # Generated plots
├── paper/                  # IEEE-format paper
│   ├── main.tex
│   ├── references.bib
│   └── paper.pdf
└── tests/                  # Unit tests
```

### Metrics Measured

1. **Key Generation Time** (ms)
2. **Encapsulation/Signing Time** (ms)
3. **Decapsulation/Verification Time** (ms)
4. **Peak Memory Usage** (KB)
5. **Public Key Size** (bytes)
6. **Secret Key Size** (bytes)
7. **Ciphertext/Signature Size** (bytes)
8. **Estimated Energy** (mJ)

### Statistical Analysis

- **Descriptive Statistics**: Mean, median, std, quartiles
- **ANOVA**: One-way ANOVA with Tukey HSD post-hoc tests
- **Correlation**: Pearson correlation matrix
- **TOPSIS**: Multi-criteria decision analysis for algorithm ranking

### Novel Contributions

1. First comprehensive benchmarking of all 5 NIST PQC finalists across all 3 RFC 7228 IoT device classes
2. First application of TOPSIS multi-criteria decision analysis to PQC algorithm selection for IoT
3. Reusable, open-source benchmarking framework

### Citation

If you use this work, please cite:

```bibtex
@article{pqc_iot_benchmark_2026,
  title={Performance Benchmarking of Post-Quantum Cryptographic Algorithms on Resource-Constrained IoT Devices: A Data-Driven Comparative Analysis},
  author={[Authors]},
  journal={IEEE Access},
  year={2026}
}
```

### License

MIT License

### References

- [NIST Post-Quantum Cryptography Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [RFC 7228: Terminology for Constrained-Node Networks](https://tools.ietf.org/html/rfc7228)
- [Open Quantum Safe Project](https://openquantumsafe.org/)
- [pqm4: PQC on ARM Cortex-M4](https://github.com/mupq/pqm4)
