<#
    APOD Wallpaper - Installer
    ---------------------------
    Installs the script to %LOCALAPPDATA%\APODWallpaper and registers a
    Windows Task Scheduler job that runs it once a day (and once at logon,
    to catch laptops that were off at the scheduled time).

    Run this with:  powershell -ExecutionPolicy Bypass -File install_task.ps1

    No admin rights required (installs per-user, runs per-user).
#>

$ErrorActionPreference = "Stop"

$AppName   = "APODWallpaper"
$InstallDir = Join-Path $env:LOCALAPPDATA $AppName
$TaskName  = "APOD Daily Wallpaper"
$ScriptSrc = Join-Path $PSScriptRoot "apod_wallpaper.py"

Write-Host "Installing $AppName to $InstallDir ..."

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path $ScriptSrc -Destination $InstallDir -Force
Copy-Item -Path (Join-Path $PSScriptRoot "apod_info.py") -Destination $InstallDir -Force

# ---------------------------------------------------------------------
# Find a Python interpreter (prefer pythonw.exe so no console flashes up)
# ---------------------------------------------------------------------
function Find-Python {
    $candidates = @("pythonw.exe", "python.exe")
    foreach ($c in $candidates) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

$PythonExe = Find-Python
if (-not $PythonExe) {
    Write-Host ""
    Write-Host "ERROR: Python was not found on this machine." -ForegroundColor Red
    Write-Host "Install Python 3 from https://www.python.org/downloads/ (check 'Add to PATH')"
    Write-Host "then re-run this installer."
    exit 1
}
Write-Host "Using Python at: $PythonExe"

$ScriptDest = Join-Path $InstallDir "apod_wallpaper.py"

# ---------------------------------------------------------------------
# Register the scheduled task
# ---------------------------------------------------------------------
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptDest`""

$TriggerDaily  = New-ScheduledTaskTrigger -Daily -At 1:00PM
$TriggerLogon  = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Existing task found, removing before re-registering..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger @($TriggerDaily, $TriggerLogon) `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Downloads NASA's Astronomy Picture of the Day and sets it as desktop wallpaper." | Out-Null

Write-Host ""
Write-Host "Scheduled task '$TaskName' registered (runs daily at 8:00 AM and at each logon)." -ForegroundColor Green

# ---------------------------------------------------------------------
# Create a Desktop shortcut for "Today's Astronomy Picture" info viewer
# ---------------------------------------------------------------------
$InfoScript = Join-Path $InstallDir "apod_info.py"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Today's Astronomy Picture.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonExe
$Shortcut.Arguments = "`"$InfoScript`""
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "Shows today's NASA Astronomy Picture title and description, with a link to the NASA page."
$Shortcut.Save()

Write-Host "Desktop shortcut created: $ShortcutPath" -ForegroundColor Green


# ---------------------------------------------------------------------
# Run it once right now so the user sees results immediately
# ---------------------------------------------------------------------
Write-Host "Running it once now to set today's wallpaper..."
& $PythonExe $ScriptDest
Write-Host ""
Write-Host "Done. Logs are at: $InstallDir\apod_wallpaper.log"
Write-Host "To uninstall later, run uninstall_task.ps1"
