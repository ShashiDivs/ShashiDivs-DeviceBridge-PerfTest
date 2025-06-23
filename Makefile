# DeviceBridge Synthetic Data Simulation - UV Version

.PHONY: help install quick demo stress custom clean

help:
	@echo "DeviceBridge Synthetic Data Simulator (UV)"
	@echo "========================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install dependencies with UV"
	@echo ""
	@echo "Run Simulations:"
	@echo "  make quick      - Quick test (2 min, 5 devices)"
	@echo "  make demo       - Demo simulation (10 min, 23 devices)" 
	@echo "  make stress     - Stress test (5 min, 100 devices)"

# Installation with UV
install:
	@echo "📦 Installing dependencies with UV..."
	uv add requests pandas
	@echo "✅ Dependencies installed!"

# Quick test simulation
quick:
	@echo "🧪 Running quick test simulation..."
	uv run python run_simulation.py quick

# Demo simulation  
demo:
	@echo "🏥 Running demo simulation..."
	uv run python run_simulation.py demo

# Stress test simulation
stress:
	@echo "⚡ Running stress test simulation..."
	uv run python run_simulation.py stress

# Custom simulation
custom:
	@echo "⚙️  Running custom simulation..."
	uv run python run_simulation.py custom

# Interactive menu
menu:
	@echo "🏥 Starting interactive menu..."
	uv run python run_simulation.py

# Setup
setup:
	@echo "🔧 Running setup..."
	uv run python setup.py

# Clean simulation data
clean:
	@echo "🧹 Cleaning simulation data..."
	rm -rf simulation_data/
	rm -f simulation.db
	rm -f simulation_stats_*.json
	rm -f simulation_config.json
	@echo "✅ Cleanup complete!"