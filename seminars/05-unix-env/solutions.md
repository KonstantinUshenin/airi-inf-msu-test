# Примеры решений

## База

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
echo "current-after=$COURSE_LEVEL" >> course-level.txt        # в текущей оболочке — как и была
bash -c 'echo "child-after=$COURSE_LEVEL"' >> course-level.txt  # а вот дочерняя теперь её видит
```

### B3

```bash
source assets/B3/course.env
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
cd course-project || exit 1
uv init
uv add requests

mkdir -p evidence                       # задача просит сложить всё именно сюда
uv run python --version > evidence/versions.txt
uv run python -c 'import requests; print(requests.__version__)' >> evidence/versions.txt
uv tree > evidence/dependency-tree.txt
cp pyproject.toml uv.lock evidence/     # копии, а не ls: их потом читают глазами
```

## Среднее

### M1

```bash
apt list --installed > installed-packages.txt 2> apt-errors.txt
apt list --upgradable > upgradable-packages.txt 2>> apt-errors.txt
```

### M2

```bash
export PYTHONPATH="$PWD/assets/M2/modules"
python3 -c 'import course_module; print(course_module.VALUE); print(course_module.__file__)' > import.txt
```

### M3

```bash
mkdir project-restored
cp assets/M3/project-source/pyproject.toml assets/M3/project-source/uv.lock project-restored/
cd project-restored
uv sync
uv run python --version > restored-versions.txt
uv run python -c 'import requests; print(requests.__version__)' >> restored-versions.txt
```

### M4

```bash
# Два независимых проекта: у каждого свой .venv и своя версия requests.
uv init --python 3.12 project-a
cd project-a || exit 1
uv add 'requests==2.31.0'
uv run python -c 'import sys; print(sys.executable)' > ../project-a.txt
uv run python --version >> ../project-a.txt
uv run python -c 'import requests; print(requests.__version__)' >> ../project-a.txt
cd ..

uv init --python 3.12 project-b
cd project-b || exit 1
uv add 'requests>=2.32,<3'
uv run python -c 'import sys; print(sys.executable)' > ../project-b.txt
uv run python --version >> ../project-b.txt
uv run python -c 'import requests; print(requests.__version__)' >> ../project-b.txt
cd ..

# Пути к python различаются — окружения независимы, версии requests тоже.
diff project-a.txt project-b.txt || true
```

### M5

```bash
systemctl --version > systemd.txt
systemctl status systemd-journald --no-pager >> systemd.txt 2>&1 || echo "$?" >> systemd.txt
journalctl -u systemd-journald -n 20 --no-pager > service-journal.txt 2>&1
systemctl list-units --type=service --no-pager > system-services.txt 2>&1
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

uv add 'requests>=2.31'
uv lock --upgrade-package requests
uv sync
uv run python -c 'import requests; print(requests.__version__)' > after.txt
diff uv.lock.before uv.lock > lock-changes.txt || true
```

### H3

```bash
PATH="$PWD/assets/H3/bin-one:$PWD/assets/H3/bin-two:$PATH" bash -c 'course-info; which course-info' > first.txt
PATH="$PWD/assets/H3/bin-two:$PWD/assets/H3/bin-one:$PATH" bash -c 'course-info; which course-info' > second.txt
```

### H4

```bash
systemctl cat "$SERVICE_NAME" > service-unit.txt 2> service-errors.txt
systemctl status "$SERVICE_NAME" --no-pager > service-status.txt 2>> service-errors.txt || true
journalctl -u "$SERVICE_NAME" -n 100 --no-pager > service-journal.txt 2>> service-errors.txt
```

### H5

```bash
cd assets/H5/broken-project || exit 1
mkdir -p report

# Что было до починки: uv в PATH не находится, поэтому команда не работает.
{
  echo "PATH=$PATH"
  command -v uv || echo 'uv не найден в PATH'
} > report/before.txt 2> errors.txt

# Чиним поиск: uv лежит в ~/.local/bin, этого каталога в PATH не было.
export PATH="$HOME/.local/bin:$PATH"

# Lock-файл устарел: в нём requests==2.31.0, а pyproject просит >=2.32,<3.
# uv lock пересобирает его под текущий pyproject.toml.
uv lock > sync.txt 2>> errors.txt
uv lock --check > lock-check.txt 2>> errors.txt

# Окружения не было — uv sync создаёт .venv по .python-version и уже
# согласованному lock-файлу.
uv sync >> sync.txt 2>> errors.txt
uv run python app.py > app-stdout.txt 2>> errors.txt

{
  echo "PATH=$PATH"
  command -v uv
  uv --version
  uv run python -c 'import sys; print(sys.executable)'
  uv run python --version
  uv tree
} > report/after.txt 2>> errors.txt
```
