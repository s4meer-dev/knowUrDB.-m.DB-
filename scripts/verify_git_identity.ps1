$ErrorActionPreference = "Stop"

# Verify repository root
$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Not a git repository." -ForegroundColor Red
    exit 1
}

# Verify branch
$branch = git branch --show-current
if ($branch -ne "main") {
    Write-Host "Error: Not on main branch. Current branch: $branch" -ForegroundColor Red
    exit 1
}

# Verify remote
$remote = git remote get-url origin
if ($remote -notmatch "github.com.*s4meer-dev/knowUrDB\.git") {
    Write-Host "Error: Remote origin does not match expected URL." -ForegroundColor Red
    Write-Host "Current: $remote" -ForegroundColor Red
    Write-Host "Expected: https://github.com/s4meer-dev/knowUrDB.git" -ForegroundColor Red
    exit 1
}

# Verify local Git identity exists
$localName = git config --local --get user.name
$localEmail = git config --local --get user.email

if (-not $localName) {
    Write-Host "Error: Local git user.name is not set." -ForegroundColor Red
    exit 1
}
if (-not $localEmail) {
    Write-Host "Error: Local git user.email is not set." -ForegroundColor Red
    exit 1
}

# Verify Author identity
$authorIdent = git var GIT_AUTHOR_IDENT
if (-not $authorIdent) {
    Write-Host "Error: Failed to get GIT_AUTHOR_IDENT." -ForegroundColor Red
    exit 1
}

Write-Host "Git Identity Verification Passed!" -ForegroundColor Green
Write-Host "- Repository Root: $repoRoot" -ForegroundColor Cyan
Write-Host "- Branch: $branch" -ForegroundColor Cyan
Write-Host "- Remote: $remote" -ForegroundColor Cyan
Write-Host "- Author Identity: $authorIdent" -ForegroundColor Cyan
Write-Host "- Configured Local Identity: $localName <$localEmail>" -ForegroundColor Cyan
