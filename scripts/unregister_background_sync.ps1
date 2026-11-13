$ErrorActionPreference = 'Stop'
$taskName = 'YLSY Atlas Cloud Sync'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}
