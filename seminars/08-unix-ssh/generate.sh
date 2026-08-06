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

echo 'print("hello over SSH")' > "$assets_dir/H5/project/src/app.py"
echo 'git metadata' > "$assets_dir/H5/project/.git/config"
echo 'virtual environment' > "$assets_dir/H5/project/.venv/pyvenv.cfg"
echo 'bytecode placeholder' > "$assets_dir/H5/project/src/__pycache__/app.cpython.pyc"

echo "Created $assets_dir"
