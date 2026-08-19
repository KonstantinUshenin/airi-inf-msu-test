# Практическая работа

**Выход:** `.sh` или `.ipynb`.

Работаем в домашнем каталоге — `~/seminar-05/`, а не в `/tmp`: `/tmp` вычищается при перезагрузке, а решения понадобятся на защите. Скопируйте в него **содержимое** каталога семинара (`cp -r <репозиторий>/seminars/05-unix-env/. ~/seminar-05/`) и все команды выполняйте из `~/seminar-05/` — там же лежит `generate.sh`.

Перед началом запустите `./generate.sh`. Подготовленные входные файлы находятся в `assets/{ID}/`. Результаты складывайте рядом, в текущий каталог.

## База — 5 задач

### B1. PATH

**need:** Linux.

Сохраните значение `PATH`, путь к текущему Python и путь к shell в `paths.txt`.

### B2. Переменная окружения

**need:** нет.

Создайте `COURSE_LEVEL`. В `course-level.txt` сохраните её видимость в текущей и дочерней оболочке до и после экспорта.

### B3. Source

**need:** `assets/B3/course.env` с переменными `COURSE_NAME` и `DATA_DIRECTORY`.

Подключите `course.env` к текущей оболочке. Сохраните полученные значения в `environment.txt`.

### B4. Virtual environment

**need:** `uv`; доступ к Python 3.12.

Создайте `.venv` на Python 3.12 через uv. Сохраните вывод `uv python find 3.12` до активации в `before.txt`; внутри активированного окружения — `which python` и `python --version` в `inside.txt`; после деактивации снова `uv python find 3.12` — в `after.txt`.

### B5. Зависимости Python

**need:** `uv`; доступ к пакету `requests`.

Создайте uv-проект и добавьте `requests`. В каталоге `evidence` сохраните версии Python и `requests`, дерево зависимостей, копии `pyproject.toml` и `uv.lock`.

## Среднее — 5 задач

### M1. Системные пакеты

**need:** Debian или Ubuntu с актуальным индексом APT.

Сохраните установленные системные пакеты в `installed-packages.txt`, доступные обновления — в `upgradable-packages.txt`, ошибки — в `apt-errors.txt`.

### M2. PYTHONPATH

**need:** каталог `assets/M2/modules` с модулем `course_module.py`.

Сделайте модуль доступным Python через `PYTHONPATH`. Сохраните импортированное значение и путь загруженного файла в `import.txt`.

### M3. Восстановление uv-окружения

**need:** `uv`; каталог `assets/M3/project-source` с `pyproject.toml`, `uv.lock` и прямой зависимостью `requests`.

Создайте чистый каталог `project-restored`, перенесите в него только файлы описания проекта и восстановите окружение. Сохраните версии Python и `requests` в `restored-versions.txt`.

### M4. Изоляция двух проектов

**need:** `uv`; Python 3.12; доступ к `requests==2.31.0` и `requests>=2.32,<3`.

Создайте два независимых проекта на Python 3.12 с указанными версиями `requests`. Путь к Python, версию Python и версию `requests` сохраните в `project-a.txt` и `project-b.txt`.

### M5. Systemd

**need:** Linux с systemd.

Сохраните версию systemd, состояние одной системной службы, последние двадцать строк её журнала и список загруженных системных служб.

## Сложное — 5 задач

### H1. Две версии Python

**need:** `uv`; доступ к Python 3.11 и 3.12.

Создайте два независимых окружения на Python 3.11 и 3.12. Сохраните версии в `python-versions.txt`, пути — в `python-paths.txt`.

### H2. Обновление зависимости

**need:** `uv`; доступ к пакету `requests`.

Создайте uv-проект с `requests==2.31.0`. Сохраните исходную версию в `before.txt`, а lock-файл — в `uv.lock.before`. Пока в `pyproject.toml` стоит жёсткое `==2.31.0`, обновлять нечего: сначала ослабьте ограничение до диапазона (например, `>=2.31,<3`), и только потом обновите один `requests`. Сохраните новую версию в `after.txt`, изменения lock-файла — в `lock-changes.txt`.

### H3. PATH и приоритет

**need:** каталоги `assets/H3/bin-one` и `assets/H3/bin-two` с разными вариантами команды `course-info`.

Получите разные результаты команды при разном порядке каталогов в `PATH`. Сохраните результат и применённый путь в `first.txt` и `second.txt`.

### H4. Диагностика службы

**need:** Linux с systemd; переменная `SERVICE_NAME` с именем системной службы.

Сохраните unit-файл в `service-unit.txt`, состояние — в `service-status.txt`, последние сто строк журнала — в `service-journal.txt`, ошибки — в `service-errors.txt`.

### H5. Восстановление проекта

**need:** Linux; `uv` установлен как `$HOME/.local/bin/uv`, но этот каталог отсутствует в `PATH`; `assets/H5/broken-project` содержит `pyproject.toml`, устаревший `uv.lock`, `.python-version` с Python 3.12 и `app.py`; `.venv` отсутствует.

Восстановите поиск `uv`, согласуйте lock-файл с проектом, создайте окружение и запустите приложение. В `report/before.txt` сохраните исходные `PATH` и результат поиска `uv`; в `report/after.txt` — исправленный `PATH`, путь и версию `uv`, путь и версию Python, дерево зависимостей. Вывод синхронизации, проверки lock-файла и приложения сохраните в `sync.txt`, `lock-check.txt`, `app-stdout.txt`; все ошибки — в `errors.txt`.
