<#
    APOD Wallpaper - Uninstaller
    Run with: powershell -ExecutionPolicy Bypass -File uninstall_task.ps1
#>

$TaskName = "APOD Daily Wallpaper"
$AppName  = "APODWallpaper"
$InstallDir = Join-Path $env:LOCALAPPDATA $AppName

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task '$TaskName'."
} else {
    Write-Host "No scheduled task found named '$TaskName'."
}

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Today's Astronomy Picture.lnk"
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "Removed desktop shortcut."
}

$resp = Read-Host "Also delete downloaded images and logs at $InstallDir ? (y/N)"
if ($resp -eq "y" -or $resp -eq "Y") {
    Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
    Write-Host "Removed $InstallDir"
} else {
    Write-Host "Left $InstallDir in place."
}

Write-Host "Uninstall complete."
