# Примеры решений

## Basic

### B1

```bash
{
  echo "$PATH"
  which python3
  which "$SHELL"
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
source course.env
{
  echo "$COURSE_NAME"
  echo "$DATA_DIRECTORY"
} > environment.txt
```

### B4

```bash
uv python find 3.12 > before.txt
uv venv --python 3.12 .venv
source .venv/bin/activate
which python > inside.txt
python --version >> inside.txt 2>&1
deactivate
uv python find 3.12 > after.txt
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
apt list --installed > installed-packages.txt 2> apt-errors.txt
apt list --upgradable > upgradable-packages.txt 2>> apt-errors.txt
```

### B7

```bash
export PYTHONPATH="$PWD/modules"
python3 -c 'import course_module; print(course_module.VALUE); print(course_module.__file__)' > import.txt
```

### B8

```bash
mkdir project-restored
cp project-source/pyproject.toml project-source/uv.lock project-restored/
cd project-restored
uv sync
uv run python --version > restored-versions.txt
uv run python -c 'import requests; print(requests.__version__)' >> restored-versions.txt
```

### B9

```bash
ldconfig -p > libraries-all.txt
head -n 20 libraries-all.txt > libraries.txt
```

### B10

```bash
systemctl --version > systemd.txt
systemctl status systemd-journald --no-pager >> systemd.txt 2>&1 || echo "$?" >> systemd.txt
journalctl -u systemd-journald -n 20 --no-pager > service-journal.txt 2>&1
systemctl list-units --type=service --no-pager > system-services.txt 2>&1
```

## Advanced

### A1

```bash
uv venv --python 3.11 env-311
uv venv --python 3.12 env-312
env-311/bin/python --version > python-versions.txt
env-312/bin/python --version >> python-versions.txt
echo "$PWD/env-311/bin/python" > python-paths.txt
echo "$PWD/env-312/bin/python" >> python-paths.txt
```

### A2

```bash
mkdir dependency-update
cd dependency-update
uv init
uv add 'requests==2.31.0'
uv run python -c 'import requests; print(requests.__version__)' > before.txt
cp uv.lock uv.lock.before

uv add 'requests>=2.31'
uv lock --upgrade-package requests
uv sync
uv run python -c 'import requests; print(requests.__version__)' > after.txt
diff uv.lock.before uv.lock > lock-changes.txt || true
```

### A3

```bash
PATH="$PWD/bin-one:$PWD/bin-two:$PATH" bash -c 'course-info; which course-info' > first.txt
PATH="$PWD/bin-two:$PWD/bin-one:$PATH" bash -c 'course-info; which course-info' > second.txt
```

### A4

```bash
systemctl cat "$SERVICE_NAME" > service-unit.txt 2> service-errors.txt
systemctl status "$SERVICE_NAME" --no-pager > service-status.txt 2>> service-errors.txt || true
journalctl -u "$SERVICE_NAME" -n 100 --no-pager > service-journal.txt 2>> service-errors.txt
```

### A5

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
