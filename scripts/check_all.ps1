param()

if (-not $env:DATABASE_URL) {
    Write-Error "DATABASE_URL is not set. See backend/docs/postgres-migration.md for setup." -ErrorAction Stop
}

Push-Location "$PSScriptRoot/../backend"

function Invoke-Poetry {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$PoetryArgs
    )

    $poetryCmd = Get-Command poetry -ErrorAction SilentlyContinue
    if ($poetryCmd) {
        & $poetryCmd.Path @PoetryArgs
    }
    else {
        & py -m poetry @PoetryArgs
    }
}

try {
    Invoke-Poetry install --no-interaction --no-root
    Invoke-Poetry run ruff check .
    Invoke-Poetry run mypy .
    Invoke-Poetry run bandit -q -r app
    Invoke-Poetry run pip-audit --strict
    Invoke-Poetry run pytest --cov=app --cov-report=term --cov-report=xml --cov-fail-under=80
    $alembicPath = Join-Path $env:TEMP "alembic.sql"
    Invoke-Poetry run alembic upgrade head --sql | Out-File -FilePath $alembicPath -Encoding ascii
    Write-Host "All checks completed. Alembic SQL written to $alembicPath"
}
finally {
    Pop-Location
}
