#!/usr/bin/env bash
# Despliegue de Pronostix en una EC2 de AWS Academy (Amazon Linux 2023).
# Uso, desde EC2 Instance Connect:
#   curl -fsSL https://raw.githubusercontent.com/jdj40211/pronostix/main/deploy/ec2-bootstrap.sh | bash
# Es idempotente: se puede volver a correr para actualizar el codigo.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/jdj40211/pronostix.git}"
RAMA="${RAMA:-main}"
DESTINO="${DESTINO:-$HOME/pronostix}"
COMPOSE_VERSION="${COMPOSE_VERSION:-v2.29.7}"

echo ">> 1/5 Docker y git"
sudo dnf install -y docker git
sudo systemctl enable --now docker

echo ">> 2/5 Plugin de Docker Compose ${COMPOSE_VERSION}"
if ! sudo docker compose version >/dev/null 2>&1; then
  sudo mkdir -p /usr/local/lib/docker/cli-plugins
  sudo curl -fsSL \
    "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi
sudo docker compose version

echo ">> 3/5 Swap de 2 GB (la construccion de 6 imagenes aprieta la RAM)"
if ! swapon --show | grep -q swapfile; then
  sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
fi

echo ">> 4/5 Codigo (${RAMA})"
if [ -d "${DESTINO}/.git" ]; then
  git -C "${DESTINO}" fetch --quiet origin "${RAMA}"
  git -C "${DESTINO}" checkout --quiet "${RAMA}"
  git -C "${DESTINO}" reset --hard --quiet "origin/${RAMA}"
else
  git clone --quiet --branch "${RAMA}" "${REPO_URL}" "${DESTINO}"
fi

echo ">> 5/5 Levantando el ecosistema (db, redis, worker, django, 4 flask, nginx)"
cd "${DESTINO}"
export STATS_PROVIDER="${STATS_PROVIDER:-REAL}"
sudo -E docker compose up -d --build
sudo docker compose ps
echo ">> Listo. Gateway publico en el puerto 80 de esta instancia."
