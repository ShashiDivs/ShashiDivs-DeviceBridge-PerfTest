#!/usr/bin/env python3
"""
Simulation Runner - Main module to orchestrate synthetic data simulation
"""

import json
import time
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

from modules.device_simulator import DeviceSimulatorManager, DeviceConfig, create_sample_devices
from modules.data_sink import DataSinkManager, ConsoleDataSink, FileDataSink, DatabaseDataSink, APIDataSink

class SimulationConfig:
    """Configuration for simulation"""
    
    def __init__(self, config_file: str = "simulation_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = self.get_default_config()
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "simulation": {
                "duration_minutes": 60,
                "devices_per_type": 5,
                "output_directory": "simulation_data"
            },
            "devices": {
                "infusion_pump": {
                    "enabled": True,
                    "count": 5,
                    "update_interval_range": [1, 3]
                },
                "patient_bed": {
                    "enabled": True,
                    "count": 5,
                    "update_interval_range": [2, 5]
                },
                "vital_signs": {
                    "enabled": True,
                    "count": 3,
                    "update_interval_range": [0.5, 2]
                }
            },
            "data_sinks": {
                "console": {
                    "enabled": True,
                    "format": "detailed"
                },
                "file": {
                    "enabled": True,
                    "format": "json",
                    "directory": "simulation_data"
                },
                "database": {
                    "enabled": True,
                    "file": "simulation.db"
                },
                "api": {
                    "enabled": False,
                    "url": "http://localhost:8080/api",
                    "auth_token": None,  # Fixed: None instead of null
                    "batch_size": 10
                }
            },
            "scenarios": {
                "normal_operation": {
                    "description": "Normal hospital operation",
                    "alarm_probability": 0.05,
                    "device_failure_probability": 0.01
                },
                "high_activity": {
                    "description": "High patient activity period",
                    "alarm_probability": 0.15,
                    "device_failure_probability": 0.02
                },
                "emergency": {
                    "description": "Emergency situation",
                    "alarm_probability": 0.30,
                    "device_failure_probability": 0.05
                }
            }
        }

class SimulationRunner:
    """Main simulation runner"""
    
    def __init__(self, config_file: str = "simulation_config.json"):
        self.config = SimulationConfig(config_file)
        self.device_manager = DeviceSimulatorManager()
        self.sink_manager = DataSinkManager()
        self.running = False
        self.start_time = None
        self.stats = {
            "total_messages": 0,
            "messages_per_device_type": {},
            "start_time": None,
            "end_time": None
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def setup_devices(self):
        """Setup device simulators based on configuration"""
        print("🏥 Setting up device simulators...")
        
        import random
        
        for device_type, device_config in self.config.config["devices"].items():
            if not device_config["enabled"]:
                continue
                
            count = device_config["count"]
            interval_range = device_config["update_interval_range"]
            
            for i in range(count):
                config = DeviceConfig(
                    device_id=f"{device_type}_{i+1:03d}",
                    device_type=device_type,
                    location=f"Room_{random.randint(100, 999)}",
                    update_interval=random.uniform(interval_range[0], interval_range[1])
                )
                
                self.device_manager.add_simulator(device_type, config)
                
                # Initialize stats
                if device_type not in self.stats["messages_per_device_type"]:
                    self.stats["messages_per_device_type"][device_type] = 0
        
        print(f"✅ Setup {len(self.device_manager.simulators)} device simulators")
    
    def setup_data_sinks(self):
        """Setup data sinks based on configuration"""
        print("📊 Setting up data sinks...")
        
        sink_config = self.config.config["data_sinks"]
        
        # Console sink
        if sink_config["console"]["enabled"]:
            console_sink = ConsoleDataSink(sink_config["console"]["format"])
            self.sink_manager.add_sink(console_sink)
        
        # File sink
        if sink_config["file"]["enabled"]:
            file_sink = FileDataSink(
                sink_config["file"]["directory"],
                sink_config["file"]["format"]
            )
            self.sink_manager.add_sink(file_sink)
        
        # Database sink
        if sink_config["database"]["enabled"]:
            db_sink = DatabaseDataSink(sink_config["database"]["file"])
            self.sink_manager.add_sink(db_sink)
        
        # API sink
        if sink_config["api"]["enabled"]:
            api_sink = APIDataSink(
                sink_config["api"]["url"],
                sink_config["api"]["auth_token"],
                sink_config["api"]["batch_size"]
            )
            self.sink_manager.add_sink(api_sink)
        
        print(f"✅ Setup {len(self.sink_manager.sinks)} data sinks")
    
    def setup_data_flow(self):
        """Connect device simulators to data sinks"""
        print("🔗 Connecting data flow...")
        
        def data_callback(data):
            # Update statistics
            self.stats["total_messages"] += 1
            device_type = data["device_type"]
            self.stats["messages_per_device_type"][device_type] += 1
            
            # Send to all sinks
            self.sink_manager.write_to_all(data)
        
        self.device_manager.add_data_callback(data_callback)
        print("✅ Data flow connected")
    
    def start_simulation(self, duration_minutes: int = None):
        """Start the simulation"""
        if duration_minutes is None:
            duration_minutes = self.config.config["simulation"]["duration_minutes"]
        
        print(f"\n🚀 Starting DeviceBridge synthetic data simulation...")
        print(f"⏱️  Duration: {duration_minutes} minutes")
        print(f"📱 Devices: {len(self.device_manager.simulators)}")
        print(f"📊 Data sinks: {len(self.sink_manager.sinks)}")
        print("=" * 60)
        
        self.running = True
        self.start_time = datetime.now()
        self.stats["start_time"] = self.start_time.isoformat()
        
        # Start all device simulators
        self.device_manager.start_all()
        
        try:
            # Run for specified duration
            end_time = self.start_time + timedelta(minutes=duration_minutes)
            
            while self.running and datetime.now() < end_time:
                time.sleep(1)
                
                # Print periodic stats
                if (datetime.now() - self.start_time).seconds % 30 == 0:
                    self._print_stats()
            
        except KeyboardInterrupt:
            print("\n⏹️ Simulation interrupted by user")
        finally:
            self.stop_simulation()
    
    def stop_simulation(self):
        """Stop the simulation"""
        if not self.running:
            return
            
        print("\n🛑 Stopping simulation...")
        self.running = False
        
        # Stop all simulators
        self.device_manager.stop_all()
        
        # Close all sinks
        self.sink_manager.close_all()
        
        # Update final stats
        self.stats["end_time"] = datetime.now().isoformat()
        
        # Print final summary
        self._print_final_summary()
    
    def _print_stats(self):
        """Print current statistics"""
        if not self.start_time:
            return
            
        elapsed = datetime.now() - self.start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        
        total_messages = self.stats["total_messages"]
        rate = total_messages / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        
        print(f"\n📈 Stats - Elapsed: {elapsed_minutes:.1f}m | "
              f"Messages: {total_messages} | Rate: {rate:.1f}/sec")
        
        for device_type, count in self.stats["messages_per_device_type"].items():
            print(f"   {device_type}: {count} messages")
    
    def _print_final_summary(self):
        """Print final simulation summary"""
        print("\n" + "=" * 60)
        print("📋 SIMULATION SUMMARY")
        print("=" * 60)
        
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            print(f"⏱️  Duration: {elapsed}")
            print(f"📊 Total messages: {self.stats['total_messages']}")
            
            if elapsed.total_seconds() > 0:
                rate = self.stats['total_messages'] / elapsed.total_seconds()
                print(f"📈 Average rate: {rate:.2f} messages/second")
        
        print(f"\n📱 Messages by device type:")
        for device_type, count in self.stats["messages_per_device_type"].items():
            print(f"   {device_type}: {count}")
        
        # Save stats to file
        stats_file = f"simulation_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        print(f"\n💾 Statistics saved to: {stats_file}")
        
        print("\n✅ Simulation completed successfully!")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n📡 Received signal {signum}")
        self.stop_simulation()
        sys.exit(0)
    
    def run_scenario(self, scenario_name: str, duration_minutes: int = 10):
        """Run a predefined scenario"""
        scenarios = self.config.config.get("scenarios", {})
        
        if scenario_name not in scenarios:
            print(f"❌ Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {list(scenarios.keys())}")
            return
        
        scenario = scenarios[scenario_name]
        print(f"🎭 Running scenario: {scenario_name}")
        print(f"📝 Description: {scenario['description']}")
        
        # Modify device behavior based on scenario
        # This is a simplified implementation - you could extend this
        # to actually modify simulator parameters
        
        self.start_simulation(duration_minutes)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeviceBridge Synthetic Data Simulator')
    parser.add_argument('--config', default='simulation_config.json', 
                       help='Configuration file path')
    parser.add_argument('--duration', type=int, default=60, 
                       help='Simulation duration in minutes')
    parser.add_argument('--scenario', 
                       help='Run predefined scenario (normal_operation, high_activity, emergency)')
    parser.add_argument('--devices-per-type', type=int, default=5,
                       help='Number of devices per type to simulate')
    parser.add_argument('--quiet', action='store_true',
                       help='Disable console output')
    
    args = parser.parse_args()
    
    # Create simulation runner
    runner = SimulationRunner(args.config)
    
    # Override config with command line args
    if args.devices_per_type != 5:
        for device_type in runner.config.config["devices"]:
            runner.config.config["devices"][device_type]["count"] = args.devices_per_type
    
    if args.quiet:
        runner.config.config["data_sinks"]["console"]["enabled"] = False
    
    try:
        # Setup simulation
        runner.setup_devices()
        runner.setup_data_sinks()
        runner.setup_data_flow()
        
        # Run simulation
        if args.scenario:
            runner.run_scenario(args.scenario, args.duration)
        else:
            runner.start_simulation(args.duration)
            
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()