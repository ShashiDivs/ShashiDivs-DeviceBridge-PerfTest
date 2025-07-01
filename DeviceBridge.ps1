param(
    [string]$Command = "menu"
)

function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "DeviceBridge Testing Suite" -ForegroundColor Cyan
    Write-Host "=========================="
    Write-Host ""
    Write-Host "Simulation Tests:" -ForegroundColor Green
    Write-Host "1. Quick Test (2 min, 5 devices)"
    Write-Host "2. Demo Test (10 min, 23 devices)"
    Write-Host "3. Stress Test (5 min, 100 devices)"
    Write-Host ""
    Write-Host "API Load Tests:" -ForegroundColor Yellow
    Write-Host "4. JMeter Only (uses existing data)"
    Write-Host "5. Combined Test (fresh simulation + JMeter)"
    Write-Host ""
    Write-Host "Management:" -ForegroundColor Cyan
    Write-Host "6. Setup"
    Write-Host "7. View Data"
    Write-Host "8. Clean Data"
    Write-Host "9. Exit"
    Write-Host ""
    
    $choice = Read-Host "Choose option (1-9)"
    
    switch ($choice) {
        "1" { Run-QuickTest }
        "2" { Run-DemoTest }
        "3" { Run-StressTest }
        "4" { Run-JMeterOnly }
        "5" { Run-CombinedTest }
        "6" { Run-Setup }
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

function Run-JMeterOnly {
    Write-Info "Running JMeter API load test against existing data..."
    
    # Check if we have existing data
    if (!(Test-Path "simulation.db")) {
        Write-Warning "No existing data found!"
        Write-Info "Please run a simulation first (options 1, 2, or 3)"
        Read-Host "Press Enter to continue"
        Show-Menu
        return
    }
    
    # Show current data stats
    Write-Success "Found existing data:"
    if (Test-Path "simulation.db") {
        try {
            & sqlite3 simulation.db "SELECT device_type, COUNT(*) as count FROM device_data GROUP BY device_type;"
        } catch {
            Write-Info "Database found but sqlite3 not available"
        }
    }
    
    # Check if JMeter test plan exists
    if (!(Test-Path "jmeter/devicebridge_test.jmx")) {
        Write-Warning "JMeter test plan not found at jmeter/devicebridge_test.jmx"
        Write-Info "Creating basic JMeter test plan..."
        Create-BasicJMeterPlan
    }
    
    # Run JMeter test
    Write-Info "Starting JMeter load test..."
    Write-Info "- 20 virtual users"
    Write-Info "- 5 minute test duration"
    Write-Info "- Testing API endpoints with existing data"
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $resultsFile = "jmeter_results_$timestamp.jtl"
    
    try {
        & jmeter -n -t "jmeter/devicebridge_test.jmx" -l $resultsFile -Jusers=20 -Jduration=300 -Jramp_up=60
        
        Write-Success "JMeter test completed!"
        Write-Info "Results saved to: $resultsFile"
        
        # Show basic results if possible
        if (Test-Path $resultsFile) {
            $lineCount = (Get-Content $resultsFile | Measure-Object -Line).Lines
            Write-Success "Total requests: $lineCount"
        }
        
    } catch {
        Write-Warning "JMeter test failed. Make sure JMeter is installed and in PATH."
        Write-Info "Test with: jmeter --version"
    }
    
    Read-Host "Press Enter to continue"
    Show-Menu
}

function Run-CombinedTest {
    Write-Info "Running combined test (fresh simulation + JMeter)..."
    & uv run python run_combined_test.py load
    Read-Host "Press Enter to continue"
    Show-Menu
}

function Create-BasicJMeterPlan {
    # Create jmeter directory if it doesn't exist
    if (!(Test-Path "jmeter")) {
        New-Item -ItemType Directory -Path "jmeter"
    }
    
    # Create a basic JMeter test plan
    $jmeterPlan = @"
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.5">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="DeviceBridge API Test">
      <stringProp name="TestPlan.comments">Basic API load test for DeviceBridge</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.arguments" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
        <collectionProp name="Arguments.arguments">
          <elementProp name="users" elementType="Argument">
            <stringProp name="Argument.name">users</stringProp>
            <stringProp name="Argument.value">`${__P(users,20)}</stringProp>
          </elementProp>
          <elementProp name="duration" elementType="Argument">
            <stringProp name="Argument.name">duration</stringProp>
            <stringProp name="Argument.value">`${__P(duration,300)}</stringProp>
          </elementProp>
          <elementProp name="ramp_up" elementType="Argument">
            <stringProp name="Argument.name">ramp_up</stringProp>
            <stringProp name="Argument.value">`${__P(ramp_up,60)}</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="API Users">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControllerGui" testclass="LoopController" testname="Loop Controller">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <intProp name="LoopController.loops">-1</intProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">`${users}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">`${ramp_up}</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">`${duration}</stringProp>
        <stringProp name="ThreadGroup.delay">0</stringProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Get Device List">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">localhost</stringProp>
          <stringProp name="HTTPSampler.port">8080</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">/api/devices</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
        <UniformRandomTimer guiclass="UniformRandomTimerGui" testclass="UniformRandomTimer" testname="Think Time">
          <stringProp name="ConstantTimer.delay">2000</stringProp>
          <stringProp name="RandomTimer.range">3000</stringProp>
        </UniformRandomTimer>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
"@
    
    $jmeterPlan | Out-File -FilePath "jmeter/devicebridge_test.jmx" -Encoding UTF8
    Write-Success "Created basic JMeter test plan"
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
        Write-Success "Database found:"
        try {
            & sqlite3 simulation.db "SELECT device_type, COUNT(*) as count FROM device_data GROUP BY device_type;"
        } catch {
            Write-Info "Database exists but sqlite3 not available"
        }
    } else {
        Write-Warning "No database found"
    }
    
    if (Test-Path "simulation_data") {
        Write-Success "Data files found:"
        Get-ChildItem "simulation_data"
    } else {
        Write-Warning "No data files found"
    }
    
    # Show JMeter results if any
    $jmeterResults = Get-ChildItem "jmeter_results_*.jtl" -ErrorAction SilentlyContinue
    if ($jmeterResults) {
        Write-Success "JMeter results found:"
        $jmeterResults | Format-Table Name, Length, LastWriteTime
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
        Get-ChildItem "simulation_stats_*.json" -ErrorAction SilentlyContinue | Remove-Item -Force
        Get-ChildItem "jmeter_results_*.jtl" -ErrorAction SilentlyContinue | Remove-Item -Force
        
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
    "jmeter-only" { Run-JMeterOnly }
    "combined" { Run-CombinedTest }
    "setup" { & uv run python setup.py }
    "view-data" { View-Data }
    "clean" { Clean-Data }
    "menu" { Show-Menu }
}