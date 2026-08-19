# Примеры решений

Решения записаны так, будто вы уже находитесь в каталоге задачи внутри `~/seminar-05/`.

## База

### B1

```bash
{
  echo "$PATH"
  which python3
  echo "$SHELL"
} > paths.txt
```

### B2

```bash
COURSE_LEVEL='basic'
echo "current=$COURSE_LEVEL" > course-level.txt
bash -c 'echo "child-before=${COURSE_LEVEL:-missing}"' >> course-level.txt
export COURSE_LEVEL
bash -c 'echo "child-after=$COURSE_LEVEL"' >> course-level.txt
```

### B3

```bash
cat > course.env <<'EOF'
COURSE_NAME='course-app'
export COURSE_DATA="$HOME/seminar-05/data"
EOF

source course.env
{
  echo "$COURSE_NAME"
  echo "$COURSE_DATA"
} > environment.txt
```

### B4

```bash
uv python find 3.12 > before.txt 2>&1     # если 3.12 не найдена — сначала uv python install 3.12
uv venv --python 3.12 .venv
source .venv/bin/activate
which python > inside.txt
python --version >> inside.txt 2>&1
deactivate
uv python find 3.12 > after.txt 2>&1
```

### B5

```bash
mkdir course-project
cd course-project
uv init
uv add requests
uv run python --version > versions.txt
uv run python -c 'import requests; print(requests.__version__)' >> versions.txt
uv tree > dependency-tree.txt
ls -l pyproject.toml uv.lock > project-files.txt
```

### B6

```bash
mkdir -p bin
cat > bin/course-info <<'EOF'
#!/usr/bin/env bash
echo "course-info: моя команда"
EOF
chmod +x bin/course-info

command -v course-info > lookup.txt || echo 'course-info: not found' > lookup.txt
export PATH="$PWD/bin:$PATH"
command -v course-info >> lookup.txt
course-info >> lookup.txt
```

## Среднее

### M1

```bash
apt list --installed 2> apt-errors.txt | tail -n +2 > installed-packages.txt
apt list --upgradable 2>> apt-errors.txt | tail -n +2 > upgradable-packages.txt
```

### M2

```bash
export PYTHONPATH="$PWD/modules"
python3 -c 'import course_module; print(course_module.VALUE); print(course_module.__file__)' > import.txt
```

### M3

```bash
mkdir -p project-restored
cp -r project-source/. project-restored/   # переносим проект целиком
rm -rf project-restored/.venv             # ...кроме окружения: его и надо восстановить
cd project-restored
uv sync                        # .venv собирается заново по pyproject.toml и uv.lock
uv run python --version > restored-versions.txt
uv run python -c 'import requests; print(requests.__version__)' >> restored-versions.txt
```

### M4

```bash
ldconfig -p > libraries-all.txt
head -n 20 libraries-all.txt > libraries.txt
ldd /usr/bin/head > head-libs.txt
```

### M5

```bash
systemctl --version > systemd.txt
systemctl status systemd-journald --no-pager >> systemd.txt 2>&1 || echo "$?" >> systemd.txt
journalctl -u systemd-journald -n 20 --no-pager > service-journal.txt 2>&1
systemctl list-units --type=service --no-pager > system-services.txt 2>&1
```

### M6

```bash
printf 'requests==2.31.0\n' > requirements.txt
python3 -m venv .venv                          # окружение средствами самого Python
source .venv/bin/activate                      # дальше python и pip — из .venv
python -m pip install -q -r requirements.txt
python -m pip freeze > installed-versions.txt
deactivate
```

## Сложное

### H1

```bash
uv venv --python 3.11 env-311
uv venv --python 3.12 env-312
env-311/bin/python --version > python-versions.txt
env-312/bin/python --version >> python-versions.txt
echo "$PWD/env-311/bin/python" > python-paths.txt
echo "$PWD/env-312/bin/python" >> python-paths.txt
```

### H2

```bash
mkdir dependency-update
cd dependency-update
uv init
uv add 'requests==2.31.0'
uv run python -c 'import requests; print(requests.__version__)' > before.txt
cp uv.lock uv.lock.before

uv add 'requests>=2.31,<3'     # верхнюю границу сохраняем: 3.x может быть несовместимой
uv lock --upgrade-package requests
uv sync
uv run python -c 'import requests; print(requests.__version__)' > after.txt
diff uv.lock.before uv.lock > lock-changes.txt || true
```

### H3

```bash
mkdir -p bin-one bin-two
printf '#!/usr/bin/env bash\necho one\n' > bin-one/course-info
printf '#!/usr/bin/env bash\necho two\n' > bin-two/course-info
chmod +x bin-one/course-info bin-two/course-info

PATH="$PWD/bin-one:$PWD/bin-two:$PATH" bash -c 'course-info; command -v course-info' > first.txt
PATH="$PWD/bin-two:$PWD/bin-one:$PATH" bash -c 'course-info; command -v course-info' > second.txt
```

### H4

```bash
systemctl cat "$SERVICE_NAME" > service-unit.txt 2> service-errors.txt
systemctl status "$SERVICE_NAME" --no-pager > service-status.txt 2>> service-errors.txt || true
journalctl -u "$SERVICE_NAME" -n 100 --no-pager > service-journal.txt 2>> service-errors.txt
```

### H5

```bash
mkdir -p report
{
  echo "PATH=$PATH"
  echo "PYTHONPATH=${PYTHONPATH:-}"
  echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}"
  which uv
  uv --version
  uv python find
} > report/environment.txt 2> report/errors.txt

apt list --installed > report/installed-packages.txt 2>> report/errors.txt
apt list --upgradable > report/upgradable-packages.txt 2>> report/errors.txt
ldconfig -p > report/libraries.txt 2>> report/errors.txt
systemctl --version > report/systemd.txt 2>> report/errors.txt
systemctl is-system-running >> report/systemd.txt 2>> report/errors.txt || true
```
