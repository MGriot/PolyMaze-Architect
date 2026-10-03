<#
.SYNOPSIS
    Creates the Android release signing key and uploads it to GitHub Actions secrets.
.DESCRIPTION
    Run once, from the repo root, before tagging a release:
        powershell -ExecutionPolicy Bypass -File tools\setup_android_signing.ps1

    - Creates ~\.polymaze-signing\polymaze-release.keystore (PKCS12, RSA 4096, alias "polymaze") with a
      random password, and writes the alias and password to polymaze-release.txt next to it.
      Nothing is written inside the repo.
    - Uploads ANDROID_KEYSTORE_BASE64, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS and
      ANDROID_KEY_PASSWORD to the repo's Actions secrets with the GitHub CLI.

    If the keystore already exists it is reused and only the secrets are uploaded again.
    BACK UP the folder: every future update must be signed with this same key, or phones
    will refuse to install it over the previous version.
.PARAMETER Repo
    owner/name of the GitHub repository. Defaults to the repo of the current checkout.
#>
param([string]$Repo)

$ErrorActionPreference = 'Stop'
$Dir = Join-Path $HOME '.polymaze-signing'
$Keystore = Join-Path $Dir 'polymaze-release.keystore'
$Info = Join-Path $Dir 'polymaze-release.txt'
$Alias = 'polymaze'

# Windows PowerShell 5.1 turns a native tool's redirected stderr into terminating errors under 'Stop';
# rely on the exit code instead.
function Invoke-Native {
    $exe, $rest = $args  # plain $args so flags reach the tool untouched
    $ErrorActionPreference = 'Continue'
    & $exe @rest
    if ($LASTEXITCODE) { throw "$(Split-Path -Leaf $exe) $($rest[0]) failed ($LASTEXITCODE)" }
}

function Find-Keytool {
    $cmd = Get-Command keytool -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    if ($env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\keytool.exe")) { return "$env:JAVA_HOME\bin\keytool.exe" }
    throw 'keytool not found. Install a JDK (winget install Microsoft.OpenJDK.21) or set JAVA_HOME.'
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI (gh) not found: winget install GitHub.cli' }
try { Invoke-Native gh auth status *> $null } catch { throw 'Run "gh auth login" first.' }
if (-not $Repo) { $Repo = Invoke-Native gh repo view --json nameWithOwner --jq .nameWithOwner }
if (-not $Repo) { throw 'Could not detect the repository; pass -Repo owner/name.' }

if (Test-Path $Keystore) {
    Write-Host "Reusing existing keystore $Keystore" -ForegroundColor Yellow
    $line = Select-String -Path $Info -Pattern '^password=(.+)$' | Select-Object -First 1
    if (-not $line) { throw "Password not found in $Info" }
    $Password = $line.Matches[0].Groups[1].Value
} else {
    New-Item -ItemType Directory -Force $Dir | Out-Null
    $chars = [char[]]'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)  # works on Windows PowerShell 5.1 too
    $Password = -join ($bytes | ForEach-Object { $chars[$_ % $chars.Length] })

    $env:POLYMAZE_KS_PASS = $Password  # keeps the password off the command line
    try {
        Invoke-Native (Find-Keytool) -genkeypair -v -storetype PKCS12 -keystore $Keystore -alias $Alias `
            -keyalg RSA -keysize 4096 -validity 10000 -dname 'CN=MGriot, O=PolyMaze Architect' `
            '-storepass:env' POLYMAZE_KS_PASS '-keypass:env' POLYMAZE_KS_PASS  # quoted: PowerShell splits -flag:value
    } finally { Remove-Item Env:POLYMAZE_KS_PASS }

    @(
        '# PolyMaze Architect Android release key. Back up this folder somewhere safe (password manager, encrypted drive).'
        "created=$(Get-Date -Format 'yyyy-MM-dd')"
        "keystore=$Keystore"
        "alias=$Alias"
        "password=$Password"
        '# PKCS12 keystores use the same password for the store and the key.'
    ) | Set-Content -Path $Info -Encoding utf8
    Write-Host "Created $Keystore" -ForegroundColor Green
}

$secrets = [ordered]@{
    ANDROID_KEYSTORE_BASE64   = [Convert]::ToBase64String([IO.File]::ReadAllBytes($Keystore))
    ANDROID_KEYSTORE_PASSWORD = $Password
    ANDROID_KEY_ALIAS         = $Alias
    ANDROID_KEY_PASSWORD      = $Password
}
# A dotenv file keeps the values off the command line. Piping to stdin is avoided because
# Windows PowerShell 5.1 prepends a BOM to piped text.
$envFile = Join-Path $Dir 'secrets.env.tmp'
try {
    $lines = foreach ($name in $secrets.Keys) { "$name=`"$($secrets[$name])`"" }
    [IO.File]::WriteAllText($envFile, ($lines -join "`n") + "`n", (New-Object Text.UTF8Encoding $false))
    Invoke-Native gh secret set --env-file $envFile --repo $Repo
} finally { Remove-Item $envFile -ErrorAction SilentlyContinue }

Write-Host ''
Write-Host "Uploaded 4 Android signing secrets to $Repo." -ForegroundColor Green
Write-Host "BACK UP $Dir now. Losing it means future versions can't update existing installs." -ForegroundColor Yellow
