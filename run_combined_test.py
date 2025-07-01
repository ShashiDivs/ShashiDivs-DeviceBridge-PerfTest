#!/usr/bin/env python3
"""
Combined DeviceBridge Testing
Runs synthetic data simulation + JMeter load testing together
"""

import sys
import time
import threading
from pathlib import Path

# Add modules to path

from modules.simulation_runner import SimulationRunner
from modules.jmeter_runner import JMeterRunner

class CombinedTestRunner:
    """Runs simulation and JMeter tests together"""
    
    def __init__(self):
        self.simulation_runner = SimulationRunner()
        self.jmeter_runner = JMeterRunner()
        self.simulation_thread = None
        self.jmeter_thread = None
        
    def run_combined_test(self, scenario: str = "load"):
        """Run combined simulation + JMeter test"""
        
        scenarios = {
            "light": {
                "sim_devices": 5,
                "sim_duration": 10,
                "jmeter_users": 5,
                "jmeter_duration": 300
            },
            "load": {
                "sim_devices": 20,
                "sim_duration": 15,
                "jmeter_users": 20,
                "jmeter_duration": 600
            },
            "stress": {
                "sim_devices": 50,
                "sim_duration": 10,
                "jmeter_users": 50,
                "jmeter_duration": 300
            }
        }
        
        if scenario not in scenarios:
            print(f"❌ Unknown scenario: {scenario}")
            return
            
        config = scenarios[scenario]
        
        print(f"🚀 Starting Combined DeviceBridge Test - {scenario.upper()}")
        print("=" * 60)
        print(f"📊 Synthetic Data: {config['sim_devices']} devices for {config['sim_duration']} min")
        print(f"⚡ JMeter Load: {config['jmeter_users']} users for {config['jmeter_duration']} sec")
        print("=" * 60)
        
        try:
            # Phase 1: Start synthetic data simulation
            print("🏥 Phase 1: Starting synthetic data generation...")
            self._start_simulation(config)
            
            # Wait a bit for data to populate
            print("⏳ Waiting 30 seconds for initial data...")
            time.sleep(30)
            
            # Phase 2: Start JMeter load test
            print("⚡ Phase 2: Starting JMeter load test...")
            jmeter_results = self._start_jmeter_test(config)
            
            # Phase 3: Let simulation continue briefly
            print("📊 Phase 3: Continuing data generation...")
            time.sleep(60)
            
            # Stop simulation
            self.simulation_runner.stop_simulation()
            
            # Show results
            self._show_results(jmeter_results)
            
        except KeyboardInterrupt:
            print("\n⏹️ Test interrupted by user")
            self._cleanup()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self._cleanup()
    
    def _start_simulation(self, config):
        """Start simulation in background"""
        # Configure simulation
        sim_config = self.simulation_runner.config.config
        sim_config["simulation"]["duration_minutes"] = config["sim_duration"]
        sim_config["devices"]["infusion_pump"]["count"] = config["sim_devices"] // 3
        sim_config["devices"]["patient_bed"]["count"] = config["sim_devices"] // 3
        sim_config["devices"]["vital_signs"]["count"] = config["sim_devices"] // 3
        sim_config["data_sinks"]["console"]["enabled"] = False  # Less noise
        
        # Setup and start
        self.simulation_runner.setup_devices()
        self.simulation_runner.setup_data_sinks()
        self.simulation_runner.setup_data_flow()
        
        # Start in thread
        self.simulation_thread = threading.Thread(
            target=self.simulation_runner.start_simulation,
            args=(config["sim_duration"],)
        )
        self.simulation_thread.start()
    
    def _start_jmeter_test(self, config):
        """Start JMeter test"""
        test_plan = "jmeter/devicebridge_test.jmx"
        
        if not Path(test_plan).exists():
            print(f"❌ JMeter test plan not found: {test_plan}")
            return None
            
        return self.jmeter_runner.run_test(
            test_plan=test_plan,
            duration=config["jmeter_duration"],
            users=config["jmeter_users"],
            ramp_up=60
        )
    
    def _show_results(self, jmeter_results):
        """Display test results"""
        print("\n" + "=" * 60)
        print("📋 COMBINED TEST RESULTS")
        print("=" * 60)
        
        # Simulation stats
        sim_stats = self.simulation_runner.stats
        print(f"\n📊 Synthetic Data Simulation:")
        print(f"   Total messages: {sim_stats['total_messages']}")
        for device_type, count in sim_stats["messages_per_device_type"].items():
            print(f"   {device_type}: {count}")
        
        # JMeter stats
        if jmeter_results and jmeter_results.get("status") == "success":
            summary = jmeter_results.get("summary", {})
            print(f"\n⚡ JMeter Load Test:")
            print(f"   Total requests: {summary.get('total_requests', 'N/A')}")
            print(f"   Avg response time: {summary.get('avg_response_time', 'N/A')} ms")
            print(f"   Error rate: {summary.get('error_rate', 'N/A')}%")
            print(f"   Throughput: {summary.get('throughput', 'N/A')} req/sec")
        
        print("\n✅ Combined test completed!")
    
    def _cleanup(self):
        """Clean up resources"""
        if self.simulation_runner.running:
            self.simulation_runner.stop_simulation()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Combined DeviceBridge Testing')
    parser.add_argument('scenario', choices=['light', 'load', 'stress'], 
                       default='load', nargs='?',
                       help='Test scenario to run')
    
    args = parser.parse_args()
    
    runner = CombinedTestRunner()
    runner.run_combined_test(args.scenario)

if __name__ == "__main__":
    main()