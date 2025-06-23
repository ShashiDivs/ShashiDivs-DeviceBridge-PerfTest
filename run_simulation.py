#!/usr/bin/env python3
"""
DeviceBridge Synthetic Data Simulation - Main Entry Point
Simple script to run medical device data simulation locally
"""

import sys
import os
from pathlib import Path


from modules.simulation_runner import SimulationRunner

def run_quick_test():
    """Run a quick 2-minute test with minimal devices"""
    print("🧪 Running Quick Test (2 minutes)")
    print("=" * 50)
    
    runner = SimulationRunner()
    
    # Override config for quick test
    runner.config.config["simulation"]["duration_minutes"] = 2
    runner.config.config["devices"]["infusion_pump"]["count"] = 2
    runner.config.config["devices"]["patient_bed"]["count"] = 2
    runner.config.config["devices"]["vital_signs"]["count"] = 1
    runner.config.config["data_sinks"]["console"]["format"] = "simple"
    
    runner.setup_devices()
    runner.setup_data_sinks()
    runner.setup_data_flow()
    runner.start_simulation()

def run_demo():
    """Run a demo with realistic device counts"""
    print("🏥 Running Hospital Demo (10 minutes)")
    print("=" * 50)
    
    runner = SimulationRunner()
    
    # Demo configuration
    runner.config.config["simulation"]["duration_minutes"] = 10
    runner.config.config["devices"]["infusion_pump"]["count"] = 10
    runner.config.config["devices"]["patient_bed"]["count"] = 8
    runner.config.config["devices"]["vital_signs"]["count"] = 5
    runner.config.config["data_sinks"]["console"]["format"] = "detailed"
    
    runner.setup_devices()
    runner.setup_data_sinks()
    runner.setup_data_flow()
    runner.start_simulation()

def run_stress_test():
    """Run stress test with many devices"""
    print("⚡ Running Stress Test (5 minutes)")
    print("=" * 50)
    
    runner = SimulationRunner()
    
    # Stress test configuration
    runner.config.config["simulation"]["duration_minutes"] = 5
    runner.config.config["devices"]["infusion_pump"]["count"] = 50
    runner.config.config["devices"]["patient_bed"]["count"] = 30
    runner.config.config["devices"]["vital_signs"]["count"] = 20
    runner.config.config["data_sinks"]["console"]["enabled"] = False  # Too much output
    
    runner.setup_devices()
    runner.setup_data_sinks()
    runner.setup_data_flow()
    runner.start_simulation()

def run_custom():
    """Run with custom parameters"""
    print("⚙️  Custom Simulation")
    print("=" * 50)
    
    try:
        duration = int(input("Duration (minutes) [10]: ") or "10")
        pumps = int(input("Infusion pumps [5]: ") or "5")
        beds = int(input("Patient beds [5]: ") or "5")
        vitals = int(input("Vital signs monitors [3]: ") or "3")
        
        console_output = input("Show console output? (y/n) [y]: ").lower()
        console_enabled = console_output != 'n'
        
    except ValueError:
        print("❌ Invalid input. Using defaults.")
        duration, pumps, beds, vitals, console_enabled = 10, 5, 5, 3, True
    
    runner = SimulationRunner()
    
    # Custom configuration
    runner.config.config["simulation"]["duration_minutes"] = duration
    runner.config.config["devices"]["infusion_pump"]["count"] = pumps
    runner.config.config["devices"]["patient_bed"]["count"] = beds
    runner.config.config["devices"]["vital_signs"]["count"] = vitals
    runner.config.config["data_sinks"]["console"]["enabled"] = console_enabled
    
    runner.setup_devices()
    runner.setup_data_sinks()
    runner.setup_data_flow()
    runner.start_simulation()

def show_menu():
    """Show main menu"""
    print("\n🏥 DeviceBridge Synthetic Data Simulator")
    print("=" * 50)
    print("Choose a simulation type:")
    print()
    print("1. Quick Test     (2 min,  5 devices) - Fast validation")
    print("2. Demo          (10 min, 23 devices) - Realistic demo")  
    print("3. Stress Test    (5 min, 100 devices) - High load")
    print("4. Custom        (Your settings)      - Configure manually")
    print("5. Exit")
    print()

def main():
    """Main entry point"""
    
    # Check if modules directory exists
    modules_dir = Path(__file__).parent / "modules"
    if not modules_dir.exists():
        print("❌ Modules directory not found!")
        print("Please ensure the following files exist:")
        print("  - modules/device_simulator.py")
        print("  - modules/data_sink.py") 
        print("  - modules/simulation_runner.py")
        sys.exit(1)
    
    # Command line argument handling
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            run_quick_test()
        elif command == "demo":
            run_demo()
        elif command == "stress":
            run_stress_test()
        elif command == "custom":
            run_custom()
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage: python run_simulation.py [quick|demo|stress|custom]")
            sys.exit(1)
        return
    
    # Interactive menu
    while True:
        try:
            show_menu()
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                run_quick_test()
            elif choice == "2":
                run_demo()
            elif choice == "3":
                run_stress_test()
            elif choice == "4":
                run_custom()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                continue
                
            # Ask if user wants to run another simulation
            if input("\nRun another simulation? (y/n): ").lower() != 'y':
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()