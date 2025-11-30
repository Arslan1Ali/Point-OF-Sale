Write-Host "Starting Retail POS..."
$root = $PSScriptRoot

# Start Backend
Write-Host "Launching Backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; py -m poetry run uvicorn app.api.main:app --reload"

# Wait for backend to init
Write-Host "Waiting for backend to initialize..."
Start-Sleep -Seconds 5

# Start Frontend
Write-Host "Launching Frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\modern_client'; py -m poetry run python main.py"

# Start SuperAdmin Portal
Write-Host "Launching SuperAdmin Portal (Port 8080)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\super_admin_client'; py -m poetry run python main.py"

Write-Host "Done! Check the new windows."
