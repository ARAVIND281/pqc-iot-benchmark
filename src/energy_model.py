"""
PQC IoT Benchmark - Energy Model
================================

Energy consumption estimation model for IoT devices.
Based on CPU cycle counts and ARM Cortex-M datasheet specifications.

Energy formula: E = (CPU_cycles × CPI × V × I) / f

Author: PQC-IoT Research Team
Date: March 2026
"""

from dataclasses import dataclass
from typing import Dict, Optional

# Import configuration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import DeviceClass, DEVICE_CLASSES, AlgorithmSpec


@dataclass
class EnergyEstimate:
    """Energy estimation result."""
    energy_mj: float           # Energy in millijoules
    power_mw: float            # Power in milliwatts
    time_ms: float             # Time in milliseconds
    cycles: int                # CPU cycles
    device_class: str          # Device class name
    breakdown: Dict[str, float]  # Per-operation breakdown


class EnergyModel:
    """
    Energy consumption estimation model for IoT devices.
    
    Uses the energy formula: E = (CPU_cycles × CPI × V × I) / f
    
    Where:
    - CPU_cycles: Number of clock cycles for the operation
    - CPI: Cycles per instruction (depends on processor)
    - V: Operating voltage (volts)
    - I: Current draw (amperes)
    - f: Clock frequency (Hz)
    
    Reference values from ARM Cortex-M datasheets:
    
    | Processor     | Voltage (V) | Current (mA) | CPI  | Clock (MHz) |
    |---------------|-------------|--------------|------|-------------|
    | Cortex-M0     | 1.8         | 4            | 1.6  | 16          |
    | Cortex-M3     | 3.3         | 12           | 1.25 | 48          |
    | Cortex-M4     | 3.3         | 30           | 1.0  | 120         |
    """
    
    def __init__(self):
        pass
    
    def estimate_energy_mj(
        self,
        cycles_k: int,
        device_class: DeviceClass
    ) -> float:
        """
        Estimate energy consumption in millijoules.
        
        Args:
            cycles_k: CPU cycles in thousands (Kcycles)
            device_class: Target device class
            
        Returns:
            Energy consumption in millijoules
        """
        # Convert Kcycles to cycles
        cycles = cycles_k * 1000
        
        # Get device parameters
        V = device_class.voltage_v
        I = device_class.current_ma / 1000  # Convert mA to A
        f = device_class.cpu_mhz * 1e6      # Convert MHz to Hz
        cpi = device_class.cpi
        
        # Calculate time in seconds
        # Time = cycles / frequency
        time_s = cycles / f
        
        # Calculate power in watts
        # P = V × I
        power_w = V * I
        
        # Calculate energy in joules
        # E = P × t
        energy_j = power_w * time_s
        
        # Convert to millijoules
        energy_mj = energy_j * 1000
        
        return energy_mj
    
    def estimate_power_mw(self, device_class: DeviceClass) -> float:
        """
        Calculate power consumption in milliwatts for a device class.
        
        Args:
            device_class: Target device class
            
        Returns:
            Power consumption in milliwatts
        """
        power_w = device_class.voltage_v * (device_class.current_ma / 1000)
        return power_w * 1000  # Convert to mW
    
    def estimate_time_ms(self, cycles_k: int, device_class: DeviceClass) -> float:
        """
        Estimate execution time in milliseconds.
        
        Args:
            cycles_k: CPU cycles in thousands (Kcycles)
            device_class: Target device class
            
        Returns:
            Execution time in milliseconds
        """
        cycles = cycles_k * 1000
        f = device_class.cpu_mhz * 1e6
        time_s = cycles / f
        return time_s * 1000  # Convert to ms
    
    def estimate_algorithm_energy(
        self,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass
    ) -> EnergyEstimate:
        """
        Estimate total energy for a complete algorithm operation
        (keygen + encaps/sign + decaps/verify).
        
        Args:
            algorithm: Algorithm specification
            device_class: Target device class
            
        Returns:
            Detailed energy estimate with breakdown
        """
        # Calculate per-operation energy
        keygen_energy = self.estimate_energy_mj(algorithm.keygen_cycles, device_class)
        encaps_energy = self.estimate_energy_mj(algorithm.encaps_sign_cycles, device_class)
        decaps_energy = self.estimate_energy_mj(algorithm.decaps_verify_cycles, device_class)
        
        # Total energy
        total_energy = keygen_energy + encaps_energy + decaps_energy
        
        # Calculate time
        keygen_time = self.estimate_time_ms(algorithm.keygen_cycles, device_class)
        encaps_time = self.estimate_time_ms(algorithm.encaps_sign_cycles, device_class)
        decaps_time = self.estimate_time_ms(algorithm.decaps_verify_cycles, device_class)
        total_time = keygen_time + encaps_time + decaps_time
        
        # Total cycles
        total_cycles = (algorithm.keygen_cycles + algorithm.encaps_sign_cycles + 
                       algorithm.decaps_verify_cycles) * 1000
        
        # Power
        power_mw = self.estimate_power_mw(device_class)
        
        return EnergyEstimate(
            energy_mj=total_energy,
            power_mw=power_mw,
            time_ms=total_time,
            cycles=total_cycles,
            device_class=device_class.name,
            breakdown={
                'keygen_mj': keygen_energy,
                'encaps_mj': encaps_energy,
                'decaps_mj': decaps_energy,
                'keygen_ms': keygen_time,
                'encaps_ms': encaps_time,
                'decaps_ms': decaps_time
            }
        )
    
    def estimate_operation_energy(
        self,
        operation: str,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass
    ) -> float:
        """
        Estimate energy for a single operation.
        
        Args:
            operation: 'keygen', 'encaps', 'sign', 'decaps', or 'verify'
            algorithm: Algorithm specification
            device_class: Target device class
            
        Returns:
            Energy in millijoules
        """
        if operation == 'keygen':
            cycles = algorithm.keygen_cycles
        elif operation in ['encaps', 'sign']:
            cycles = algorithm.encaps_sign_cycles
        elif operation in ['decaps', 'verify']:
            cycles = algorithm.decaps_verify_cycles
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return self.estimate_energy_mj(cycles, device_class)
    
    def compare_energy_profiles(
        self,
        algorithms: list,
        device_class: DeviceClass
    ) -> Dict[str, EnergyEstimate]:
        """
        Compare energy profiles of multiple algorithms on a device class.
        
        Args:
            algorithms: List of AlgorithmSpec objects
            device_class: Target device class
            
        Returns:
            Dictionary mapping algorithm names to energy estimates
        """
        return {
            algo.name: self.estimate_algorithm_energy(algo, device_class)
            for algo in algorithms
        }
    
    def get_energy_ranking(
        self,
        algorithms: list,
        device_class: DeviceClass
    ) -> list:
        """
        Rank algorithms by energy consumption (lowest first).
        
        Args:
            algorithms: List of AlgorithmSpec objects
            device_class: Target device class
            
        Returns:
            List of (algorithm_name, energy_mj) tuples, sorted by energy
        """
        profiles = self.compare_energy_profiles(algorithms, device_class)
        rankings = [(name, est.energy_mj) for name, est in profiles.items()]
        return sorted(rankings, key=lambda x: x[1])
    
    def check_energy_feasibility(
        self,
        algorithm: AlgorithmSpec,
        device_class: DeviceClass
    ) -> tuple:
        """
        Check if algorithm is energy-feasible on device class.
        
        Args:
            algorithm: Algorithm specification
            device_class: Target device class
            
        Returns:
            Tuple of (is_feasible, energy_mj, budget_mj, ratio)
        """
        estimate = self.estimate_algorithm_energy(algorithm, device_class)
        budget = device_class.energy_budget_mj
        ratio = estimate.energy_mj / budget
        is_feasible = ratio <= 1.0
        
        return (is_feasible, estimate.energy_mj, budget, ratio)


# Global model instance
_model = None


def get_energy_model() -> EnergyModel:
    """Get the global energy model instance."""
    global _model
    if _model is None:
        _model = EnergyModel()
    return _model


def estimate_energy(cycles_k: int, device_class_name: str) -> float:
    """
    Convenience function to estimate energy.
    
    Args:
        cycles_k: CPU cycles in thousands
        device_class_name: Name of device class
        
    Returns:
        Energy in millijoules
    """
    from config import DEVICE_CLASS_BY_NAME
    device_class = DEVICE_CLASS_BY_NAME[device_class_name]
    return get_energy_model().estimate_energy_mj(cycles_k, device_class)


if __name__ == "__main__":
    from config import ALGORITHMS, DEVICE_CLASSES, KEM_ALGORITHMS, SIGNATURE_ALGORITHMS
    
    print("Energy Model Test")
    print("=" * 70)
    
    model = EnergyModel()
    
    # Test for each device class
    for dc in DEVICE_CLASSES:
        print(f"\n{dc.name} ({dc.processor} @ {dc.cpu_mhz} MHz)")
        print(f"  Power: {model.estimate_power_mw(dc):.1f} mW")
        print(f"  Energy budget: {dc.energy_budget_mj} mJ")
        print("-" * 70)
        
        # Test each algorithm
        print(f"  {'Algorithm':<25} {'Energy (mJ)':<15} {'Time (ms)':<15} {'Feasible'}")
        print(f"  {'-'*25} {'-'*15} {'-'*15} {'-'*10}")
        
        for algo in ALGORITHMS:
            estimate = model.estimate_algorithm_energy(algo, dc)
            feasible, energy, budget, ratio = model.check_energy_feasibility(algo, dc)
            status = "Yes" if feasible else f"No ({ratio:.1f}x)"
            print(f"  {algo.name:<25} {energy:>12.4f}   {estimate.time_ms:>12.2f}   {status}")
        
    # Show energy rankings for Class 2
    print("\n" + "=" * 70)
    print("Energy Rankings for Class 2 (Best to Worst)")
    print("-" * 70)
    
    print("\nKEM Algorithms:")
    rankings = model.get_energy_ranking(KEM_ALGORITHMS, DEVICE_CLASSES[2])
    for i, (name, energy) in enumerate(rankings, 1):
        print(f"  {i}. {name}: {energy:.4f} mJ")
    
    print("\nSignature Algorithms:")
    rankings = model.get_energy_ranking(SIGNATURE_ALGORITHMS, DEVICE_CLASSES[2])
    for i, (name, energy) in enumerate(rankings, 1):
        print(f"  {i}. {name}: {energy:.4f} mJ")
