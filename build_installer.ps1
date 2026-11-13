# YLSY Atlas — Windows EXE ve isteğe bağlı Inno Setup yükleyicisi.
# Derleme yalnızca Windows üzerinde yapılır.
param([switch]$ExeOnly, [switch]$SkipBuild, [switch]$UseStaged)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if ($UseStaged -and -not $SkipBuild) { throw '-UseStaged için -SkipBuild de gereklidir.' }
$running = Get-Process -Name 'ylsy-atlas','YLSY Atlas' -ErrorAction SilentlyContinue
if (-not $SkipBuild) {
  & (Join-Path $PSScriptRoot 'build.ps1') -Stage:($null -ne $running)
  if ($LASTEXITCODE -ne 0) { throw 'EXE derlemesi başarısız.' }
}
$sourceExe = if ($UseStaged -or ($running -and -not $SkipBuild)) { 'build\staged\ylsy-atlas.exe' } else { 'build\payload\ylsy-atlas.exe' }
$appExe = Join-Path $PSScriptRoot $sourceExe
if (!(Test-Path -LiteralPath $appExe)) { throw 'Uygulama EXE dosyası bulunamadı; önce build.ps1 çalıştırın.' }
if ($ExeOnly) { Write-Host 'EXE hazır. Kurulum derlemesi atlandı.' -ForegroundColor Yellow; exit 0 }
$candidates = @()
if (${env:ProgramFiles(x86)}) { $candidates += Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe' }
if ($env:ProgramFiles) { $candidates += Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe' }
if ($env:LOCALAPPDATA) { $candidates += Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe' }
if ($env:ProgramFiles) { $candidates += Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe' }
$candidates = @($candidates | Where-Object { Test-Path $_ })
$iscc = if ($candidates.Count) { $candidates[0] } else { (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1) }
if (-not $iscc) {
  Write-Host 'EXE oluşturuldu ancak kurulum için Inno Setup 6 kurulu değil.' -ForegroundColor Yellow
  Write-Host 'Inno Setup 6 kurulunca tekrar .\build_installer.ps1 çalıştırın.'
  exit 0
}
& $iscc "/DSourceExe=$sourceExe" (Join-Path $PSScriptRoot 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw 'Kurulum dosyası oluşturulamadı.' }
$setup = Join-Path $PSScriptRoot 'dist\YLSY-Atlas-v4.0.0-Setup.exe'
if (!(Test-Path $setup)) { throw 'Inno Setup çıktı dosyası bulunamadı.' }
Write-Host "Kurulum dosyası: $setup" -ForegroundColor Green
$legacyRootExe = Join-Path $PSScriptRoot 'YLSY-Atlas-desktop-v4.0.0.exe'
$legacyDistExe = Join-Path $PSScriptRoot 'dist\ylsy-atlas.exe'
foreach ($extraExe in @($legacyRootExe, $legacyDistExe)) {
  if (Test-Path -LiteralPath $extraExe -PathType Leaf) { Remove-Item -LiteralPath $extraExe -Force }
}
$generatedBuild = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'build'))
$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
if ($generatedBuild.StartsWith($projectRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
    (Split-Path -Leaf $generatedBuild) -eq 'build' -and (Test-Path -LiteralPath $generatedBuild -PathType Container)) {
  Remove-Item -LiteralPath $generatedBuild -Recurse -Force
}
Write-Host 'Gereksiz kök EXE ve ara derleme dosyaları temizlendi; dist içinde yalnızca Setup EXE bırakıldı.' -ForegroundColor Cyan
