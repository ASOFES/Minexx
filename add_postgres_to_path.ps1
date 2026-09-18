# Script pour ajouter PostgreSQL au PATH système
$postgresPath = "C:\Program Files\PostgreSQL\17\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if (-not $currentPath.Contains($postgresPath)) {
    $newPath = $currentPath + ";" + $postgresPath
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "PostgreSQL a été ajouté au PATH utilisateur."
} else {
    Write-Host "PostgreSQL est déjà dans le PATH utilisateur."
}

# Vérification
Write-Host "`nVérification de l'installation :"
Write-Host "--------------------------------"
Write-Host "Version de psql :"
& "$postgresPath\psql.exe" --version
Write-Host "`nTest de connexion à la base de données :"
Write-Host "----------------------------------------"
Write-Host "Pour tester la connexion, exécutez :"
Write-Host "psql -U postgres"
Write-Host "`nNote : Utilisez le mot de passe que vous avez défini pendant l'installation." 