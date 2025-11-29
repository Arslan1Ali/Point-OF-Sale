param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ComposeArgs
)

Push-Location (Join-Path $PSScriptRoot "..")
try {
    if ($ComposeArgs -and $ComposeArgs.Length -gt 0) {
        docker compose -f docker-compose.dev.yml up --build @ComposeArgs
    }
    else {
        docker compose -f docker-compose.dev.yml up --build
    }
}
finally {
    Pop-Location
}
