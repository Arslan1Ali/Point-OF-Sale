param()

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

Push-Location (Join-Path $PSScriptRoot "../backend")
try {
    Invoke-Poetry install --no-interaction --no-root
    Invoke-Poetry run alembic upgrade head
    Invoke-Poetry run python scripts/create_admin_user.py
}
finally {
    Pop-Location
}
