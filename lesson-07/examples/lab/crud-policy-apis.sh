#!/usr/bin/env sh
set -eu

API="http://oh-proxy"
USER="${OH_ADMIN_USER:-admin}"
PASS="${OH_ADMIN_PASSWORD:-admin}"

token_for() {
    service="$1"
    login_payload=$(printf '{"username":"%s","password":"%s"}' "$USER" "$PASS")
    response="$(
        docker compose exec -T "$service" curl -s \
            -H "Content-Type: application/json" \
            -d "$login_payload" \
            "$API/auth/login" || true
    )"
    printf "%s" "$response" | sed -n 's/.*"token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
}

call() {
    service="$1"
    token="$2"
    method="$3"
    path="$4"
    body="${5:-}"

    printf "\n--- %s %s via %s ---\n" "$method" "$path" "$service"
    if [ -n "$body" ]; then
        docker compose exec -T "$service" curl -s -i \
            -X "$method" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$body" \
            "$API$path"
    else
        docker compose exec -T "$service" curl -s -i \
            -X "$method" \
            -H "Authorization: Bearer $token" \
            "$API$path"
    fi
    printf "\n"
}

call_no_auth() {
    service="$1"
    method="$2"
    path="$3"

    printf "\n--- %s %s via %s, anonymous ---\n" "$method" "$path" "$service"
    docker compose exec -T "$service" curl -s -i -X "$method" "$API$path"
    printf "\n"
}

quiet_call() {
    service="$1"
    token="$2"
    method="$3"
    path="$4"

    docker compose exec -T "$service" curl -s -o /dev/null \
        -X "$method" \
        -H "Authorization: Bearer $token" \
        "$API$path" || true
}

extract_code() {
    sed -n 's/.*"code"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p'
}

clinical_token="$(token_for clinical-client)"
lab_token="$(token_for lab-client)"
vpn_token="$(token_for vpn-client)"

if [ -z "$clinical_token" ] || [ -z "$lab_token" ] || [ -z "$vpn_token" ]; then
    printf "Could not obtain all tokens. Make sure demo data is loaded and admin/admin works.\n"
    exit 1
fi

printf "\n=== Discovery and Network Surface ===\n"
call_no_auth clinical-client GET /healthcheck
call_no_auth guest-client GET /healthcheck
call_no_auth dmz-client GET /swagger-ui/index.html
call_no_auth clinical-client GET /swagger-ui/index.html

printf "\n=== Clinical API: Admission Types, Full CRUD ===\n"
quiet_call clinical-client "$clinical_token" DELETE /admissiontypes/ZZ
call clinical-client "$clinical_token" GET /admissiontypes
call clinical-client "$clinical_token" POST /admissiontypes \
    '{"code":"ZZ","description":"SECURITY LAB TRIAGE"}'
call clinical-client "$clinical_token" GET /admissiontypes
call clinical-client "$clinical_token" PUT /admissiontypes \
    '{"code":"ZZ","description":"SECURITY LAB TRIAGE UPDATED"}'
call clinical-client "$clinical_token" GET /admissiontypes
call clinical-client "$clinical_token" DELETE /admissiontypes/ZZ
call clinical-client "$clinical_token" GET /admissiontypes
call lab-client "$lab_token" GET /admissiontypes

printf "\n=== Lab API: Exam Types, Full CRUD ===\n"
quiet_call lab-client "$lab_token" DELETE /examtypes/ZT
call lab-client "$lab_token" GET /examtypes
call lab-client "$lab_token" POST /examtypes \
    '{"code":"ZT","description":"Security lab exam type"}'
call lab-client "$lab_token" GET /examtypes
call lab-client "$lab_token" PUT /examtypes/ZT \
    '{"code":"ZT","description":"Security lab exam type updated"}'
call lab-client "$lab_token" GET /examtypes
call lab-client "$lab_token" DELETE /examtypes/ZT
call lab-client "$lab_token" GET /examtypes

printf "\n=== Lab API: Exams and Exam Rows, Verified Reads ===\n"
printf "These calls use real demo-data exam records. They are read examples, not toy writes.\n"
call lab-client "$lab_token" GET /exams/description/WBC
call lab-client "$lab_token" GET /examrows/byExamCode/01.02
call clinical-client "$clinical_token" GET /examrows/byExamCode/01.02

printf "\n=== Clinical API: Patients, Full CRUD ===\n"
patient_payload='{"firstName":"Security","secondName":"Patient","birthDate":"1990-01-01","age":36,"agetype":"Y","sex":"F","address":"Training ward","city":"St Isidore","telephone":"+390000000","note":"Lesson 07 toy patient","motherName":"Mary","mother":"A","fatherName":"Joseph","father":"A","bloodType":"A+","hasInsurance":"N","parentTogether":"Y","taxCode":"SECURITYLAB01","lock":0,"allergies":"none","anamnesis":"training","status":"O","consensusFlag":true,"consensusServiceFlag":true}'
patient_create_response="$(
    docker compose exec -T clinical-client curl -s -i \
        -X POST \
        -H "Authorization: Bearer $clinical_token" \
        -H "Content-Type: application/json" \
        -d "$patient_payload" \
        "$API/patients"
)"
printf "\n--- POST /patients via clinical-client ---\n%s\n" "$patient_create_response"
patient_code="$(printf "%s" "$patient_create_response" | extract_code | head -n 1)"
if [ -n "$patient_code" ]; then
    call clinical-client "$clinical_token" GET "/patients/$patient_code"
    patient_update_payload="$(printf '%s' "$patient_payload" | sed "s/{/{\"code\":$patient_code,/; s/Security\",\"secondName\":\"Patient/Security\",\"secondName\":\"Patient Updated/")"
    call clinical-client "$clinical_token" PUT "/patients/$patient_code" \
        "$patient_update_payload"
    call clinical-client "$clinical_token" GET "/patients/$patient_code"
    call clinical-client "$clinical_token" DELETE "/patients/$patient_code"
else
    printf "Patient creation did not expose a numeric code; continuing with read-only patient examples.\n"
fi
call clinical-client "$clinical_token" GET '/patients?page=0&size=3'
call lab-client "$lab_token" GET /patients

printf "\n=== Clinical API: Admissions, Read and Probe ===\n"
call clinical-client "$clinical_token" GET '/admissions?admissionrange=2020-01-01T00:00:00&admissionrange=2027-12-31T23:59:59&page=0&size=3&paged=true'
call vpn-client "$vpn_token" GET '/admissions?admissionrange=2020-01-01T00:00:00&admissionrange=2027-12-31T23:59:59&page=0&size=3&paged=true'
call lab-client "$lab_token" GET /admissions

printf "\n=== Lab API: Laboratories, Verified Reads ===\n"
printf "Laboratory writes require a valid OpenHospital clinical workflow. This lab reads existing requests and focuses on subnet policy.\n"
call lab-client "$lab_token" GET '/laboratories?oneWeek=false&page=0&size=3'
call lab-client "$lab_token" GET /laboratories/15
call_no_auth guest-client GET /laboratories || true

printf "\n=== Cleanup ===\n"

printf "\nDone. Review the responses above to see which layer answered each request.\n"
