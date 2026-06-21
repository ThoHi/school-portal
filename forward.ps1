# forward.ps1 — Expose local app service ports via Microsoft Dev Tunnels.
#
# Uses a STABLE NAMED tunnel so the public URLs stay the same across restarts.
# Ports are split into:
#   $Ports        - every service port to forward
#   $PublicPorts  - the subset open to anyone with the URL (no login)
# Any port NOT in $PublicPorts requires a Dev Tunnels login to access.
#
# Usage:
#   .\forward.ps1                 # forward the ports below (stable URLs)
#   .\forward.ps1 9090 9091       # override the list with ad-hoc ports
#   .\forward.ps1 -TunnelId test  # use a different named tunnel
#
# To add/remove a service port permanently, edit the arrays below and re-run —
# the script syncs the tunnel's ports AND public/private access to match.

param(
    [int[]]$Ports = @(8080, 8081, 8082, 8083, 8084),

    # Publicly open (anonymous) services. Must be a subset of $Ports.
    #   8081 = parent report
    #   8082 = e-library launcher
    #   8083 = calibre-web (the actual book server the launcher links to)
    [int[]]$PublicPorts = @(8081, 8082, 8083),

    [string]$TunnelId = "school-portal"
)

# Ensure the devtunnel CLI is installed.
if (-not (Get-Command devtunnel -ErrorAction SilentlyContinue)) {
    Write-Host "devtunnel CLI not found." -ForegroundColor Red
    Write-Host "Install it with:  winget install Microsoft.devtunnel" -ForegroundColor Yellow
    exit 1
}

# Make sure we're signed in (login is a no-op if already authenticated).
$loginStatus = devtunnel user show 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($loginStatus)) {
    Write-Host "Signing in to Dev Tunnels..." -ForegroundColor Cyan
    devtunnel user login
}

# Create the named tunnel once (private by default); ignore if it exists.
$existing = devtunnel show $TunnelId 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating stable tunnel '$TunnelId'..." -ForegroundColor Cyan
    devtunnel create $TunnelId
}

# Sync the tunnel's ports to match $Ports.
$existingPorts = (devtunnel port list $TunnelId 2>$null | Select-String -Pattern '\b(\d{2,5})\b' -AllMatches |
    ForEach-Object { $_.Matches.Value }) -as [int[]]

foreach ($p in $Ports) {
    if ($existingPorts -notcontains $p) {
        Write-Host "Adding port $p to tunnel..." -ForegroundColor DarkCyan
        devtunnel port create $TunnelId -p $p | Out-Null
    }
}

# Remove any ports on the tunnel that are no longer in $Ports (mirror the list).
foreach ($p in $existingPorts) {
    if ($Ports -notcontains $p) {
        Write-Host "Removing stale port $p from tunnel..." -ForegroundColor DarkYellow
        devtunnel port delete $TunnelId -p $p | Out-Null
    }
}

# Reset all access rules, then re-grant anonymous access only to $PublicPorts.
# This keeps public/private exactly mirroring the config on every run.
devtunnel access reset $TunnelId | Out-Null
foreach ($p in $PublicPorts) {
    if ($Ports -notcontains $p) {
        Write-Host "WARNING: public port $p is not in `$Ports — skipping." -ForegroundColor Red
        continue
    }
    Write-Host "Opening port $p to the public (anonymous)..." -ForegroundColor Green
    devtunnel access create $TunnelId -p $p --anonymous | Out-Null
}

$privatePorts = $Ports | Where-Object { $PublicPorts -notcontains $_ }
Write-Host ""
Write-Host ("Tunnel '{0}'" -f $TunnelId) -ForegroundColor Green
Write-Host ("  Public (no login) : {0}" -f ($PublicPorts -join ', ')) -ForegroundColor Green
Write-Host ("  Private (login)   : {0}" -f ($privatePorts -join ', ')) -ForegroundColor Yellow
Write-Host "URLs stay the same every run. Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

devtunnel host $TunnelId
