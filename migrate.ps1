# PowerShell script to run migration
Write-Host "Starting database migration..." -ForegroundColor Yellow
Write-Host ""

# Try to find Python executable
$pythonExe = $null

# Check common Python locations
$pythonPaths = @(
    "python.exe",
    "python3.exe",
    "py.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe", 
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python38\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe",
    "C:\Python39\python.exe",
    "C:\Python38\python.exe",
    "C:\Python\python.exe"
)

foreach ($path in $pythonPaths) {
    try {
        $testPath = Get-Command $path -ErrorAction SilentlyContinue
        if ($testPath) {
            $pythonExe = $path
            Write-Host "Found Python at: $pythonExe" -ForegroundColor Green
            break
        }
    } catch {
        # Continue searching
    }
}

if (-not $pythonExe) {
    Write-Host "ERROR: Python not found in PATH or common locations!" -ForegroundColor Red
    Write-Host "Please install Python or add it to PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the migration script
Write-Host "Running migration with: $pythonExe" -ForegroundColor Cyan
Write-Host ""

& $pythonExe execute_migration.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Migration completed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Migration failed!" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to close"
