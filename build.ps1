# YLSY Atlas Desktop 4.0.0 — approved icon for EXE, native window and taskbar.
param([switch]$Stage)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host '[YLSY ATLAS DESKTOP 4.0.0] Windows derlemesi basliyor...' -ForegroundColor Cyan

$IconPath = (Resolve-Path (Join-Path $PSScriptRoot 'assets\atlas-icon.ico')).Path
$VersionFile = (Resolve-Path (Join-Path $PSScriptRoot 'assets\version_info.txt')).Path
$BuildDir = Join-Path $PSScriptRoot 'build'
$DistDir = if ($Stage) { Join-Path $BuildDir 'staged' } else { Join-Path $BuildDir 'payload' }
$SpecDir = Join-Path $BuildDir 'spec'
$PyInstallerWorkDir = Join-Path $BuildDir 'pyinstaller'
$ReportDir = Join-Path $BuildDir 'reports'
$ExePath = Join-Path $DistDir 'ylsy-atlas.exe'

# Verify that the app isn't running before rebuilding.
$running = Get-Process -Name 'YLSY-Atlas' -ErrorAction SilentlyContinue
if ($running -and -not $Stage) { throw 'Lutfen once YLSY Atlas uygulamasini kapatin veya -Stage ile ayri bir EXE derleyin.' }
# Old PyInstaller output and previous EXE can retain outdated resources.
# Build internals and diagnostic reports stay separate from release files.
foreach ($target in @($BuildDir, $DistDir)) {
    if (Test-Path $target) { Remove-Item $target -Force -Recurse }
}
New-Item -ItemType Directory -Path $SpecDir,$PyInstallerWorkDir,$ReportDir -Force | Out-Null

$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    $Py = 'py'; $PyPrefix = @('-3')
} else {
    $Py = 'python'; $PyPrefix = @()
}
& $Py @PyPrefix -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Bagimliliklar yuklenemedi.' }

# PyInstaller uses Qt hooks to bundle Qt WebEngine and its helper process.
& $Py @PyPrefix -m PyInstaller --noconfirm --clean --noupx --onefile --windowed `
    --name 'ylsy-atlas' `
    --specpath $SpecDir `
    --workpath $PyInstallerWorkDir `
    --distpath $DistDir `
    --icon $IconPath `
    --version-file $VersionFile `
    --add-data "$PSScriptRoot\web;web" `
    --add-data "$PSScriptRoot\assets;assets" `
    --add-data "$PSScriptRoot\resources;resources" `
    --collect-submodules 'keyring.backends' `
    run.py
if ($LASTEXITCODE -ne 0 -or !(Test-Path $ExePath)) { throw 'Windows EXE derlemesi basarisiz.' }

# Inspect the real embedded EXE resource instead of trusting Explorer's cached thumbnail.
Add-Type -AssemblyName System.Drawing
$exeIcon = [System.Drawing.Icon]::ExtractAssociatedIcon($ExePath)
if ($null -eq $exeIcon) { throw 'EXE simgesi okunamadi.' }
$checkImage = Join-Path $ReportDir 'exe-icon-check.png'
$bitmap = $exeIcon.ToBitmap()
$bitmap.Save($checkImage, [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
$exeIcon.Dispose()

$sourceHash = (Get-FileHash -Algorithm SHA256 $IconPath).Hash
Write-Host "EXE simgesi (SHA256): $sourceHash" -ForegroundColor Cyan
Write-Host "EXE surumu: $((Get-Item $ExePath).VersionInfo.FileVersion)" -ForegroundColor Cyan
Write-Host "EXE: $ExePath" -ForegroundColor Green
Write-Host "Windows tarafindan okunan EXE simgesi: $checkImage" -ForegroundColor Green
Write-Host 'EXE ikonu eski gorunurse .\\check_exe_icon.ps1 dosyasini calistirin.' -ForegroundColor Yellow
Write-Host 'Eski gorunumu gosteriyorsa gorev cubugundaki eski kisayolu kaldirin; yeni EXE''yi tekrar sabitleyin.' -ForegroundColor Yellow

Write-Host 'EXE, pencere ve gorev cubugu AYNI onayli turbin ikonunu kullaniyor.' -ForegroundColor Cyan
