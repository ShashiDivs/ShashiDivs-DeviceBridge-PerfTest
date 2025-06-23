#!/usr/bin/env python3
"""
Data Sink Module
Handles storing and forwarding simulated device data
"""

import json
import csv
import sqlite3
import requests
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading
import queue

class DataSink:
    """Base class for data sinks"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        
    def write(self, data: Dict[str, Any]):
        """Write data to sink"""
        raise NotImplementedError
        
    def close(self):
        """Close sink and cleanup resources"""
        pass

class ConsoleDataSink(DataSink):
    """Prints data to console"""
    
    def __init__(self, format_type: str = "simple"):
        super().__init__("console")
        self.format_type = format_type
        
    def write(self, data: Dict[str, Any]):
        if not self.enabled:
            return
            
        if self.format_type == "simple":
            print(f"📊 {data['device_type']} {data['device_id']}: {data['timestamp']}")
        elif self.format_type == "detailed":
            print(f"📊 [{data['timestamp']}] {data['device_type']} {data['device_id']} @ {data['location']}")
            # Print key metrics based on device type
            if data['device_type'] == 'infusion_pump':
                print(f"   Flow: {data.get('flow_rate', 'N/A')} ml/hr, Pressure: {data.get('pressure', 'N/A')} psi")
            elif data['device_type'] == 'patient_bed':
                print(f"   Weight: {data.get('weight', 'N/A')} kg, Position: {data.get('position_angle', 'N/A')}°")
            elif data['device_type'] == 'vital_signs':
                print(f"   HR: {data.get('heart_rate', 'N/A')}, BP: {data.get('blood_pressure', {}).get('systolic', 'N/A')}/{data.get('blood_pressure', {}).get('diastolic', 'N/A')}")
        elif self.format_type == "json":
            print(json.dumps(data, indent=2))

class FileDataSink(DataSink):
    """Writes data to files"""
    
    def __init__(self, output_dir: str = "simulation_data", format: str = "json"):
        super().__init__("file")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.format = format
        self.file_handles = {}
        
    def write(self, data: Dict[str, Any]):
        if not self.enabled:
            return
            
        device_type = data['device_type']
        
        if self.format == "json":
            self._write_json(data, device_type)
        elif self.format == "csv":
            self._write_csv(data, device_type)
    
    def _write_json(self, data: Dict[str, Any], device_type: str):
        filename = self.output_dir / f"{device_type}_data.jsonl"
        
        with open(filename, 'a') as f:
            f.write(json.dumps(data) + '\n')
    
    def _write_csv(self, data: Dict[str, Any], device_type: str):
        filename = self.output_dir / f"{device_type}_data.csv"
        
        # Flatten nested dictionaries
        flat_data = self._flatten_dict(data)
        
        # Check if file exists to write headers
        file_exists = filename.exists()
        
        with open(filename, 'a', newline='') as f:
            if not file_exists:
                writer = csv.DictWriter(f, fieldnames=flat_data.keys())
                writer.writeheader()
            else:
                writer = csv.DictWriter(f, fieldnames=flat_data.keys())
            writer.writerow(flat_data)
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)

class DatabaseDataSink(DataSink):
    """Writes data to SQLite database"""
    
    def __init__(self, db_path: str = "simulation_data.db"):
        super().__init__("database")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._setup_tables()
        
    def _setup_tables(self):
        """Create tables for different device types"""
        cursor = self.conn.cursor()
        
        # Common fields table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                device_type TEXT,
                location TEXT,
                timestamp TEXT,
                session_id TEXT,
                data_json TEXT
            )
        ''')
        
        # Infusion pump specific table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS infusion_pump_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                timestamp TEXT,
                flow_rate REAL,
                target_flow_rate REAL,
                pressure REAL,
                battery_level REAL,
                volume_infused REAL,
                volume_remaining REAL,
                status TEXT,
                alarms TEXT
            )
        ''')
        
        # Patient bed specific table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_bed_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                timestamp TEXT,
                weight REAL,
                position_angle REAL,
                occupancy BOOLEAN,
                movement_level INTEGER,
                bed_exit_risk TEXT
            )
        ''')
        
        # Vital signs specific table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vital_signs_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                timestamp TEXT,
                heart_rate INTEGER,
                blood_pressure_sys INTEGER,
                blood_pressure_dia INTEGER,
                oxygen_saturation REAL,
                respiratory_rate INTEGER,
                temperature REAL
            )
        ''')
        
        self.conn.commit()
    
    def write(self, data: Dict[str, Any]):
        if not self.enabled:
            return
            
        with self.lock:
            cursor = self.conn.cursor()
            
            # Insert into common table
            cursor.execute('''
                INSERT INTO device_data 
                (device_id, device_type, location, timestamp, session_id, data_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['device_id'],
                data['device_type'], 
                data['location'],
                data['timestamp'],
                data['session_id'],
                json.dumps(data)
            ))
            
            # Insert into device-specific table
            device_type = data['device_type']
            if device_type == 'infusion_pump':
                cursor.execute('''
                    INSERT INTO infusion_pump_data
                    (device_id, timestamp, flow_rate, target_flow_rate, pressure, 
                     battery_level, volume_infused, volume_remaining, status, alarms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['device_id'], data['timestamp'], data['flow_rate'],
                    data['target_flow_rate'], data['pressure'], data['battery_level'],
                    data['volume_infused'], data['volume_remaining'], data['status'],
                    json.dumps(data['alarms'])
                ))
            elif device_type == 'patient_bed':
                cursor.execute('''
                    INSERT INTO patient_bed_data
                    (device_id, timestamp, weight, position_angle, occupancy,
                     movement_level, bed_exit_risk)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['device_id'], data['timestamp'], data['weight'],
                    data['position_angle'], data['occupancy'], data['movement_level'],
                    data['bed_exit_risk']
                ))
            elif device_type == 'vital_signs':
                cursor.execute('''
                    INSERT INTO vital_signs_data
                    (device_id, timestamp, heart_rate, blood_pressure_sys,
                     blood_pressure_dia, oxygen_saturation, respiratory_rate, temperature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['device_id'], data['timestamp'], data['heart_rate'],
                    data['blood_pressure']['systolic'], data['blood_pressure']['diastolic'],
                    data['oxygen_saturation'], data['respiratory_rate'], data['temperature']
                ))
            
            self.conn.commit()
    
    def close(self):
        self.conn.close()

class APIDataSink(DataSink):
    """Sends data to REST API"""
    
    def __init__(self, api_url: str, auth_token: Optional[str] = None, batch_size: int = 1):
        super().__init__("api")
        self.api_url = api_url
        self.auth_token = auth_token
        self.batch_size = batch_size
        self.batch_queue = queue.Queue()
        self.session = requests.Session()
        
        # Setup authentication
        if auth_token:
            self.session.headers.update({'Authorization': f'Bearer {auth_token}'})
        
        # Start batch processor
        self.batch_thread = threading.Thread(target=self._process_batches, daemon=True)
        self.batch_thread.start()
        
    def write(self, data: Dict[str, Any]):
        if not self.enabled:
            return
            
        self.batch_queue.put(data)
    
    def _process_batches(self):
        """Process data in batches"""
        batch = []
        
        while True:
            try:
                # Get data with timeout
                data = self.batch_queue.get(timeout=1)
                batch.append(data)
                
                # Send batch when full or queue is empty
                if len(batch) >= self.batch_size:
                    self._send_batch(batch)
                    batch = []
                    
            except queue.Empty:
                # Send any remaining data in batch
                if batch:
                    self._send_batch(batch)
                    batch = []
                continue
    
    def _send_batch(self, batch: List[Dict[str, Any]]):
        """Send batch to API"""
        try:
            if len(batch) == 1:
                # Single record
                response = self.session.post(
                    f"{self.api_url}/devices/data",
                    json=batch[0],
                    timeout=5
                )
            else:
                # Batch of records
                response = self.session.post(
                    f"{self.api_url}/devices/data/batch",
                    json={"data": batch},
                    timeout=10
                )
            
            if response.status_code in [200, 201]:
                print(f"✅ Sent {len(batch)} records to API")
            else:
                print(f"❌ API error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Failed to send to API: {e}")

class DataSinkManager:
    """Manages multiple data sinks"""
    
    def __init__(self):
        self.sinks = []
        
    def add_sink(self, sink: DataSink):
        """Add a data sink"""
        self.sinks.append(sink)
        print(f"➕ Added {sink.name} data sink")
    
    def write_to_all(self, data: Dict[str, Any]):
        """Write data to all enabled sinks"""
        for sink in self.sinks:
            if sink.enabled:
                try:
                    sink.write(data)
                except Exception as e:
                    print(f"❌ Error writing to {sink.name}: {e}")
    
    def enable_sink(self, name: str):
        """Enable a specific sink"""
        for sink in self.sinks:
            if sink.name == name:
                sink.enabled = True
                print(f"✅ Enabled {name} sink")
                return
        print(f"❌ Sink {name} not found")
    
    def disable_sink(self, name: str):
        """Disable a specific sink"""
        for sink in self.sinks:
            if sink.name == name:
                sink.enabled = False
                print(f"🔇 Disabled {name} sink")
                return
        print(f"❌ Sink {name} not found")
    
    def close_all(self):
        """Close all sinks"""
        for sink in self.sinks:
            try:
                sink.close()
            except Exception as e:
                print(f"❌ Error closing {sink.name}: {e}")

# Example usage
if __name__ == "__main__":
    # Create sink manager
    sink_manager = DataSinkManager()
    
    # Add different types of sinks
    sink_manager.add_sink(ConsoleDataSink("detailed"))
    sink_manager.add_sink(FileDataSink("simulation_output", "json"))
    sink_manager.add_sink(DatabaseDataSink("test_simulation.db"))
    
    # Example data
    sample_data = {
        "device_id": "pump_001",
        "device_type": "infusion_pump",
        "location": "Room_101",
        "timestamp": datetime.now().isoformat(),
        "session_id": "abc123",
        "flow_rate": 5.2,
        "target_flow_rate": 5.0,
        "pressure": 25.8,
        "battery_level": 85.5,
        "volume_infused": 125.0,
        "volume_remaining": 375.0,
        "status": "running",
        "alarms": ["LOW_BATTERY"]
    }
    
    # Write to all sinks
    sink_manager.write_to_all(sample_data)
    
    # Cleanup
    sink_manager.close_all()