# Trade Agent — Start Script
# Run this to start both backend and frontend together

Write-Output "========================================="
Write-Output "  Trade Agent — Starting Services"
Write-Output "========================================="

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Kill anything on port 8000 or 3000
$p1 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1
if ($p1) { Stop-Process -Id $p1 -Force; Write-Output "Cleaned port 8000" }
$p2 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1
if ($p2) { Stop-Process -Id $p2 -Force; Write-Output "Cleaned port 3000" }

# Start backend
Write-Output "Starting backend on http://localhost:8000 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\Administrator\trade-agent\backend; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

# Start frontend
Write-Output "Starting frontend on http://localhost:3000 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\Administrator\trade-agent\frontend; npm run dev"

Start-Sleep -Seconds 5
Start-Process "http://localhost:3000"
Write-Output "========================================="
Write-Output "  Backend:  http://localhost:8000/docs"
Write-Output "  Frontend: http://localhost:3000"
Write-Output "========================================="
