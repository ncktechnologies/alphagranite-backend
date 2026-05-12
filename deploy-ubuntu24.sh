#!/usr/bin/env bash
set -euo pipefail

# Ubuntu 24.04 bootstrap + deploy script for Alpha Granite backend.
# - Installs: git, nginx, postgresql, certbot, docker engine + compose plugin
# - Clones/updates code from GitHub
# - Prepares env file with local PostgreSQL DATABASE_URL (hosted on server)
# - Deploys API using Docker Compose
# - Optionally provisions Let's Encrypt TLS via nginx plugin
#
# Usage:
#   sudo bash deploy-ubuntu24.sh
#
# Optional environment overrides:
#   APP_USER=ubuntu
#   APP_DIR=/var/platform/alphagranite-backend
#   REPO_URL=https://github.com/ncktechnologies/alphagranite-backend.git
#   REPO_BRANCH=dev
#   DOMAIN=api.example.com
#   CERTBOT_EMAIL=ops@example.com
#   WEB_HOST_PORT=8000
#   APP_ENV_FILE=.env.production
#   COMPOSE_PROJECT_NAME=alphagranite
#   DATABASE_URL=postgresql://admin:...@host:5432/alpha_granite_dev
#   DB_NAME=alpha_granite
#   DB_USER=alpha_granite
#   DB_PASSWORD=<secure-password>
#   DB_PORT=5432
#   PG_ALLOWED_CIDR=0.0.0.0/0
#   DRY_RUN=1

APP_USER="${APP_USER:-ubuntu}"
APP_DIR="${APP_DIR:-/var/platform/alphagranite-backend}"
REPO_URL="${REPO_URL:-https://chuksugwuh:<secret-here>@github.com/ncktechnologies/alphagranite-backend.git}"
REPO_BRANCH="${REPO_BRANCH:-dev}"
DOMAIN="${DOMAIN:-dev.api.ag.protechadvance.com}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-chuks@carpediemts.com}"
WEB_HOST_PORT="${WEB_HOST_PORT:-8000}"
APP_ENV_FILE="${APP_ENV_FILE:-.env.dev}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-alphagranite}"
DATABASE_URL="${DATABASE_URL:-}"
DB_NAME="${DB_NAME:-alpha_granite}"
DB_USER="${DB_USER:-alpha_granite}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_PORT="${DB_PORT:-5432}"
PG_ALLOWED_CIDR="${PG_ALLOWED_CIDR:-0.0.0.0/0}"
DRY_RUN="${DRY_RUN:-0}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "ERROR: Run as root (use sudo)."
  exit 1
fi

if [[ -z "${APP_USER:-}" || "${APP_USER}" == "root" ]]; then
  echo "ERROR: APP_USER must be a non-root user (example: ubuntu)."
  exit 1
fi

if ! id "${APP_USER}" >/dev/null 2>&1; then
  echo "ERROR: APP_USER '${APP_USER}' does not exist."
  exit 1
fi

if [[ "${REPO_BRANCH}" != dev* ]]; then
  echo "ERROR: REPO_BRANCH must start with 'dev' (for example: dev or dev-feature-x)."
  exit 1
fi

if [[ -z "${DATABASE_URL}" && -z "${DB_PASSWORD}" ]]; then
  DB_PASSWORD="$(openssl rand -base64 24 | tr -d '\n')"
  echo "INFO: Generated random DB_PASSWORD."
fi

log() {
  echo "[deploy] $*"
}

print_dry_run_plan() {
  cat <<EOF
[deploy] DRY RUN mode enabled. No changes will be made.

Planned actions:
1. Install base packages: git, nginx, certbot, postgresql, ufw, prerequisites
2. Install Docker Engine + Compose plugin (if missing)
3. Configure firewall (OpenSSH, Nginx Full, PostgreSQL ${DB_PORT} from ${PG_ALLOWED_CIDR})
4. Provision local PostgreSQL role/database and network access
5. Clone/update repo: ${REPO_URL} (branch: ${REPO_BRANCH}) into ${APP_DIR}
6. Prepare env file: ${APP_ENV_FILE}
7. Deploy Docker service: web (compose project: ${COMPOSE_PROJECT_NAME})
8. Configure host nginx reverse proxy for domain: ${DOMAIN}
9. Run certbot for TLS using email: ${CERTBOT_EMAIL}

Resolved runtime values:
- APP_USER=${APP_USER}
- APP_DIR=${APP_DIR}
- REPO_URL=${REPO_URL}
- REPO_BRANCH=${REPO_BRANCH}
- DOMAIN=${DOMAIN}
- CERTBOT_EMAIL=${CERTBOT_EMAIL}
- APP_ENV_FILE=${APP_ENV_FILE}
- DATABASE_URL=$(if [[ -n "${DATABASE_URL}" ]]; then echo "${DATABASE_URL}"; else echo "auto-generated (local)"; fi)

To execute for real, rerun without DRY_RUN=1.
EOF
}

install_base_packages() {
  log "Installing base packages (git, nginx, postgres, certbot, prerequisites)..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    postgresql \
    postgresql-contrib \
    ufw \
    openssl

  systemctl enable --now nginx
  systemctl enable --now postgresql
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    log "Docker already installed; skipping installation."
  else
    log "Installing Docker Engine + Docker Compose plugin..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    cat >/etc/apt/sources.list.d/docker.list <<EOF

deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable
EOF

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
  fi

  usermod -aG docker "${APP_USER}"
}

configure_firewall() {
  log "Configuring firewall (UFW)..."
  ufw allow OpenSSH >/dev/null 2>&1 || true
  ufw allow 'Nginx Full' >/dev/null 2>&1 || true
  ufw allow from "${PG_ALLOWED_CIDR}" to any port "${DB_PORT}" proto tcp >/dev/null 2>&1 || true
  ufw --force enable >/dev/null 2>&1 || true
}

configure_postgres() {
  log "Configuring local PostgreSQL database and role..."

  # Ensure postgres service is ready
  systemctl restart postgresql

  sudo -u postgres psql <<SQL
DO
\$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
      CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}';
   ELSE
      ALTER ROLE ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
   END IF;
END
\$\$;
SQL

  if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
    sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"
  fi

  log "Configuring PostgreSQL network access (listen on all interfaces)..."
  local pg_conf
  local pg_hba

  pg_conf="$(sudo -u postgres psql -tAc "SHOW config_file" | xargs)"
  pg_hba="$(sudo -u postgres psql -tAc "SHOW hba_file" | xargs)"

  if [[ -z "${pg_conf}" || -z "${pg_hba}" ]]; then
    echo "ERROR: Unable to locate PostgreSQL config files."
    exit 1
  fi

  # Ensure PostgreSQL listens beyond localhost.
  if grep -qE "^[[:space:]]*#?[[:space:]]*listen_addresses[[:space:]]*=" "${pg_conf}"; then
    sed -i "s|^[#[:space:]]*listen_addresses[[:space:]]*=.*|listen_addresses = '*'|" "${pg_conf}"
  else
    echo "listen_addresses = '*'" >>"${pg_conf}"
  fi

  # Allow password-authenticated remote connections for requested CIDR.
  if ! grep -q "host\s\+all\s\+all\s\+${PG_ALLOWED_CIDR}\s\+scram-sha-256" "${pg_hba}"; then
    echo "host all all ${PG_ALLOWED_CIDR} scram-sha-256" >>"${pg_hba}"
  fi

  systemctl restart postgresql
}

maybe_configure_postgres() {
  configure_postgres
}

clone_or_update_repo() {
  log "Cloning/updating repository into ${APP_DIR}..."
  install -d -m 0755 "${APP_DIR}"
  chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

  if [[ ! -d "${APP_DIR}/.git" ]]; then
    sudo -u "${APP_USER}" git clone "${REPO_URL}" "${APP_DIR}"
  fi

  sudo -u "${APP_USER}" git -C "${APP_DIR}" fetch --all --prune
  sudo -u "${APP_USER}" git -C "${APP_DIR}" checkout "${REPO_BRANCH}"
  sudo -u "${APP_USER}" git -C "${APP_DIR}" pull --ff-only origin "${REPO_BRANCH}"
}

prepare_env_file() {
  log "Preparing ${APP_ENV_FILE}..."

  local env_path="${APP_DIR}/${APP_ENV_FILE}"
  if [[ ! -f "${env_path}" ]]; then
    if [[ -f "${APP_DIR}/compose.staging.env.example" ]]; then
      cp "${APP_DIR}/compose.staging.env.example" "${env_path}"
    elif [[ -f "${APP_DIR}/compose.dev.env.example" ]]; then
      cp "${APP_DIR}/compose.dev.env.example" "${env_path}"
    elif [[ -f "${APP_DIR}/.env.example" ]]; then
      cp "${APP_DIR}/.env.example" "${env_path}"
    else
      touch "${env_path}"
    fi
  fi

  # Use external DATABASE_URL when provided; otherwise fallback to host PostgreSQL.
  local db_url
  if [[ -n "${DATABASE_URL}" ]]; then
    db_url="${DATABASE_URL}"
  else
    db_url="postgresql://${DB_USER}:${DB_PASSWORD}@host.docker.internal:5432/${DB_NAME}"
  fi

  grep -q '^DATABASE_URL=' "${env_path}" \
    && sed -i "s|^DATABASE_URL=.*|DATABASE_URL=${db_url}|" "${env_path}" \
    || echo "DATABASE_URL=${db_url}" >>"${env_path}"

  grep -q '^WEB_HOST_PORT=' "${env_path}" \
    && sed -i "s|^WEB_HOST_PORT=.*|WEB_HOST_PORT=${WEB_HOST_PORT}|" "${env_path}" \
    || echo "WEB_HOST_PORT=${WEB_HOST_PORT}" >>"${env_path}"

  grep -q '^COMPOSE_PROJECT_NAME=' "${env_path}" \
    && sed -i "s|^COMPOSE_PROJECT_NAME=.*|COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}|" "${env_path}" \
    || echo "COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}" >>"${env_path}"

  chown "${APP_USER}:${APP_USER}" "${env_path}"
}

configure_nginx_site() {
  log "Configuring host nginx reverse proxy..."

  local server_name
  if [[ -n "${DOMAIN}" ]]; then
    server_name="${DOMAIN}"
  else
    server_name="_"
  fi

  cat >/etc/nginx/sites-available/alphagranite-backend.conf <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${server_name};

    client_max_body_size 100m;

    location / {
        proxy_pass http://127.0.0.1:${WEB_HOST_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

  ln -sf /etc/nginx/sites-available/alphagranite-backend.conf /etc/nginx/sites-enabled/alphagranite-backend.conf
  rm -f /etc/nginx/sites-enabled/default

  nginx -t
  systemctl reload nginx
}

provision_tls_if_configured() {
  if [[ -z "${DOMAIN}" || -z "${CERTBOT_EMAIL}" ]]; then
    log "Skipping certbot (set DOMAIN and CERTBOT_EMAIL to enable TLS provisioning)."
    return
  fi

  log "Requesting/renewing Let's Encrypt certificate for ${DOMAIN}..."
  certbot --nginx -d "${DOMAIN}" -m "${CERTBOT_EMAIL}" --agree-tos --non-interactive --redirect
}

deploy_containers() {
  log "Deploying app with Docker Compose..."

  local env_path="${APP_ENV_FILE}"
  sudo -u "${APP_USER}" bash -lc "cd '${APP_DIR}' && mkdir -p static/uploads static/defaults logs"

  # Deploy only app service; host nginx handles TLS/reverse proxy.
  sudo -u "${APP_USER}" bash -lc "cd '${APP_DIR}' && docker compose --env-file '${env_path}' -p '${COMPOSE_PROJECT_NAME}' up -d --build web"

  sudo -u "${APP_USER}" bash -lc "cd '${APP_DIR}' && docker compose --env-file '${env_path}' -p '${COMPOSE_PROJECT_NAME}' ps"
}

print_summary() {
  cat <<EOF

Deployment complete.

Application directory: ${APP_DIR}
Branch: ${REPO_BRANCH}
Compose project: ${COMPOSE_PROJECT_NAME}
Env file: ${APP_ENV_FILE}
Web port: ${WEB_HOST_PORT}
Domain: ${DOMAIN:-<not set>}

PostgreSQL:
  mode: $(if [[ -n "${DATABASE_URL}" ]]; then echo "external"; else echo "local-host"; fi)
  database_url: ${DATABASE_URL:-postgresql://${DB_USER}:***@host.docker.internal:${DB_PORT}/${DB_NAME}}
  $(if [[ -z "${DATABASE_URL}" ]]; then echo "user: ${DB_USER}"; fi)
  $(if [[ -z "${DATABASE_URL}" ]]; then echo "password: ${DB_PASSWORD}"; fi)
  $(if [[ -z "${DATABASE_URL}" ]]; then echo "port: ${DB_PORT}"; fi)
  $(if [[ -z "${DATABASE_URL}" ]]; then echo "allowed_cidr: ${PG_ALLOWED_CIDR}"; fi)

Next steps:
1. Re-login as ${APP_USER} (or run: newgrp docker) before manual docker commands.
2. Verify app health:
   curl http://127.0.0.1:${WEB_HOST_PORT}/health
3. If domain is configured, test HTTPS:
   curl -I https://${DOMAIN}

EOF
}

main() {
  if [[ "${DRY_RUN}" == "1" ]]; then
    print_dry_run_plan
    return 0
  fi

  install_base_packages
  install_docker
  configure_firewall
  maybe_configure_postgres
  clone_or_update_repo
  prepare_env_file
  deploy_containers
  configure_nginx_site
  provision_tls_if_configured
  print_summary
}

main "$@"
