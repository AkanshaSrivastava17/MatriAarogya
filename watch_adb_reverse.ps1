$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"

while ($true) {
    try {
        $devices = & $adb devices 2>$null
        if ($devices -match "emulator-\d+\s+device") {
            & $adb reverse tcp:8000 tcp:8000 2>$null
        }
    } catch {
        # ignore transient errors
    }
    Start-Sleep -Seconds 3
}
