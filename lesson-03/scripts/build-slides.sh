#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LESSON_ROOT="$(dirname "$SCRIPT_DIR")"

CLEAN=false
for arg in "$@"; do
    case "$arg" in
        -Clean|--clean)
            CLEAN=true
            ;;
    esac
done

cd "$LESSON_ROOT"

if [ "$CLEAN" = true ]; then
    docker compose run --rm texlive -C
else
    docker compose run --rm texlive -pdf -interaction=nonstopmode -halt-on-error main.tex
fi
