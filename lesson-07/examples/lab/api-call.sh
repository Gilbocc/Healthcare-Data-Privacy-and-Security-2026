#!/usr/bin/env sh
set -eu

usage() {
    cat <<'USAGE'
Usage:
  ./api-call.sh <subnet> <method> <path> [json-body]

Subnets:
  clinical | lab | guest | vpn | dmz

Examples:
  ./api-call.sh clinical GET /patients
  ./api-call.sh lab GET /examtypes
  OH_NO_AUTH=1 ./api-call.sh dmz GET /swagger-ui/index.html
  ./api-call.sh clinical POST /admissiontypes '{"code":"ZZ","description":"SECURITY LAB"}'

Environment:
  OH_ADMIN_USER      default: admin
  OH_ADMIN_PASSWORD  default: admin
  OH_NO_AUTH=1       skip login/token and send the request anonymously
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ "$#" -lt 3 ]; then
    usage
    exit 0
fi

subnet="$1"
method="$2"
path="$3"
body="${4:-}"

case "$subnet" in
    clinical) service="clinical-client" ;;
    lab) service="lab-client" ;;
    guest) service="guest-client" ;;
    vpn) service="vpn-client" ;;
    dmz) service="dmz-client" ;;
    *) printf "Unknown subnet: %s\n\n" "$subnet"; usage; exit 1 ;;
esac

api="http://oh-proxy"
token=""

if [ "${OH_NO_AUTH:-0}" != "1" ]; then
    user="${OH_ADMIN_USER:-admin}"
    pass="${OH_ADMIN_PASSWORD:-admin}"
    login_payload=$(printf '{"username":"%s","password":"%s"}' "$user" "$pass")
    login_response="$(
        docker compose exec -T "$service" curl -s \
            -H "Content-Type: application/json" \
            -d "$login_payload" \
            "$api/auth/login" || true
    )"
    token="$(printf "%s" "$login_response" | sed -n 's/.*"token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
    if [ -n "$token" ]; then
        :
    else
        printf "No token obtained from %s. Continuing anonymously so the response shows the layer that blocks it.\n\n" "$subnet"
    fi
fi

printf "=== %s %s %s via %s ===\n" "$method" "$path" "$subnet" "$service"

if [ -n "$body" ]; then
    if [ -n "$token" ]; then
        docker compose exec -T "$service" curl -s -i \
            -X "$method" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$body" \
            "$api$path"
    else
        docker compose exec -T "$service" curl -s -i \
            -X "$method" \
            -H "Content-Type: application/json" \
            -d "$body" \
            "$api$path"
    fi
else
    if [ -n "$token" ]; then
        docker compose exec -T "$service" curl -s -i \
            -X "$method" \
            -H "Authorization: Bearer $token" \
            "$api$path"
    else
        docker compose exec -T "$service" curl -s -i \
            -X "$method" \
            "$api$path"
    fi
fi
printf "\n"
