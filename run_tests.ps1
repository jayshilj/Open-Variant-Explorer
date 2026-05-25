# Automated PowerShell runner for Open-Variant Explorer test suite
Write-Host "Activating virtual environment..." -ForegroundColor Green
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Warning: Virtual environment activation script not found. Running with global python." -ForegroundColor Yellow
}

Write-Host "Running parser and directly-follows graph test suite..." -ForegroundColor Green
python -m unittest discover -s tests -p "test_*.py" -v

Write-Host "Completed validation check." -ForegroundColor Green
