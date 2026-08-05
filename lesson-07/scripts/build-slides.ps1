param(
    [switch]$Clean
)

$lessonRoot = Split-Path $PSScriptRoot -Parent

Push-Location $lessonRoot
try {
    if ($Clean) {
        docker compose run --rm texlive -C
        return
    }

    docker compose run --rm texlive -pdf -interaction=nonstopmode -halt-on-error main.tex
}
finally {
    Pop-Location
}
