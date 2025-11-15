"""
PQC IoT Benchmark - Constraint Simulator
=========================================

Simulates IoT device resource constraints for benchmark testing.
Uses Python's resource module for memory limits and time caps.

Author: PQC-IoT Research Team
Date: March 2026
"""

import resource
import platform
import sys
from typing import Optional, Tuple
from dataclasses import dataclass

# Import configuration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import DeviceClass, DEVICE_CLASSES, DEVICE_CLASS_BY_NAME


@dataclass
class ConstraintResult:
    """Result of constraint checking."""
    passed: bool
    memory_ok: bool
    time_ok: bool
    cycles_ok: bool
    energy_ok: bool
    message: str


class ConstraintSimulator:
    """
    Simulates IoT device resource constraints.
    
    Note: Memory limits via resource.setrlimit work on Unix-like systems.
    On macOS/Linux, we can set soft limits for virtual address space.
    """
    
    def __init__(self):
        self.original_memory_limit: Optional[Tuple[int, int]] = None
        self.current_device_class: Optional[DeviceClass] = None
        self.is_unix = platform.system() in ['Darwin', 'Linux']
        
    def set_memory_limit(self, device_class: DeviceClass) -> bool:
        """
        Set virtual memory limit to simulate device class RAM constraint.
        
        Args:
            device_class: Target device class configuration
            
        Returns:
            True if limit was set successfully, False otherwise
        """
        if not self.is_unix:
            print(f"Warning: Memory limits not supported on {platform.system()}")
            return False
        
        try:
            # Store original limit
            self.original_memory_limit = resource.getrlimit(resource.RLIMIT_AS)
            
            # Convert KB to bytes and set limit
            # We use a larger limit than the device RAM because Python itself 
            # needs memory, but we track actual PQC memory separately
            memory_bytes = device_class.ram_kb * 1024 * 100  # Allow more headroom
            
            # Set soft limit (hard limit unchanged)
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, self.original_memory_limit[1]))
            
            self.current_device_class = device_class
            return True
            
        except (ValueError, resource.error) as e:
            print(f"Warning: Could not set memory limit: {e}")
            return False
    
    def reset_constraints(self) -> bool:
        """
        Remove all resource limits, restoring original values.
        
        Returns:
            True if reset successful, False otherwise
        """
        if not self.is_unix:
            return True
            
        try:
            if self.original_memory_limit is not None:
                resource.setrlimit(resource.RLIMIT_AS, self.original_memory_limit)
                self.original_memory_limit = None
            
            self.current_device_class = None
            return True
            
        except (ValueError, resource.error) as e:
            print(f"Warning: Could not reset memory limit: {e}")
            return False
    
    def check_time_constraint(self, elapsed_ms: float, device_class: DeviceClass) -> bool:
        """
        Check if operation completed within device class time budget.
        
        Args:
            elapsed_ms: Elapsed time in milliseconds
            device_class: Target device class
            
        Returns:
            True if within time budget, False otherwise
        """
        return elapsed_ms <= device_class.time_cap_ms
    
    def check_memory_constraint(self, memory_kb: float, device_class: DeviceClass) -> bool:
        """
        Check if memory usage is within device class RAM limit.
        
        Args:
            memory_kb: Memory usage in kilobytes
            device_class: Target device class
            
        Returns:
            True if within RAM limit, False otherwise
        """
        return memory_kb <= device_class.ram_kb
    
    def check_cycles_constraint(self, cycles: int, device_class: DeviceClass) -> bool:
        """
        Check if CPU cycles are within device class budget.
        
        Args:
            cycles: CPU cycles used
            device_class: Target device class
            
        Returns:
            True if within cycles budget, False otherwise
        """
        return cycles <= device_class.cpu_cycles_budget
    
    def check_energy_constraint(self, energy_mj: float, device_class: DeviceClass) -> bool:
        """
        Check if energy consumption is within device class budget.
        
        Args:
            energy_mj: Energy consumption in millijoules
            device_class: Target device class
            
        Returns:
            True if within energy budget, False otherwise
        """
        return energy_mj <= device_class.energy_budget_mj
    
    def check_all_constraints(
        self,
        elapsed_ms: float,
        memory_kb: float,
        cycles: int,
        energy_mj: float,
        device_class: DeviceClass
    ) -> ConstraintResult:
        """
        Check all constraints for a given operation.
        
        Args:
            elapsed_ms: Elapsed time in milliseconds
            memory_kb: Memory usage in kilobytes
            cycles: CPU cycles used
            energy_mj: Energy consumption in millijoules
            device_class: Target device class
            
        Returns:
            ConstraintResult with detailed check results
        """
        memory_ok = self.check_memory_constraint(memory_kb, device_class)
        time_ok = self.check_time_constraint(elapsed_ms, device_class)
        cycles_ok = self.check_cycles_constraint(cycles, device_class)
        energy_ok = self.check_energy_constraint(energy_mj, device_class)
        
        all_passed = memory_ok and time_ok and cycles_ok and energy_ok
        
        # Build detailed message
        failures = []
        if not memory_ok:
            failures.append(f"Memory ({memory_kb:.1f}KB > {device_class.ram_kb}KB)")
        if not time_ok:
            failures.append(f"Time ({elapsed_ms:.1f}ms > {device_class.time_cap_ms}ms)")
        if not cycles_ok:
            failures.append(f"Cycles ({cycles:,} > {device_class.cpu_cycles_budget:,})")
        if not energy_ok:
            failures.append(f"Energy ({energy_mj:.3f}mJ > {device_class.energy_budget_mj}mJ)")
        
        if all_passed:
            message = "All constraints satisfied"
        else:
            message = "Failed: " + ", ".join(failures)
        
        return ConstraintResult(
            passed=all_passed,
            memory_ok=memory_ok,
            time_ok=time_ok,
            cycles_ok=cycles_ok,
            energy_ok=energy_ok,
            message=message
        )
    
    def get_cpu_scaling_factor(self, device_class: DeviceClass, host_mhz: int = 3000) -> float:
        """
        Get CPU scaling factor to convert host benchmark times to target device times.
        
        This is a simplified linear scaling based on clock frequency ratio.
        Real-world differences would also depend on architecture (8-bit vs 32-bit),
        memory latency, cache effects, etc.
        
        Args:
            device_class: Target device class
            host_mhz: Host CPU frequency (default 3000 MHz for modern desktops)
            
        Returns:
            Scaling factor (multiply host times by this factor)
        """
        return host_mhz / device_class.cpu_mhz
    
    def estimate_device_time_ms(
        self,
        host_time_ms: float,
        device_class: DeviceClass,
        host_mhz: int = 3000
    ) -> float:
        """
        Estimate execution time on target device given host measurement.
        
        Args:
            host_time_ms: Measured time on host in milliseconds
            device_class: Target device class
            host_mhz: Host CPU frequency
            
        Returns:
            Estimated time on target device in milliseconds
        """
        scaling_factor = self.get_cpu_scaling_factor(device_class, host_mhz)
        return host_time_ms * scaling_factor
    
    def cycles_to_time_ms(self, cycles: int, device_class: DeviceClass) -> float:
        """
        Convert CPU cycles to time in milliseconds for a device class.
        
        Args:
            cycles: Number of CPU cycles
            device_class: Target device class
            
        Returns:
            Time in milliseconds
        """
        # cycles / (MHz * 1e6) gives seconds, multiply by 1000 for ms
        # But cycles are in thousands (Kcycles), so multiply by 1000 first
        cycles_actual = cycles * 1000  # Convert Kcycles to cycles
        time_seconds = cycles_actual / (device_class.cpu_mhz * 1e6)
        return time_seconds * 1000  # Convert to ms
    
    def get_feasibility_rating(
        self,
        elapsed_ms: float,
        memory_kb: float,
        energy_mj: float,
        device_class: DeviceClass
    ) -> str:
        """
        Get feasibility rating for an algorithm on a device class.
        
        Returns:
            'FEASIBLE', 'MARGINAL', or 'INFEASIBLE'
        """
        # Check hard constraints
        memory_ratio = memory_kb / device_class.ram_kb
        time_ratio = elapsed_ms / device_class.time_cap_ms
        energy_ratio = energy_mj / device_class.energy_budget_mj
        
        max_ratio = max(memory_ratio, time_ratio, energy_ratio)
        
        if max_ratio > 1.0:
            return 'INFEASIBLE'
        elif max_ratio > 0.7:  # Using more than 70% of any budget
            return 'MARGINAL'
        else:
            return 'FEASIBLE'


# Global simulator instance
_simulator = None


def get_simulator() -> ConstraintSimulator:
    """Get the global constraint simulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = ConstraintSimulator()
    return _simulator


def set_memory_limit(device_class_name: str) -> bool:
    """
    Convenience function to set memory limit by device class name.
    
    Args:
        device_class_name: Name of device class ('Class 0', 'Class 1', 'Class 2')
        
    Returns:
        True if limit set successfully
    """
    device_class = DEVICE_CLASS_BY_NAME.get(device_class_name)
    if device_class is None:
        print(f"Unknown device class: {device_class_name}")
        return False
    return get_simulator().set_memory_limit(device_class)


def reset_constraints() -> bool:
    """Convenience function to reset all constraints."""
    return get_simulator().reset_constraints()


if __name__ == "__main__":
    # Test the constraint simulator
    print("Testing Constraint Simulator")
    print("=" * 50)
    
    simulator = ConstraintSimulator()
    
    for dc in DEVICE_CLASSES:
        print(f"\n{dc.name}:")
        print(f"  RAM: {dc.ram_kb} KB")
        print(f"  CPU: {dc.cpu_mhz} MHz")
        print(f"  Time cap: {dc.time_cap_ms} ms")
        print(f"  Energy budget: {dc.energy_budget_mj} mJ")
        
        # Test time conversion
        test_cycles = 1000  # 1000 Kcycles = 1M cycles
        time_ms = simulator.cycles_to_time_ms(test_cycles, dc)
        print(f"  1M cycles = {time_ms:.2f} ms")
        
        # Test constraint checking
        result = simulator.check_all_constraints(
            elapsed_ms=100,
            memory_kb=20,
            cycles=5_000_000,
            energy_mj=0.5,
            device_class=dc
        )
        print(f"  Test result: {result.message}")
