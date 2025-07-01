param(
    [string]$Command = "menu"
)

function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }

function Install-JMeter {
    Write-Info "Installing JMeter for Windows..."
    
    if (!(Test-Path "C:\jmeter")) {
        try {
            Write-Info "Downloading JMeter..."
            Invoke-WebRequest -Uri 'https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.5.zip' -OutFile 'jmeter.zip'
            Write-Info "Extracting JMeter..."
            Expand-Archive -Path 'jmeter.zip' -DestinationPath 'C:\'
            
            if (Test-Path "C:\apache-jmeter-5.5") {
                Move-Item "C:\apache-jmeter-5.5" "C:\jmeter"
            }
            
            Remove-Item 'jmeter.zip' -Force
            Write-Success "JMeter installed successfully!"
            Write-Warning "Add C:\jmeter\bin to your PATH"
            
        } catch {
            Write-Host "Failed to install JMeter" -ForegroundColor Red
        }
    } else {
        Write-Success "JMeter already installed"
    }
}

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "DeviceBridge Testing Suite" -ForegroundColor Cyan
    Write-Host "=========================="
    Write-Host ""
    Write-Host "1. Quick Test (2 min, 5 devices)"
    Write-Host "2. Demo Test (10 min, 23 devices)"
    Write-Host "3. Stress Test (5 min, 100 devices)"
    Write-Host "4. Load Test (Simulation + JMeter)"
    Write-Host "5. Setup"
    Write-Host "6. Install JMeter"
    Write-Host "7. View Data"
    Write-Host "8. Clean Data"
    Write-Host "9. Exit"
    Write-Host ""
    
    $choice = Read-Host "Choose option (1-9)"
    
    switch ($choice) {
        "1" { Run-QuickTest }
        "2" { Run-DemoTest }
        "3" { Run-StressTest }
        "4" { Run-LoadTest }
        "5" { Run-Setup }
        "6" { Install-JMeter }
        "7" { View-Data }
        "8" { Clean-Data }
        "9" { exit }
        default { 
            Write-Warning "Invalid choice"
            Start-Sleep -Seconds 1
            Show-Menu 
        }
    }
}

function Run-QuickTest {
    Write-Info "Running quick test..."
    & uv run python run_simulation.py quick
    Read-Host "Press Enter to continue"
    Show-Menu
}

function Run-DemoTest {
    Write-Info "Running demo test..."
    & uv run python run_simulation.py demo
    Read-Host "Press Enter to continue"
    Show-Menu
}

function Run-StressTest {
    Write-Info "Running stress test..."
    & uv run python run_simulation.py stress
    Read-Host "Press Enter to continue"
    Show-Menu
}

function Run-LoadTest {
    Write-Info "Running load test..."
    & uv run python run_combined_test.py load
    Read-Host "Press Enter to continue"
    Show-Menu
}

function Run-Setup {
    Write-Info "Running setup..."
    & uv run python setup.py
    Read-Host "Press Enter to continue"
    Show-Menu
}

function View-Data {
    Write-Info "Viewing data..."
    
    if (Test-Path "simulation.db") {
        Write-Success "Database found"
    } else {
        Write-Warning "No database found"
    }
    
    if (Test-Path "simulation_data") {
        Write-Success "Data files found:"
        Get-ChildItem "simulation_data"
    } else {
        Write-Warning "No data files found"
    }
    
    Read-Host "Press Enter to continue"
    Show-Menu
}

function Clean-Data {
    $confirm = Read-Host "Delete all data? (y/N)"
    
    if ($confirm -eq "y") {
        Write-Info "Cleaning data..."
        
        if (Test-Path "simulation_data") { Remove-Item "simulation_data" -Recurse -Force }
        if (Test-Path "simulation.db") { Remove-Item "simulation.db" -Force }
        if (Test-Path "simulation_config.json") { Remove-Item "simulation_config.json" -Force }
        
        Write-Success "Cleanup complete"
    }
    
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Main execution
switch ($Command) {
    "quick" { & uv run python run_simulation.py quick }
    "demo" { & uv run python run_simulation.py demo }
    "stress" { & uv run python run_simulation.py stress }
    "load" { & uv run python run_combined_test.py load }
    "setup" { & uv run python setup.py }
    "install-jmeter" { Install-JMeter }
    "view-data" { View-Data }
    "clean" { Clean-Data }
    "menu" { Show-Menu }
}