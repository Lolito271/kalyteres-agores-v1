import subprocess
import os
import sys

def run_command(command, description):
    print(f"\n[RUNNING] {description}...")
    try:
        # We use shell=True for simple command strings, specially in windows
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAILED] {description}")
        print(e.output)
        print(e.stderr)
        return False

def automate():
    # 1. Generate Article
    if not run_command("python scripts/generate_article.py", "Generating new article with verified links"):
        return

    # 2. Build Site
    if not run_command("python scripts/build_site.py", "Building static site and categories"):
        return

    # 3. Deploy (using the local deploy logic if git is configured)
    print("\n[INFO] Starting Deployment to GitHub Pages...")
    deploy_commands = [
        'if (Test-Path "C:\\tmp_deploy") { Remove-Item -Recurse -Force "C:\\tmp_deploy" }',
        'New-Item -ItemType Directory -Path "C:\\tmp_deploy"',
        'robocopy "public" "C:\\tmp_deploy" /E /NJH /NJS',
        'cd "C:\\tmp_deploy"',
        '& "C:\\Program Files\\Git\\bin\\git.exe" init',
        '& "C:\\Program Files\\Git\\bin\\git.exe" config user.email "bot@antigravity.ai"',
        '& "C:\\Program Files\\Git\\bin\\git.exe" config user.name "Antigravity Bot"',
        '& "C:\\Program Files\\Git\\bin\\git.exe" remote add origin https://github.com/Lolito271/kalyteres-agores-v1.git',
        '& "C:\\Program Files\\Git\\bin\\git.exe" checkout -b gh-pages',
        '& "C:\\Program Files\\Git\\bin\\git.exe" add .',
        '& "C:\\Program Files\\Git\\bin\\git.exe" commit -m "Automated Update: New Article & Verified Links"',
        '& "C:\\Program Files\\Git\\bin\\git.exe" push origin gh-pages --force'
    ]
    
    # Run deploy via powershell
    full_deploy_cmd = "powershell -Command \"" + "; ".join(deploy_commands) + "\""
    if run_command(full_deploy_cmd, "Deploying to GitHub Pages"):
        print("\n[DONE] Everything synchronized successfully!")
    else:
        print("\n[ERROR] Deployment failed.")

if __name__ == "__main__":
    automate()
