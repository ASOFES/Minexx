$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Start Django Server.lnk")
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = """$PSScriptRoot\run_server_hidden.vbs"""
$Shortcut.WorkingDirectory = "$PSScriptRoot"
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Save()
Write-Host "Raccourci créé dans le dossier de démarrage Windows. Le serveur démarrera et redémarrera automatiquement." 