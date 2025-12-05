"""
PQC IoT Benchmark - Benchmark Runner
====================================

Main benchmark execution script. Supports both real cryptographic operations
(via liboqs) and simulation mode (using published pqm4 cycle counts).

Author: PQC-IoT Research Team
Date: March 2026
"""

import time
import tracemalloc
import csv
import random
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import asdict

# Import project modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ALGORITHMS, DEVICE_CLASSES, AlgorithmSpec, DeviceClass,
    NUM_ITERATIONS, WARMUP_ITERATIONS, RANDOM_SEED, NOISE_STD_PERCENT,
    RAW_BENCHMARKS_FILE, BENCHMARK_COLUMNS, PROJECT_ROOT
)
from constraint_simulator import ConstraintSimulator, get_simulator
from energy_model import EnergyModel, get_energy_model

# Try to import liboqs
LIBOQS_AVAILABLE = False
try:
    import oqs
    LIBOQS_AVAILABLE = True
    print("✓ liboqs library found - using real cryptographic operations")
except ImportError:
    print("✗ liboqs not available - using simulation mode with pqm4 reference data")


class BenchmarkRunner:
    """
    Main benchmark runner supporting both real and simulated benchmarks.
    
    If liboqs is available, performs real cryptographic operations.
    Otherwise, simulates results using published pqm4 cycle counts with
    Gaussian noise for realistic variation.
    """
    
    def __init__(self, use_simulation: bool = None):
        """
        Initialize the benchmark runner.
        
        Args:
            use_simulation: Force simulation mode if True, real if False.
                           If None, auto-detect based on liboqs availability.
        """
        if use_simulation is None:
            self.use_simulation = not LIBOQS_AVAILABLE
        else:
            self.use_simulation = use_simulation
        
        self.constraint_simulator = get_simulator()
        self.energy_model = get_energy_model()
        self.rng = np.random.RandomState(RANDOM_SEED)
        
        # Results storage
        self.results = []
        
        print(f"Benchmark mode: {'SIMULATION' if self.use_simulation else 'REAL (liboqs)'}")
    
    def run_benchmark(
        self,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass,
        iteration: int
    ) -> Dict[str, Any]:
        """
        Run a single benchmark iteration.
        
        Args:
            algorithm: Algorithm to benchmark
            device_class: Target device class
            iteration: Iteration number
            
        Returns:
            Dictionary with benchmark results
        """
        if self.use_simulation:
            return self._run_simulated_benchmark(algorithm, device_class, iteration)
        else:
            return self._run_real_benchmark(algorithm, device_class, iteration)
    
    def _run_simulated_benchmark(
        self,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass,
        iteration: int
    ) -> Dict[str, Any]:
        """
        Run a simulated benchmark using reference cycle counts.
        
        Adds Gaussian noise (5% std dev) for realistic variation.
        """
        # Add noise to cycle counts
        noise_factor = 1 + self.rng.normal(0, NOISE_STD_PERCENT / 100)
        
        keygen_cycles = int(algorithm.keygen_cycles * max(0.5, noise_factor))
        encaps_cycles = int(algorithm.encaps_sign_cycles * max(0.5, noise_factor))
        decaps_cycles = int(algorithm.decaps_verify_cycles * max(0.5, noise_factor))
        
        # Convert cycles to time for this device class
        keygen_time = self.energy_model.estimate_time_ms(keygen_cycles, device_class)
        encaps_time = self.energy_model.estimate_time_ms(encaps_cycles, device_class)
        decaps_time = self.energy_model.estimate_time_ms(decaps_cycles, device_class)
        total_time = keygen_time + encaps_time + decaps_time
        
        # Estimate memory usage (rough estimate based on key sizes + working memory)
        # Add some noise to memory too
        base_memory = algorithm.pubkey_bytes + algorithm.seckey_bytes + algorithm.ct_sig_bytes
        working_memory = base_memory * 2  # Rough estimate for working memory
        memory_kb = (base_memory + working_memory) / 1024 * max(0.8, 1 + self.rng.normal(0, 0.1))
        
        # Calculate energy
        total_cycles = keygen_cycles + encaps_cycles + decaps_cycles
        energy_mj = self.energy_model.estimate_energy_mj(total_cycles, device_class)
        
        # Check constraints
        constraint_result = self.constraint_simulator.check_all_constraints(
            elapsed_ms=total_time,
            memory_kb=memory_kb,
            cycles=total_cycles * 1000,  # Convert Kcycles to cycles
            energy_mj=energy_mj,
            device_class=device_class
        )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'algorithm': algorithm.name,
            'family': algorithm.family,
            'type': algorithm.type,
            'security_level': algorithm.security_level,
            'device_class': device_class.name,
            'iteration': iteration,
            'keygen_time_ms': keygen_time,
            'encaps_time_ms': encaps_time,
            'decaps_time_ms': decaps_time,
            'total_time_ms': total_time,
            'peak_memory_kb': memory_kb,
            'pubkey_size_bytes': algorithm.pubkey_bytes,
            'seckey_size_bytes': algorithm.seckey_bytes,
            'ct_size_bytes': algorithm.ct_sig_bytes,
            'energy_mj': energy_mj,
            'status': 'SUCCESS' if constraint_result.passed else 'FAILED'
        }
    
    def _run_real_benchmark(
        self,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass,
        iteration: int
    ) -> Dict[str, Any]:
        """
        Run a real benchmark using liboqs library.
        
        Measures actual cryptographic operations and applies CPU scaling
        to estimate times on target device class.
        """
        status = 'SUCCESS'
        
        try:
            # Start memory tracking
            tracemalloc.start()
            
            if algorithm.type == 'kem':
                result = self._benchmark_kem(algorithm, device_class)
            else:
                result = self._benchmark_signature(algorithm, device_class)
            
            # Get peak memory
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Scale times to target device
            scaling_factor = self.constraint_simulator.get_cpu_scaling_factor(device_class)
            keygen_time = result['keygen_time_ms'] * scaling_factor
            encaps_time = result['encaps_time_ms'] * scaling_factor
            decaps_time = result['decaps_time_ms'] * scaling_factor
            total_time = keygen_time + encaps_time + decaps_time
            
            memory_kb = peak / 1024
            
            # Estimate energy based on time
            # Reverse calculation: time_ms -> cycles -> energy
            total_cycles_k = int(total_time * device_class.cpu_mhz * 1000 / 1000)  # ms to Kcycles
            energy_mj = self.energy_model.estimate_energy_mj(total_cycles_k, device_class)
            
            # Check constraints
            constraint_result = self.constraint_simulator.check_all_constraints(
                elapsed_ms=total_time,
                memory_kb=memory_kb,
                cycles=total_cycles_k * 1000,
                energy_mj=energy_mj,
                device_class=device_class
            )
            
            if not constraint_result.passed:
                status = 'FAILED'
            
            return {
                'timestamp': datetime.now().isoformat(),
                'algorithm': algorithm.name,
                'family': algorithm.family,
                'type': algorithm.type,
                'security_level': algorithm.security_level,
                'device_class': device_class.name,
                'iteration': iteration,
                'keygen_time_ms': keygen_time,
                'encaps_time_ms': encaps_time,
                'decaps_time_ms': decaps_time,
                'total_time_ms': total_time,
                'peak_memory_kb': memory_kb,
                'pubkey_size_bytes': result['pubkey_size'],
                'seckey_size_bytes': result['seckey_size'],
                'ct_size_bytes': result['ct_size'],
                'energy_mj': energy_mj,
                'status': status
            }
            
        except Exception as e:
            tracemalloc.stop()
            print(f"Error benchmarking {algorithm.name}: {e}")
            return self._get_failed_result(algorithm, device_class, iteration, str(e))
    
    def _benchmark_kem(
        self,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass
    ) -> Dict[str, Any]:
        """Benchmark a KEM algorithm using liboqs."""
        kem = oqs.KeyEncapsulation(algorithm.liboqs_name)
        
        # Key generation
        start = time.perf_counter_ns()
        public_key = kem.generate_keypair()
        keygen_time = (time.perf_counter_ns() - start) / 1e6  # ns to ms
        
        # Encapsulation
        start = time.perf_counter_ns()
        ciphertext, shared_secret_enc = kem.encap_secret(public_key)
        encaps_time = (time.perf_counter_ns() - start) / 1e6
        
        # Decapsulation
        start = time.perf_counter_ns()
        shared_secret_dec = kem.decap_secret(ciphertext)
        decaps_time = (time.perf_counter_ns() - start) / 1e6
        
        return {
            'keygen_time_ms': keygen_time,
            'encaps_time_ms': encaps_time,
            'decaps_time_ms': decaps_time,
            'pubkey_size': len(public_key),
            'seckey_size': kem.length_secret_key,
            'ct_size': len(ciphertext)
        }
    
    def _benchmark_signature(
        self,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass
    ) -> Dict[str, Any]:
        """Benchmark a signature algorithm using liboqs."""
        sig = oqs.Signature(algorithm.liboqs_name)
        
        # Key generation
        start = time.perf_counter_ns()
        public_key = sig.generate_keypair()
        keygen_time = (time.perf_counter_ns() - start) / 1e6
        
        # Sign (using a test message)
        message = b"Test message for PQC benchmark" * 10  # ~300 bytes
        start = time.perf_counter_ns()
        signature = sig.sign(message)
        sign_time = (time.perf_counter_ns() - start) / 1e6
        
        # Verify
        start = time.perf_counter_ns()
        is_valid = sig.verify(message, signature, public_key)
        verify_time = (time.perf_counter_ns() - start) / 1e6
        
        return {
            'keygen_time_ms': keygen_time,
            'encaps_time_ms': sign_time,  # Using same field for sign
            'decaps_time_ms': verify_time,  # Using same field for verify
            'pubkey_size': len(public_key),
            'seckey_size': sig.length_secret_key,
            'ct_size': len(signature)  # Signature size
        }
    
    def _get_failed_result(
        self,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass,
        iteration: int,
        error: str
    ) -> Dict[str, Any]:
        """Generate a failed result entry."""
        return {
            'timestamp': datetime.now().isoformat(),
            'algorithm': algorithm.name,
            'family': algorithm.family,
            'type': algorithm.type,
            'security_level': algorithm.security_level,
            'device_class': device_class.name,
            'iteration': iteration,
            'keygen_time_ms': -1,
            'encaps_time_ms': -1,
            'decaps_time_ms': -1,
            'total_time_ms': -1,
            'peak_memory_kb': -1,
            'pubkey_size_bytes': algorithm.pubkey_bytes,
            'seckey_size_bytes': algorithm.seckey_bytes,
            'ct_size_bytes': algorithm.ct_sig_bytes,
            'energy_mj': -1,
            'status': f'ERROR: {error}'
        }
    
    def run_all_benchmarks(
        self,
        algorithms: list = None,
        device_classes: list = None,
        num_iterations: int = None,
        progress_callback = None
    ) -> list:
        """
        Run benchmarks for all configurations.
        
        Args:
            algorithms: List of algorithms to benchmark (default: all)
            device_classes: List of device classes (default: all)
            num_iterations: Number of iterations (default: from config)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of all benchmark results
        """
        if algorithms is None:
            algorithms = ALGORITHMS
        if device_classes is None:
            device_classes = DEVICE_CLASSES
        if num_iterations is None:
            num_iterations = NUM_ITERATIONS
        
        total_configs = len(algorithms) * len(device_classes)
        total_iterations = total_configs * num_iterations
        
        print(f"\nStarting benchmark run:")
        print(f"  Algorithms: {len(algorithms)}")
        print(f"  Device classes: {len(device_classes)}")
        print(f"  Iterations per config: {num_iterations}")
        print(f"  Total iterations: {total_iterations:,}")
        print("=" * 60)
        
        self.results = []
        config_count = 0
        
        for algorithm in algorithms:
            for device_class in device_classes:
                config_count += 1
                print(f"\n[{config_count}/{total_configs}] {algorithm.name} on {device_class.name}")
                
                for i in range(num_iterations):
                    result = self.run_benchmark(algorithm, device_class, i + 1)
                    self.results.append(result)
                    
                    # Progress update every 100 iterations
                    if (i + 1) % 100 == 0 or i == num_iterations - 1:
                        completed = (config_count - 1) * num_iterations + i + 1
                        pct = completed / total_iterations * 100
                        success_count = sum(1 for r in self.results[-100:] if r['status'] == 'SUCCESS')
                        print(f"  Progress: {i+1}/{num_iterations} iterations | "
                              f"Overall: {pct:.1f}% | Last 100 success rate: {success_count}%")
                        
                        if progress_callback:
                            progress_callback(completed, total_iterations)
        
        print(f"\n{'=' * 60}")
        print(f"Benchmark complete! Total results: {len(self.results):,}")
        
        return self.results
    
    def save_results(self, filepath: Path = None):
        """
        Save benchmark results to CSV file.
        
        Args:
            filepath: Output file path (default: from config)
        """
        if filepath is None:
            filepath = RAW_BENCHMARKS_FILE
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=BENCHMARK_COLUMNS)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"Results saved to: {filepath}")
        print(f"Total rows: {len(self.results):,}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the benchmark results."""
        if not self.results:
            return {'error': 'No results available'}
        
        total = len(self.results)
        success = sum(1 for r in self.results if r['status'] == 'SUCCESS')
        failed = total - success
        
        # Group by algorithm
        by_algorithm = {}
        for r in self.results:
            algo = r['algorithm']
            if algo not in by_algorithm:
                by_algorithm[algo] = {'total': 0, 'success': 0}
            by_algorithm[algo]['total'] += 1
            if r['status'] == 'SUCCESS':
                by_algorithm[algo]['success'] += 1
        
        return {
            'total_iterations': total,
            'successful': success,
            'failed': failed,
            'success_rate': success / total * 100 if total > 0 else 0,
            'by_algorithm': by_algorithm
        }


def run_quick_test():
    """Run a quick test with reduced iterations."""
    print("\n" + "=" * 60)
    print("QUICK TEST MODE (10 iterations per config)")
    print("=" * 60)
    
    runner = BenchmarkRunner()
    
    # Test with just a few algorithms
    test_algorithms = [ALGORITHMS[0], ALGORITHMS[6]]  # Kyber-512 and Dilithium2
    test_device_classes = [DEVICE_CLASSES[2]]  # Class 2 only
    
    runner.run_all_benchmarks(
        algorithms=test_algorithms,
        device_classes=test_device_classes,
        num_iterations=10
    )
    
    # Print summary
    summary = runner.get_summary()
    print(f"\nQuick Test Summary:")
    print(f"  Total iterations: {summary['total_iterations']}")
    print(f"  Success rate: {summary['success_rate']:.1f}%")
    
    return runner.results


def run_full_benchmark() -> 'pd.DataFrame':
    """
    Run the full benchmark suite and return results as DataFrame.
    
    This is the main entry point for programmatic use (e.g., from run_pipeline.py).
    
    Returns:
        pd.DataFrame: Benchmark results with all measurements
    """
    import pandas as pd
    
    print("\n" + "=" * 60)
    print("PQC IoT Full Benchmark")
    print("=" * 60)
    
    runner = BenchmarkRunner()
    
    # Run full benchmark
    runner.run_all_benchmarks()
    
    # Save results
    runner.save_results()
    
    # Return as DataFrame
    df = pd.DataFrame(runner.results)
    return df


def main():
    """Main entry point for benchmark execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='PQC IoT Benchmark Runner')
    parser.add_argument('--quick', action='store_true', help='Run quick test (10 iterations)')
    parser.add_argument('--iterations', type=int, default=NUM_ITERATIONS,
                       help=f'Number of iterations per config (default: {NUM_ITERATIONS})')
    parser.add_argument('--simulation', action='store_true', help='Force simulation mode')
    parser.add_argument('--output', type=str, help='Output CSV file path')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_test()
        return
    
    print("\n" + "=" * 60)
    print("PQC IoT Benchmark Runner")
    print("=" * 60)
    
    runner = BenchmarkRunner(use_simulation=args.simulation if args.simulation else None)
    
    # Run full benchmark
    runner.run_all_benchmarks(num_iterations=args.iterations)
    
    # Save results
    output_path = Path(args.output) if args.output else RAW_BENCHMARKS_FILE
    runner.save_results(output_path)
    
    # Print summary
    summary = runner.get_summary()
    print(f"\n{'=' * 60}")
    print("BENCHMARK SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total iterations: {summary['total_iterations']:,}")
    print(f"Successful: {summary['successful']:,} ({summary['success_rate']:.1f}%)")
    print(f"Failed: {summary['failed']:,}")
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
