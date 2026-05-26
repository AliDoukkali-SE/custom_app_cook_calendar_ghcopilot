param(
  [string]$GitHubOrg = "AliDoukkali-SE",
  [string]$GitHubRepo = "custom_app_cook_calendar_ghcopilot",
  [string]$AppName = "gh-actions-meal-calendar",
  [string]$RgName = "rg-meal-calendar-dev"
)

$ErrorActionPreference = "Stop"

$SubId = az account show --query id -o tsv
$TenantId = az account show --query tenantId -o tsv

# 1. App Registration + SP (idempotent)
$AppId = az ad app list --display-name $AppName --query "[0].appId" -o tsv
if (-not $AppId) {
  $AppId = az ad app create --display-name $AppName --query appId -o tsv
}
$spExists = az ad sp list --filter "appId eq '$AppId'" --query "[0].id" -o tsv
if (-not $spExists) { az ad sp create --id $AppId | Out-Null }

Write-Host "AppId = $AppId"

# 2. Federated credentials
$subjMain = "repo:{0}/{1}:ref:refs/heads/main" -f $GitHubOrg, $GitHubRepo
$subjPr   = "repo:{0}/{1}:pull_request"        -f $GitHubOrg, $GitHubRepo

$fcMain = @{
  name        = "github-main"
  issuer      = "https://token.actions.githubusercontent.com"
  subject     = $subjMain
  description = "GitHub Actions - main branch"
  audiences   = @("api://AzureADTokenExchange")
} | ConvertTo-Json -Compress

$fcPr = @{
  name        = "github-pr"
  issuer      = "https://token.actions.githubusercontent.com"
  subject     = $subjPr
  description = "GitHub Actions - pull requests"
  audiences   = @("api://AzureADTokenExchange")
} | ConvertTo-Json -Compress

# Write to temp files to avoid quoting issues with az CLI
$tmpMain = New-TemporaryFile
$tmpPr   = New-TemporaryFile
$fcMain | Out-File -FilePath $tmpMain -Encoding utf8
$fcPr   | Out-File -FilePath $tmpPr   -Encoding utf8

try {
  az ad app federated-credential create --id $AppId --parameters "@$tmpMain"
} catch { Write-Warning "main FC: $_" }
try {
  az ad app federated-credential create --id $AppId --parameters "@$tmpPr"
} catch { Write-Warning "pr FC: $_" }

Remove-Item $tmpMain, $tmpPr -Force

# 3. Role assignment
try {
  az role assignment create --assignee $AppId --role Contributor --scope "/subscriptions/$SubId/resourceGroups/$RgName"
} catch { Write-Warning "role: $_" }

Write-Host ""
Write-Host "=== GitHub secrets ===" -ForegroundColor Cyan
Write-Host "AZURE_CLIENT_ID       = $AppId"
Write-Host "AZURE_TENANT_ID       = $TenantId"
Write-Host "AZURE_SUBSCRIPTION_ID = $SubId"
