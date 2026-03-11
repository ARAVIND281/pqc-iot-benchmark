"""
Automated Unit Tests for MSP430 hardware emulator constraints.
Integrates into the primary CI/CD test suite for PQC evaluations.
"""
import unittest
from src.simulators.MSP430_simulator import MSP430Emulator

class TestMSP430Emulator(unittest.TestCase):
    
    def setUp(self):
        self.emulator = MSP430Emulator()
        
    def test_dynamic_power_calculation(self):
        # Validate energy output for a standard PQC operation (1.5M cycles)
        cycles = 1_500_000
        mj = self.emulator.calculate_dynamic_power(cycles)
        self.assertGreater(mj, 0.0)
        self.assertLess(mj, 1000.0)
        
    def test_thermal_penalty_scaling(self):
        # Hot microcontrollers consume more power due to leakage
        hot_emu = MSP430Emulator(baseline_temp_celsius=65.0)
        mj_normal = self.emulator.calculate_dynamic_power(1_000_000)
        mj_hot = hot_emu.calculate_dynamic_power(1_000_000)
        self.assertGreater(mj_hot, mj_normal)
        
    def test_memory_deployment_bounds(self):
        # Test minimal feasible constraints
        self.assertTrue(self.emulator.validate_memory_deployment(100, 100, 100))
        # Test extreme edge cases (e.g. SPHINCS+ signatures which are 40KB+)
        if self.emulator.ram_kb < 64:
            self.assertFalse(self.emulator.validate_memory_deployment(40000, 40000, 40000))
            
    def test_tls_fragmentation_math(self):
        res = self.emulator.estimate_tls_handshake_overhead(mtu_size=512)
        self.assertGreater(res['packets'], 2)
        
    def test_bus_delay_simulation_accuracy(self):
        delay = self.emulator._internal_bus_delay(2048)
        self.assertIsInstance(delay, int)

if __name__ == '__main__':
    unittest.main()
