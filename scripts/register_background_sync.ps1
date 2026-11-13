param([Parameter(Mandatory=$true)][string]$ExePath)
$ErrorActionPreference = 'Stop'
if (!(Test-Path -LiteralPath $ExePath -PathType Leaf)) { throw 'YLSY Atlas EXE bulunamadı.' }
$taskName = 'YLSY Atlas Cloud Sync'
$action = New-ScheduledTaskAction -Execute $ExePath -Argument '--sync-pending'
$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 3) -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Host 'YLSY Atlas arka plan eşitleme görevi kuruldu.'
