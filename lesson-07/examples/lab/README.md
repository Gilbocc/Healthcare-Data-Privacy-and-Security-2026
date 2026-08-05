# Lesson 07 Lab: OpenHospital API Behind a Proxy

This lab deploys the real [`informatici/openhospital-api`](https://github.com/informatici/openhospital-api)
project with its MariaDB database, then places Nginx in front of it.

The learning path is deliberately progressive:

1. deploy OpenHospital API;
2. access it through an Nginx proxy that allows everything;
3. use Swagger from a DMZ-like documentation network to discover endpoints;
4. test login and real CRUD operations through the API;
5. replace the open policy with subnet/path restrictions;
6. verify that guest, lab, clinical, VPN, and DMZ networks behave differently;
7. inspect logs and explain the evidence.

## Prerequisites

- Docker and Docker Compose.
- Git.
- A shell with `make`, `sed`, and basic Unix tools. On Windows, WSL is recommended.
- Internet access for the first build, because the lab clones OpenHospital sources and downloads
  Maven dependencies.

The first build can take several minutes.

## Milestone 1: Prepare OpenHospital API

```bash
cd lesson-07/examples/lab
./prepare-openhospital-api.sh
```

This clones `openhospital-api` under `vendor/`, copies the lab `.env`, and runs the upstream
`make` target that prepares OpenHospital Core and configuration files.

## Milestone 2: Build and Start

```bash
docker compose build database backend
docker compose up -d database
```

Wait until the database is ready, then optionally load demo data:

```bash
docker compose run --rm oh-database-init
```

Start the API, proxy, and clients:

```bash
docker compose up -d backend reverse-proxy clinical-client lab-client guest-client vpn-client dmz-client
docker compose ps
```

## Milestone 3: Test the Open Proxy

The starter Nginx config allows everything. Use it to prove that the deployment works before
security rules are added.

```bash
docker compose exec clinical-client curl -i http://oh-proxy/healthcheck
docker compose exec guest-client curl -i http://oh-proxy/healthcheck
docker compose exec dmz-client curl -i http://oh-proxy/swagger-ui/index.html
```

At this stage Swagger is reachable because the starter policy is deliberately open. In the final
policy, Swagger will be reachable only from the DMZ-like network. Treat it as documentation for
operators and API testers, not as a clinical workstation tool.

Try login:

```bash
docker compose exec clinical-client curl -i \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  http://oh-proxy/auth/login
```

The demo database used in this lab accepts `admin` / `admin` for local API testing. If the login
fails, make sure `docker compose run --rm oh-database-init` completed successfully and inspect the
backend logs.

```bash
docker compose logs --tail=100 backend
```

## Milestone 4: Exercise Real CRUD Operations

Connectivity alone is not enough. A useful API lab should prove that normal operations work before
security rules are tightened. This exercise uses `AdmissionType`, a small administrative resource
with standard CRUD operations:

- `GET /admissiontypes` reads existing admission types;
- `POST /admissiontypes` creates a toy admission type;
- `PUT /admissiontypes` changes its description;
- `DELETE /admissiontypes/{code}` removes it.

Run the scripted version first:

```bash
./crud-admissiontypes.sh
```

The script logs in from the clinical subnet, extracts the JWT access token, and sends the token as
`Authorization: Bearer ...` on the CRUD requests. The record uses code `ZZ` by default and is meant
to be disposable lab data.

To run the same exercise manually, first get a token:

```bash
TOKEN=$(docker compose exec -T clinical-client curl -s \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  http://oh-proxy/auth/login | sed -n 's/.*"token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
```

Then perform create, read, update, and delete:

```bash
docker compose exec -T clinical-client curl -i \
  -H "Authorization: Bearer $TOKEN" \
  http://oh-proxy/admissiontypes

docker compose exec -T clinical-client curl -i \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"ZZ","description":"SECURITY LAB TRIAGE"}' \
  http://oh-proxy/admissiontypes

docker compose exec -T clinical-client curl -i \
  -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"ZZ","description":"SECURITY LAB TRIAGE UPDATED"}' \
  http://oh-proxy/admissiontypes

docker compose exec -T clinical-client curl -i \
  -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  http://oh-proxy/admissiontypes/ZZ
```

The security lesson is that the proxy is not only protecting pages. It is controlling access to
operations that can change hospital data. After the hardened policy is applied, the clinical subnet
can perform this administrative CRUD exercise, while the lab and guest subnets cannot.

## Milestone 4b: Call Any Lab API Easily

Use `api-call.sh` when you want to call one endpoint from one subnet and see the raw HTTP response:

```bash
./api-call.sh clinical GET /patients?page=0\&size=3
./api-call.sh lab GET /examtypes
OH_NO_AUTH=1 ./api-call.sh dmz GET /swagger-ui/index.html
./api-call.sh clinical POST /admissiontypes '{"code":"ZZ","description":"SECURITY LAB"}'
```

Use `crud-policy-apis.sh` when you want a guided tour of all API areas used by the lab policy:

```bash
./crud-policy-apis.sh
```

The guided script prints the response for each request. It covers:

- health checks from clinical and guest networks;
- Swagger from DMZ and clinical networks;
- full CRUD for `/admissiontypes` from the clinical network;
- full CRUD for `/examtypes` from the lab network;
- verified reads for real demo-data `/exams`, `/examrows`, `/admissions`, and `/laboratories`;
- full create/read/update for a temporary `/patients` record from the clinical network;
- denied calls from subnets that should not reach a path.

The guided script avoids fake lab-domain writes. OpenHospital laboratory requests and exam records
are tied to existing clinical workflows and database constraints, so this tutorial uses real demo data
for those API areas. A `403` means the proxy blocked the request before the API handled it.

## Milestone 5: Add Network Policy

Replace the starter policy with the solution policy:

```bash
cp nginx/solution.conf nginx/default.conf
docker compose exec reverse-proxy nginx -s reload
```

Read `nginx/solution.conf` before testing. The policy is:

- guest network cannot access OpenHospital API;
- lab network can access lab-related APIs such as `/laboratories`, `/exams`, `/examtypes`, and
  `/examrows`;
- lab network cannot access patient APIs such as `/patients`;
- clinical and VPN networks can access patient, admission, and admission-type APIs;
- Swagger and OpenAPI metadata are limited to the DMZ-like network.

## Milestone 6: Verify Subnet and Path Rules

```bash
./check-policy.sh
```

The expected final result is:

```text
PASS clinical healthcheck
PASS guest healthcheck denied
PASS lab laboratories allowed
PASS lab patients denied
PASS clinical patients allowed
PASS vpn patients allowed
PASS clinical CRUD API allowed
PASS lab CRUD API denied
PASS dmz swagger allowed
PASS clinical swagger denied
PASS guest swagger denied
```

Some API endpoints may return `401` or another application-level status if authentication is
required. That is still useful: Nginx should return `403` for a subnet/path that is blocked before
the API sees it. If an allowed request reaches the API but the API requires a token, the network
policy did its job and the application security layer is now responding.

## Milestone 7: Inspect Evidence

```bash
docker compose logs --tail=50 reverse-proxy
docker compose logs --tail=50 backend
```

Compare proxy evidence with application evidence:

- proxy logs show source subnet, path, and HTTP status;
- backend logs show whether the request reached OpenHospital API;
- denied guest requests should appear at the proxy but not as successful backend activity.

## Milestone 8: Design One New Rule

Choose one policy change and test it:

- allow lab users to read `/patients/search` but not `/patients`;
- allow VPN access to one specific read-only administrative endpoint;
- allow guest clients only to `/healthcheck`;
- create an `admin_net` and restrict `/users` and `/usergroups` to it.

Document the intended clinical reason, the Nginx rule, the test command, the observed status code,
and the relevant log line.

## Stop and Reset

```bash
docker compose down
```

To remove built containers and the database volume:

```bash
docker compose down -v
```

To remove downloaded OpenHospital sources:

```bash
rm -rf vendor
```
