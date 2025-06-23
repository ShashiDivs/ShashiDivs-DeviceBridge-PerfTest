#!/usr/bin/env python3
"""
DeviceBridge Synthetic Data Simulator
Simulates realistic medical device data streams for local testing
"""

import json
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import uuid

@dataclass
class DeviceConfig:
    """Configuration for a simulated device"""
    device_id: str
    device_type: str
    location: str
    update_interval: float  # seconds
    enabled: bool = True

class BaseDeviceSimulator:
    """Base class for all device simulators"""
    
    def __init__(self, config: DeviceConfig):
        self.config = config
        self.running = False
        self.thread = None
        self.data_history = []
        self.callbacks = []
        
    def add_callback(self, callback):
        """Add callback function to receive data"""
        self.callbacks.append(callback)
        
    def generate_base_data(self) -> Dict[str, Any]:
        """Generate base data common to all devices"""
        return {
            "device_id": self.config.device_id,
            "device_type": self.config.device_type,
            "location": self.config.location,
            "timestamp": datetime.now().isoformat(),
            "session_id": str(uuid.uuid4())[:8]
        }
    
    def generate_device_data(self) -> Dict[str, Any]:
        """Override this method in subclasses"""
        raise NotImplementedError
        
    def send_data(self, data: Dict[str, Any]):
        """Send data to all registered callbacks"""
        self.data_history.append(data)
        # Keep only last 100 records in memory
        if len(self.data_history) > 100:
            self.data_history.pop(0)
            
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in callback: {e}")
    
    def start(self):
        """Start the simulation"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        print(f"✅ Started {self.config.device_type} simulator: {self.config.device_id}")
    
    def stop(self):
        """Stop the simulation"""
        self.running = False
        if self.thread:
            self.thread.join()
        print(f"🛑 Stopped {self.config.device_type} simulator: {self.config.device_id}")
    
    def _run(self):
        """Main simulation loop"""
        while self.running:
            if self.config.enabled:
                try:
                    data = self.generate_device_data()
                    self.send_data(data)
                except Exception as e:
                    print(f"Error generating data for {self.config.device_id}: {e}")
            
            time.sleep(self.config.update_interval)

class InfusionPumpSimulator(BaseDeviceSimulator):
    """Simulates infusion pump device data"""
    
    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        # Pump state
        self.flow_rate = 5.0  # ml/hr
        self.pressure = 25.0  # psi
        self.battery_level = 100.0
        self.volume_infused = 0.0
        self.status = "running"
        self.alarms = []
        
    def generate_device_data(self) -> Dict[str, Any]:
        # Simulate realistic pump behavior
        self._update_pump_state()
        
        base_data = self.generate_base_data()
        pump_data = {
            "flow_rate": round(self.flow_rate, 2),
            "target_flow_rate": 5.0,
            "pressure": round(self.pressure, 1),
            "battery_level": round(self.battery_level, 1),
            "volume_infused": round(self.volume_infused, 2),
            "volume_remaining": round(500 - self.volume_infused, 2),
            "status": self.status,
            "alarms": self.alarms.copy(),
            "temperature": round(random.uniform(20, 25), 1),
            "pump_cycles": random.randint(1000, 5000)
        }
        
        return {**base_data, **pump_data}
    
    def _update_pump_state(self):
        # Simulate flow rate variations
        self.flow_rate += random.uniform(-0.2, 0.2)
        self.flow_rate = max(0, min(10, self.flow_rate))
        
        # Simulate pressure changes
        self.pressure += random.uniform(-2, 2)
        self.pressure = max(10, min(50, self.pressure))
        
        # Battery drain
        self.battery_level -= random.uniform(0.01, 0.05)
        self.battery_level = max(0, self.battery_level)
        
        # Volume tracking
        self.volume_infused += self.flow_rate * (self.config.update_interval / 3600)
        
        # Generate alarms
        self.alarms = []
        if self.battery_level < 20:
            self.alarms.append("LOW_BATTERY")
        if self.pressure > 45:
            self.alarms.append("HIGH_PRESSURE")
        if self.volume_infused > 450:
            self.alarms.append("LOW_VOLUME")

class PatientBedSimulator(BaseDeviceSimulator):
    """Simulates patient bed monitoring data"""
    
    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        # Bed state
        self.weight = 75.0  # kg
        self.position_angle = 30.0  # degrees
        self.occupancy = True
        self.movement_level = 2  # 0-5 scale
        self.bed_exit_risk = "low"
        
    def generate_device_data(self) -> Dict[str, Any]:
        self._update_bed_state()
        
        base_data = self.generate_base_data()
        bed_data = {
            "weight": round(self.weight, 1),
            "position_angle": round(self.position_angle, 1),
            "occupancy": self.occupancy,
            "movement_level": self.movement_level,
            "bed_exit_risk": self.bed_exit_risk,
            "rails_up": random.choice([True, False]),
            "call_light": random.choice([True, False]) if random.random() < 0.1 else False,
            "room_temperature": round(random.uniform(20, 24), 1),
            "humidity": round(random.uniform(40, 60), 1)
        }
        
        return {**base_data, **bed_data}
    
    def _update_bed_state(self):
        # Simulate patient movement
        if self.occupancy:
            self.weight += random.uniform(-0.5, 0.5)
            self.weight = max(50, min(150, self.weight))
            
            # Position changes
            self.position_angle += random.uniform(-5, 5)
            self.position_angle = max(0, min(70, self.position_angle))
            
            # Movement simulation
            self.movement_level = random.randint(0, 5)
            
            # Bed exit risk assessment
            if self.movement_level > 3 and random.random() < 0.3:
                self.bed_exit_risk = "high"
            elif self.movement_level > 1:
                self.bed_exit_risk = "medium"
            else:
                self.bed_exit_risk = "low"
        else:
            # Simulate occasional occupancy changes
            if random.random() < 0.05:  # 5% chance to become occupied
                self.occupancy = True
                self.weight = random.uniform(60, 120)

class VitalSignsSimulator(BaseDeviceSimulator):
    """Simulates vital signs monitor data"""
    
    def __init__(self, config: DeviceConfig):
        super().__init__(config)
        # Vital signs state
        self.heart_rate = 75
        self.blood_pressure_sys = 120
        self.blood_pressure_dia = 80
        self.oxygen_saturation = 98
        self.respiratory_rate = 16
        self.temperature = 36.5
        
    def generate_device_data(self) -> Dict[str, Any]:
        self._update_vitals()
        
        base_data = self.generate_base_data()
        vitals_data = {
            "heart_rate": self.heart_rate,
            "blood_pressure": {
                "systolic": self.blood_pressure_sys,
                "diastolic": self.blood_pressure_dia
            },
            "oxygen_saturation": round(self.oxygen_saturation, 1),
            "respiratory_rate": self.respiratory_rate,
            "temperature": round(self.temperature, 1),
            "ecg_rhythm": random.choice(["normal", "irregular", "atrial_fib"]),
            "alerts": self._generate_alerts()
        }
        
        return {**base_data, **vitals_data}
    
    def _update_vitals(self):
        # Realistic vital signs variations
        self.heart_rate += random.randint(-3, 3)
        self.heart_rate = max(45, min(150, self.heart_rate))
        
        self.blood_pressure_sys += random.randint(-5, 5)
        self.blood_pressure_sys = max(90, min(180, self.blood_pressure_sys))
        
        self.blood_pressure_dia += random.randint(-3, 3)
        self.blood_pressure_dia = max(50, min(110, self.blood_pressure_dia))
        
        self.oxygen_saturation += random.uniform(-1, 1)
        self.oxygen_saturation = max(85, min(100, self.oxygen_saturation))
        
        self.respiratory_rate += random.randint(-1, 1)
        self.respiratory_rate = max(8, min(30, self.respiratory_rate))
        
        self.temperature += random.uniform(-0.2, 0.2)
        self.temperature = max(35, min(40, self.temperature))
    
    def _generate_alerts(self):
        alerts = []
        if self.heart_rate > 100:
            alerts.append("TACHYCARDIA")
        elif self.heart_rate < 60:
            alerts.append("BRADYCARDIA")
            
        if self.blood_pressure_sys > 140:
            alerts.append("HYPERTENSION")
        elif self.blood_pressure_sys < 100:
            alerts.append("HYPOTENSION")
            
        if self.oxygen_saturation < 90:
            alerts.append("LOW_OXYGEN")
            
        if self.temperature > 38:
            alerts.append("FEVER")
            
        return alerts

class DeviceSimulatorManager:
    """Manages multiple device simulators"""
    
    def __init__(self):
        self.simulators = {}
        self.data_callbacks = []
        
    def add_simulator(self, device_type: str, config: DeviceConfig) -> BaseDeviceSimulator:
        """Add a new device simulator"""
        if device_type == "infusion_pump":
            simulator = InfusionPumpSimulator(config)
        elif device_type == "patient_bed":
            simulator = PatientBedSimulator(config)
        elif device_type == "vital_signs":
            simulator = VitalSignsSimulator(config)
        else:
            raise ValueError(f"Unknown device type: {device_type}")
        
        # Add global callbacks to simulator
        for callback in self.data_callbacks:
            simulator.add_callback(callback)
            
        self.simulators[config.device_id] = simulator
        return simulator
    
    def add_data_callback(self, callback):
        """Add callback to receive data from all simulators"""
        self.data_callbacks.append(callback)
        # Add to existing simulators
        for simulator in self.simulators.values():
            simulator.add_callback(callback)
    
    def start_all(self):
        """Start all simulators"""
        for simulator in self.simulators.values():
            simulator.start()
        print(f"🚀 Started {len(self.simulators)} device simulators")
    
    def stop_all(self):
        """Stop all simulators"""
        for simulator in self.simulators.values():
            simulator.stop()
        print("🛑 Stopped all device simulators")
    
    def get_simulator(self, device_id: str) -> Optional[BaseDeviceSimulator]:
        """Get simulator by device ID"""
        return self.simulators.get(device_id)
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get latest data from all simulators"""
        all_data = []
        for simulator in self.simulators.values():
            if simulator.data_history:
                all_data.append(simulator.data_history[-1])
        return all_data

def create_sample_devices(manager: DeviceSimulatorManager, count_per_type: int = 5):
    """Create sample devices for testing"""
    
    # Create infusion pumps
    for i in range(count_per_type):
        config = DeviceConfig(
            device_id=f"pump_{i+1:03d}",
            device_type="infusion_pump",
            location=f"Room_{random.randint(100, 599)}",
            update_interval=random.uniform(1, 3)
        )
        manager.add_simulator("infusion_pump", config)
    
    # Create patient beds
    for i in range(count_per_type):
        config = DeviceConfig(
            device_id=f"bed_{i+1:03d}",
            device_type="patient_bed", 
            location=f"Room_{random.randint(100, 599)}",
            update_interval=random.uniform(2, 5)
        )
        manager.add_simulator("patient_bed", config)
    
    # Create vital signs monitors
    for i in range(count_per_type):
        config = DeviceConfig(
            device_id=f"vitals_{i+1:03d}",
            device_type="vital_signs",
            location=f"Room_{random.randint(100, 599)}",
            update_interval=random.uniform(0.5, 2)
        )
        manager.add_simulator("vital_signs", config)

# Example usage
if __name__ == "__main__":
    # Create manager
    manager = DeviceSimulatorManager()
    
    # Add data callback to print received data
    def print_data(data):
        print(f"📊 {data['device_type']} {data['device_id']}: {data['timestamp']}")
    
    manager.add_data_callback(print_data)
    
    # Create sample devices
    create_sample_devices(manager, count_per_type=2)
    
    try:
        # Start simulation
        manager.start_all()
        
        # Let it run for 30 seconds
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopping simulation...")
    finally:
        manager.stop_all()