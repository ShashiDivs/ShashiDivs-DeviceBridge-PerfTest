#!/usr/bin/env python3
"""
JMeter Integration Module
Runs JMeter tests alongside synthetic data simulation
"""

import subprocess
import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional

class JMeterRunner:
    """Manages JMeter test execution"""
    
    def __init__(self, jmeter_home: str = None):
        self.jmeter_home = jmeter_home
        self.jmeter_cmd = self._find_jmeter()
        self.running = False
        self.results = {}
        
    def _find_jmeter(self) -> str:
        """Find JMeter executable"""
        if self.jmeter_home:
            return f"{self.jmeter_home}/bin/jmeter"
        
        # Try common locations
        locations = [
            "C:\\jmeter\\bin\\jmeter.bat",  # Windows direct path
            "/opt/jmeter/bin/jmeter",
            "/usr/local/bin/jmeter", 
            "jmeter"  # If in PATH
        ]
        
        for location in locations:
            try:
                result = subprocess.run([location, "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return location
            except:
                continue
        
        raise Exception("JMeter not found. Please install JMeter.")
    
    def run_test(self, test_plan: str, duration: int = 300, 
                 users: int = 10, ramp_up: int = 60) -> Dict[str, Any]:
        """Run JMeter test"""
        
        results_file = f"jmeter_results_{int(time.time())}.jtl"
        report_dir = f"jmeter_report_{int(time.time())}"
        
        cmd = [
            self.jmeter_cmd,
            "-n",  # Non-GUI mode
            "-t", test_plan,  # Test plan file
            "-l", results_file,  # Results file
            "-e",  # Generate report
            "-o", report_dir,  # Report output directory
            f"-Jusers={users}",
            f"-Jramp_up={ramp_up}",
            f"-Jduration={duration}"
        ]
        
        print(f"🚀 Starting JMeter test: {test_plan}")
        print(f"   Users: {users}, Ramp-up: {ramp_up}s, Duration: {duration}s")
        
        self.running = True
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ JMeter test completed successfully")
                return {
                    "status": "success",
                    "results_file": results_file,
                    "report_dir": report_dir,
                    "summary": self._parse_results(results_file)
                }
            else:
                print(f"❌ JMeter test failed: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
                
        finally:
            self.running = False
    
    def _parse_results(self, results_file: str) -> Dict[str, Any]:
        """Parse JMeter results file"""
        try:
            import pandas as pd
            
            df = pd.read_csv(results_file)
            
            return {
                "total_requests": len(df),
                "avg_response_time": df['elapsed'].mean(),
                "min_response_time": df['elapsed'].min(),
                "max_response_time": df['elapsed'].max(),
                "error_rate": (df['success'] == False).sum() / len(df) * 100,
                "throughput": len(df) / (df['timeStamp'].max() - df['timeStamp'].min()) * 1000
            }
        except Exception as e:
            return {"error": f"Failed to parse results: {e}"}