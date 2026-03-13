param (
    [string]$GitPath = "C:\Program Files\Git\bin\git.exe"
)

$DeployDir = "C:\tmp_deploy"
$PublicDir = "public"

# Clean temp dir
if (Test-Path $DeployDir) {
    Remove-Item -Recurse -Force $DeployDir
}
New-Item -ItemType Directory -Path $DeployDir | Out-Null

# Copy public contents
robocopy $PublicDir $DeployDir /E /NJH /NJS | Out-Null

# Navigate to deploy dir and push
Set-Location -Path $DeployDir
& $GitPath init
& $GitPath config user.email "bot@antigravity.ai"
& $GitPath config user.name "Antigravity Bot"
& $GitPath remote add origin https://github.com/Lolito271/kalyteres-agores-v1.git
& $GitPath checkout -b gh-pages
& $GitPath add .
& $GitPath commit -m "Auto Deploy: Latest Articles & Category Updates"
& $GitPath push origin gh-pages --force

# Cleanup
Set-Location -Path "C:\Users\Lolito\OneDrive\Desktop\antigravity\kalyteres-agores-v1"
Remove-Item -Recurse -Force $DeployDir
Write-Host "Deploy Done."
