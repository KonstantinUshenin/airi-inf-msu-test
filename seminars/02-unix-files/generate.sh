#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
assets_dir="$script_dir/assets"

rm -rf -- "$assets_dir"
mkdir -p \
  "$assets_dir/B4/parts" \
  "$assets_dir/B5/empty-directory" \
  "$assets_dir/B5/non-empty-directory" \
  "$assets_dir/M1" \
  "$assets_dir/M2/shared" \
  "$assets_dir/M3" \
  "$assets_dir/H2/source" \
  "$assets_dir/H2/destination" \
  "$assets_dir/H5/project/config" \
  "$assets_dir/H5/project/data" \
  "$assets_dir/H5/backups"

echo 'First part.' > "$assets_dir/B4/parts/01.txt"
echo 'Second part.' > "$assets_dir/B4/parts/02.txt"
echo 'Third part.' > "$assets_dir/B4/parts/03.txt"

echo 'remove this file' > "$assets_dir/B5/remove-me.txt"
echo 'keep this file' > "$assets_dir/B5/non-empty-directory/keep.txt"

echo 'existing input' > "$assets_dir/M1/exists.txt"

cat > "$assets_dir/M2/run.sh" <<'EOF'
#!/usr/bin/env bash
echo 'worker started'
EOF
chmod 600 "$assets_dir/M2/run.sh"

cat > "$assets_dir/M3/source.txt" <<'EOF'
alpha
beta
gamma
EOF

for index in 1 2 3 4 5 6 7 8 9 10; do
  head -c "$((index * 11))" /dev/zero | tr '\0' "$index" > "$assets_dir/H2/source/file-$index.txt"
done

echo 'mode=training' > "$assets_dir/H5/project/config/app.conf"
echo 'first row' > "$assets_dir/H5/project/data/part-1.txt"
echo 'second row is longer' > "$assets_dir/H5/project/data/part-2.txt"

echo "Created $assets_dir"
