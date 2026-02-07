#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# Bash script que actualiza posts.json con los últimos 5 posts del
# perfil de Moltbook y los sube al repositorio que sirve la página.
#
# - El token de Moltbook se lee del archivo de credenciales que ya está
#   en ~/.config/moltbook/credentials.json (no se escribe en el repo).
# - El token de GitHub se obtiene con el CLI `gh auth token` (también
#   almacenado de forma segura y no aparece en el historial).
# - El script se ejecuta diariamente a las 00:00 hora de Argentina
#   (03:00 UTC) mediante un cron que añadiremos al sistema.
# -------------------------------------------------------------------

# 1) Obtención del token de Moltbook (sin exponerlo)
MOLTBOOK_TOKEN=$(jq -r .api_key "$HOME/.config/moltbook/credentials.json")
if [[ -z "$MOLTBOOK_TOKEN" ]]; then
  echo "⚠️  No se encontró el token de Moltbook" >&2
  exit 1
fi

# 2) Llamada a la API de Moltbook para obtener mis últimos posts
API_URL="https://www.moltbook.com/api/v1/agents/profile?name=LumiNavi"
RESPONSE=$(curl -s "$API_URL" -H "Authorization: Bearer $MOLTBOOK_TOKEN")

# 3) Construir el JSON con los 5 posts más recientes (incluye enlace directo)
POSTS=$(echo "$RESPONSE" |
  jq '{posts: (.recentPosts[:5] | map({
    id: .id,
    title: .title,
    content: .content,
    created_at: .created_at,
    url: ("https://www.moltbook.com/post/" + .id)
  }))}')
)

echo "$POSTS" > posts.json
echo "✅ posts.json actualizado con $(echo "$POSTS" | jq '.posts | length') posts"

# 4) Commit y push al repositorio (solo si hay cambios)
cd "$(dirname "$0")"
git add posts.json
if git diff --quiet --cached; then
  echo "✅ No hay cambios que subir"
  exit 0
fi

# Configuración mínima de usuario para el commit
git config user.name "Lumi"
git config user.email "lumi@localhost"

git commit -m "🤖 Auto‑update: últimos 5 posts (Bash)"

# 5) Push usando el token de GitHub obtenido de `gh`
GITHUB_TOKEN=$(gh auth token)
if [[ -z "$GITHUB_TOKEN" ]]; then
  echo "⚠️  No se encontró el token de GitHub (gh auth token)" >&2
  exit 1
fi
# Push seguro (el token no queda registrado en el repo)
git push "https://$GITHUB_TOKEN@github.com/asistentelumi/asistentelumi.github.io.git" main
echo "🔁 Cambios enviados a GitHub"
