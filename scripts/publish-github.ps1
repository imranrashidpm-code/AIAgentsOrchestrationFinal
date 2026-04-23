#Requires -Version 5.1
<#
.SYNOPSIS
  Creates the GitHub repo if it does not exist, then pushes main using a PAT.

.DESCRIPTION
  1. Set GITHUB_TOKEN to a classic personal access token with "repo" scope:
     https://github.com/settings/tokens
  2. Run from repo root:
       .\scripts\publish-github.ps1

  The script restores a token-free origin URL after a successful push.
#>
param(
    [string]$Owner = "developer-digitalsofts",
    [string]$Repo = "AIAgentsOrchestrator"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not $env:GITHUB_TOKEN) {
    Write-Error @"
GITHUB_TOKEN is not set.

1. Create a classic PAT with "repo" scope: https://github.com/settings/tokens
2. In PowerShell:
     `$env:GITHUB_TOKEN = "ghp_your_token_here"
   Then:
     .\scripts\publish-github.ps1

Or create an empty repo named $Repo under $Owner on GitHub, then run:
     git push -u origin main
"@
}

$headers = @{
    Authorization = "Bearer $($env:GITHUB_TOKEN)"
    Accept        = "application/vnd.github+json"
    User-Agent    = "AIAgentsOrchestrator-publish-script"
}

$repoUri = "https://api.github.com/repos/$Owner/$Repo"
$exists = $false
try {
    Invoke-RestMethod -Uri $repoUri -Headers $headers -Method Get | Out-Null
    $exists = $true
    Write-Host "Repository $Owner/$Repo already exists on GitHub."
}
catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code -eq 404) {
        Write-Host "Creating repository $Owner/$Repo ..."
        $body = @{ name = $Repo; private = $false; auto_init = $false } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Headers $headers `
            -Method Post -Body $body -ContentType "application/json" | Out-Null
        Write-Host "Repository created."
    }
    else {
        throw
    }
}

$secureRemote = "https://x-access-token:$($env:GITHUB_TOKEN)@github.com/$Owner/$Repo.git"
$cleanRemote = "https://github.com/$Owner/$Repo.git"

git remote set-url origin $secureRemote
try {
    git push -u origin main
    Write-Host "Push completed."
}
finally {
    git remote set-url origin $cleanRemote
    Write-Host "Origin reset to token-free URL: $cleanRemote"
}
