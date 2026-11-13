$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$python=Get-Command py -ErrorAction SilentlyContinue
if($python){
  & py -3 -c 'import PIL' 2>$null
  if($LASTEXITCODE -eq 0){& py -3 (Join-Path $PSScriptRoot 'generate_app_icon.py')}
  else{& python (Join-Path $PSScriptRoot 'generate_app_icon.py')}
}
else{& python (Join-Path $PSScriptRoot 'generate_app_icon.py')}
if($LASTEXITCODE -ne 0){throw 'Net uygulama simgesi olusturulamadi.'}
