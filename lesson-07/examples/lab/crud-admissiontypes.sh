#!/usr/bin/env sh
set -eu

API="http://oh-proxy"
USER="${OH_ADMIN_USER:-admin}"
PASS="${OH_ADMIN_PASSWORD:-admin}"
CODE="${OH_CRUD_CODE:-ZZ}"

login_payload=$(printf '{"username":"%s","password":"%s"}' "$USER" "$PASS")

printf "Logging in as %s from the clinical subnet...\n" "$USER"
login_response="$(
    docker compose exec -T clinical-client curl -s \
        -H "Content-Type: application/json" \
        -d "$login_payload" \
        "$API/auth/login"
)"

token="$(printf "%s" "$login_response" | sed -n 's/.*"token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"

if [ -z "$token" ]; then
    printf "Login did not return a token. Response was:\n%s\n" "$login_response"
    exit 1
fi

auth_header="Authorization: Bearer $token"

request() {
    method="$1"
    path="$2"
    data="${3:-}"

    if [ -n "$data" ]; then
        docker compose exec -T clinical-client curl -s -i \
            -X "$method" \
            -H "$auth_header" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API$path"
    else
        docker compose exec -T clinical-client curl -s -i \
            -X "$method" \
            -H "$auth_header" \
            "$API$path"
    fi
}

printf "\n1. READ existing admission types\n"
request GET /admissiontypes

printf "\n\n2. CREATE a toy admission type %s\n" "$CODE"
request POST /admissiontypes \
    "$(printf '{"code":"%s","description":"SECURITY LAB TRIAGE"}' "$CODE")"

printf "\n\n3. READ again and look for %s\n" "$CODE"
request GET /admissiontypes

printf "\n\n4. UPDATE %s\n" "$CODE"
request PUT /admissiontypes \
    "$(printf '{"code":"%s","description":"SECURITY LAB TRIAGE UPDATED"}' "$CODE")"

printf "\n\n5. READ again and confirm the updated description\n"
request GET /admissiontypes

printf "\n\n6. DELETE %s\n" "$CODE"
request DELETE "/admissiontypes/$CODE"

printf "\n\n7. READ one last time and confirm %s is gone\n" "$CODE"
request GET /admissiontypes
printf "\n"
