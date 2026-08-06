#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
assets_dir="$script_dir/assets"

rm -rf -- "$assets_dir"
mkdir -p \
  "$assets_dir/B4" \
  "$assets_dir/M1/keys" \
  "$assets_dir/M3/local-data/nested" \
  "$assets_dir/M4" \
  "$assets_dir/H2/local-data/nested" \
  "$assets_dir/H5/project/src" \
  "$assets_dir/H5/project/.git" \
  "$assets_dir/H5/project/.venv" \
  "$assets_dir/H5/project/src/__pycache__"

cat > "$assets_dir/B4/local.txt" <<'EOF'
File transferred through SSH.
Second line for content comparison.
EOF

echo 'alpha' > "$assets_dir/M3/local-data/a.txt"
echo 'beta' > "$assets_dir/M3/local-data/nested/b.txt"
cp -R "$assets_dir/M3/local-data/." "$assets_dir/H2/local-data/"

touch "$assets_dir/M4/course-known-hosts"

cat > "$assets_dir/H5/project/README.md" <<'EOF'
# Demo project

This directory contains files that must be copied and service directories that must be excluded.
EOF
echo 'print("hello over SSH")' > "$assets_dir/H5/project/src/app.py"
echo 'git metadata' > "$assets_dir/H5/project/.git/config"
echo 'virtual environment' > "$assets_dir/H5/project/.venv/pyvenv.cfg"
echo 'bytecode placeholder' > "$assets_dir/H5/project/src/__pycache__/app.cpython.pyc"

cat > "$assets_dir/README.md" <<'EOF'
# Входные данные

- `B4` — локальный файл для передачи.
- `M1` — пустой каталог для учебного ключа.
- `M3` — локальное дерево для синхронизации.
- `M4` — отдельный пустой `known_hosts`.
- `H2` — локальная копия дерева для изменения и синхронизации.
- `H5` — проект со служебными каталогами для проверки исключений.

Учебный SSH-сервер, удалённые каталоги и сервисы генератор создать не может.
EOF

echo "Created $assets_dir"
