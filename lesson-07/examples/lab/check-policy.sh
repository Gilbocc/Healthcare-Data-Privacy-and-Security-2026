#!/usr/bin/env sh
set -eu

check_code() {
    name="$1"
    expected="$2"
    service="$3"
    url="$4"

    actual="$(docker compose exec "$service" curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$url" || true)"

    case ",$expected," in
        *,"$actual",*)
        printf "PASS %-34s expected=%s actual=%s\n" "$name" "$expected" "$actual"
        ;;
        *)
        printf "FAIL %-34s expected=%s actual=%s\n" "$name" "$expected" "$actual"
        return 1
        ;;
    esac
}

check_code "clinical healthcheck" "200" "clinical-client" "http://oh-proxy/healthcheck"
check_code "guest healthcheck denied" "403" "guest-client" "http://oh-proxy/healthcheck"
check_code "lab laboratories allowed" "200,401" "lab-client" "http://oh-proxy/laboratories"
check_code "lab patients denied" "403" "lab-client" "http://oh-proxy/patients"
check_code "clinical patients allowed" "200,401" "clinical-client" "http://oh-proxy/patients"
check_code "vpn patients allowed" "200,401" "vpn-client" "http://oh-proxy/patients"
check_code "clinical CRUD API allowed" "200,401" "clinical-client" "http://oh-proxy/admissiontypes"
check_code "lab CRUD API denied" "403" "lab-client" "http://oh-proxy/admissiontypes"
check_code "dmz swagger allowed" "200" "dmz-client" "http://oh-proxy/swagger-ui/index.html"
check_code "clinical swagger denied" "403" "clinical-client" "http://oh-proxy/swagger-ui/index.html"
check_code "guest swagger denied" "403" "guest-client" "http://oh-proxy/swagger-ui/index.html"
