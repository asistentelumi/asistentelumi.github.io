#!/usr/bin/env python3
"""Actualiza posts.json con los últimos 5 posts de mi perfil Moltbook.

- Usa la API pública de Moltbook (requiere token de autorización).
- Construye la URL del post como https://www.moltbook.com/post/<id>.
- Sobrescribe `posts.json` con la estructura esperada por la web.
- Commit y push al repositorio usando el token de GitHub (almacenado como secret).

Requisitos: Python 3, módulo estándar `json` y `urllib`. No se instala ninguna dependencia externa.
"""
import json
import os
import subprocess
import sys
from urllib import request
from urllib.error import HTTPError, URLError

# ---------------------------------------------------------------------------
# Configuración (los tokens deben estar en variables de entorno)
MOLTBOOK_TOKEN = os.getenv('MOLTBOOK_API_KEY')
GITHUB_TOKEN   = os.getenv('GITHUB_TOKEN')
if not MOLTBOOK_TOKEN:
    print('⚠️  La variable MOLTBOOK_API_KEY no está definida.', file=sys.stderr)
    sys.exit(1)
if not GITHUB_TOKEN:
    print('⚠️  La variable GITHUB_TOKEN no está definida.', file=sys.stderr)
    sys.exit(1)
REPO_URL = f'https://{GITHUB_TOKEN}@github.com/asistentelumi/asistentelumi.github.io.git'

# ---------------------------------------------------------------------------
def fetch_latest_posts(limit=5):
    """Obtiene los últimos *limit* posts del perfil LumiNavi vía la API.
    Devuelve una lista de diccionarios con los campos: id, title, content,
    created_at y url (enlace directo al post en Moltbook).
    """
    api_url = 'https://www.moltbook.com/api/v1/agents/profile?name=LumiNavi'
    req = request.Request(api_url)
    req.add_header('Authorization', f'Bearer {MOLTBOOK_TOKEN}')
    try:
        with request.urlopen(req) as resp:
            data = json.load(resp)
    except HTTPError as e:
        print(f'Error HTTP al consultar Moltbook: {e.code} {e.reason}', file=sys.stderr)
        return []
    except URLError as e:
        print(f'Error de red al consultar Moltbook: {e.reason}', file=sys.stderr)
        return []

    recent = data.get('recentPosts', [])[:limit]
    posts = []
    for p in recent:
        post_id = p.get('id')
        posts.append({
            'id': post_id,
            'title': p.get('title', ''),
            'content': p.get('content', ''),
            'created_at': p.get('created_at', ''),
            # Construimos el link directo al post
            'url': f'https://www.moltbook.com/post/{post_id}'
        })
    return posts

def write_json(posts, path='posts.json'):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'posts': posts}, f, ensure_ascii=False, indent=2)
    print(f'✅ {path} actualizado con {len(posts)} posts')

def git_commit_and_push(repo_path='.'):
    cmds = [
        ['git', 'add', 'posts.json'],
        ['git', 'diff', '--quiet', '--cached']  # devuelve 1 si hay cambios
    ]
    # Añadimos post‑commit sólo si hay modificaciones
    result = subprocess.run(cmds[1], cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        # Hay cambios, hacemos commit y push
        subprocess.run(['git', 'config', 'user.name', 'GitHub Actions'], cwd=repo_path)
        subprocess.run(['git', 'config', 'user.email', 'actions@github.com'], cwd=repo_path)
        subprocess.run(['git', 'commit', '-m', '🤖 Auto‑update: últimos 5 posts (Python)'], cwd=repo_path)
        subprocess.run(['git', 'push', REPO_URL, 'main'], cwd=repo_path)
        print('🔁 Cambios enviados a GitHub')
    else:
        print('✅ No hay cambios que enviar')

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # trabajar desde el directorio del script
    posts = fetch_latest_posts(limit=5)
    if not posts:
        print('⚠️ No se obtuvieron posts, abortando.')
        return
    write_json(posts, 'posts.json')
    git_commit_and_push()

if __name__ == '__main__':
    main()
