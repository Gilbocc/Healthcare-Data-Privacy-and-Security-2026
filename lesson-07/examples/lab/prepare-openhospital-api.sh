#!/usr/bin/env sh
set -eu

API_DIR="vendor/openhospital-api"
API_REPO="https://github.com/informatici/openhospital-api.git"

if [ ! -d "$API_DIR/.git" ]; then
    mkdir -p vendor
    git clone --depth 1 "$API_REPO" "$API_DIR"
fi

cp .env "$API_DIR/.env"

(
    cd "$API_DIR"
    make
)

printf "\nOpenHospital API source prepared in %s\n" "$API_DIR"
printf "Next: docker compose build database backend\n"
