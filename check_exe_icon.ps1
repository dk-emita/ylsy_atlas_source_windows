# YLSY Atlas 2.3.5 icon diagnostic, run after build.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$exe = Join-Path $PSScriptRoot "dist\ylsy-atlas.exe"
if (!(Test-Path $exe)) { throw "Once build.ps1 calistirin." }
$reports = Join-Path $PSScriptRoot "build\reports"
New-Item -ItemType Directory -Path $reports -Force | Out-Null
Write-Host "Derlenmis EXE surumu: $((Get-Item $exe).VersionInfo.FileVersion)"
$diagPath = Join-Path $reports ("ylsy-atlas-icon-test-{0}.exe" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
Copy-Item $exe $diagPath -Force
Add-Type -AssemblyName System.Drawing
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon($diagPath)
if (-not $icon) { throw "EXE icerisindeki simge okunamadi." }
$bitmap = $icon.ToBitmap()
$out = Join-Path $reports "ylsy-atlas-icon-test.png"
$bitmap.Save($out,[System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
$icon.Dispose()
Write-Host "Yeni adli EXE: $diagPath"
Write-Host "EXE icerisinden okunan gercek simge: $out"
Write-Host "PNG dogru fakat Explorer eskiyse: Windows simge onbellegi."
Write-Host "PNG de eskiyse: EXE ikon kaynak/derleme problemi."
