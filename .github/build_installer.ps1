Write-Host "Building installer..." -ForegroundColor Green

try {
    Write-Host "Checking Python version..."
    $pythonVersion = (python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if (-not $pythonVersion) {
        throw "Cannot get Python version. Please ensure Python is installed and in PATH."
    }
    Write-Host "Detected Python version: $pythonVersion" -ForegroundColor Cyan

    # Requires Python 3.x
    if ($pythonVersion.StartsWith("2.")) {
        throw "Detected Python 2.x, please use Python 3.x."
    }
    Write-Host "Python version check passed." -ForegroundColor Green

    Write-Host "Running PyInstaller..."
    python -m PyInstaller ui.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code: $LASTEXITCODE"
    }
    Write-Host "PyInstaller succeeded." -ForegroundColor Green

    Write-Host "Getting latest Git tag..."
    $latestTag = git describe --tags --abbrev=0
    if (-not $latestTag) {
        throw "Cannot get latest Git tag."
    }
    $bmsPathName = "bms-translator-" + $latestTag
    Write-Host "Latest tag: $latestTag" -ForegroundColor Cyan
    Write-Host "Build path name: $bmsPathName" -ForegroundColor Cyan

    Write-Host "Creating target directory: $bmsPathName"
    mkdir -p $bmsPathName
    if (-not (Test-Path $bmsPathName)) {
        throw "Failed to create directory: $bmsPathName"
    }
    Write-Host "Target directory created." -ForegroundColor Green

    Write-Host "Copying config/ directory..."
    cp -r config/ $bmsPathName/config/
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy config/ directory."
    }
    # Ensure config/ directory is writable
    Get-ChildItem -Path "$bmsPathName/config" -Recurse | ForEach-Object {
        if (($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq [System.IO.FileAttributes]::ReadOnly) {
            $_.IsReadOnly = $false
        }
    }
    Write-Host "config/ directory copied." -ForegroundColor Green

    Write-Host "Copying dist/ui.exe..."
    cp dist/ui.exe $bmsPathName/$bmsPathName.exe
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy dist/ui.exe."
    }
    # Ensure exe is writable
    $exePath = Join-Path $bmsPathName "$bmsPathName.exe"
    if ((Get-Item $exePath).Attributes -band [System.IO.FileAttributes]::ReadOnly) {
        (Get-Item $exePath).IsReadOnly = $false
    }
    Write-Host "dist/ui.exe copied." -ForegroundColor Green

    Write-Host "Directory structure:"
    tree $bmsPathName

    Write-Host "Compressing files to: $bmsPathName.zip"
    Compress-Archive -Path "$bmsPathName" -DestinationPath "$bmsPathName.zip" -Force
    if (-not (Test-Path "$bmsPathName.zip")) {
        throw "Failed to compress files."
    }
    Write-Host "Files compressed: $bmsPathName.zip" -ForegroundColor Green

    Write-Host "Installer build completed!" -ForegroundColor Green
    echo "installer_zip_path=$bmsPathName.zip" >> $env:GITHUB_OUTPUT
}
catch {
    Write-Error "Error building installer: $($_.Exception.Message)"
    exit 1
}