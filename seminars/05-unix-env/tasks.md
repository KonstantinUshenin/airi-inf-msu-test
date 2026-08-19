# Практическая работа

**Выход:** `.sh` или `.ipynb`.

Все задачи выполняются **на своей виртуальной машине, в домашнем каталоге** — например, в
`~/seminar-05/`. Каталог `/tmp` не используем: он вычищается при перезагрузке, а окружения, проекты
и отчёты нужны вам до защиты. Файлы-результаты (`paths.txt`, `report/` и прочие) складывайте в
каталог задачи.

Задачи разбиты на три уровня. Базовые — обязательный минимум, по ним отмечают, кто их решил.
Список с запасом: преподаватель выбирает, что давать.

## База

### B1. PATH

**need:** Linux.

Сохраните значение `PATH`, путь к текущему Python и путь к вашей оболочке в `paths.txt`.

**Пример:** `cat paths.txt` → три строки, первая вида `/usr/local/bin:/usr/bin:/bin`, вторая —
`/usr/bin/python3`, третья — `/bin/bash`.

### B2. Переменная окружения

**need:** нет.

Создайте `COURSE_LEVEL`. Сохраните её видимость в текущей и дочерней оболочке до и после экспорта.

**Пример:** `cat course-level.txt` → `current=basic`, `child-before=missing`, `child-after=basic`.

### B3. Source

**need:** нет.

Создайте файл `course.env` с двумя переменными — `COURSE_NAME` (без `export`) и `COURSE_DATA` (с
`export`). Подключите его к текущей оболочке и сохраните полученные значения в `environment.txt`.

**Пример:** для `COURSE_NAME='course-app'` и `export COURSE_DATA="$HOME/seminar-05/data"` файл
`environment.txt` содержит `course-app` и `/home/student/seminar-05/data`.

### B4. Virtual environment

**need:** `uv`; доступ к Python 3.12.

Создайте `.venv` на Python 3.12 через uv. Сохраните вывод `uv python find 3.12` до активации, путь и
версию интерпретатора внутри активированного окружения и вывод `uv python find 3.12` после
деактивации.

**Пример:** `cat inside.txt` → `~/seminar-05/b4/.venv/bin/python` и `Python 3.12.3`; в `before.txt`
и `after.txt` — путь вне окружения, и он одинаковый.

### B5. Зависимости Python

**need:** `uv`; доступ к пакету `requests`.

Создайте uv-проект и добавьте `requests`. Сохраните версии Python и `requests` в `versions.txt`,
дерево зависимостей — в `dependency-tree.txt`, а список появившихся файлов описания проекта
(`pyproject.toml`, `uv.lock`) — в `project-files.txt`.

**Пример:** `cat versions.txt` → `Python 3.12.3` и версия вида `2.32.3`; в `dependency-tree.txt`
под строкой `requests` перечислены `certifi`, `charset-normalizer`, `idna`, `urllib3`.

### B6. Какой файл запустится

**need:** Linux.

Положите в `~/seminar-05/b6/bin` исполняемый скрипт `course-info`, печатающий одну строку. Не меняя
`PATH`, покажите, что по имени команда не находится; затем добавьте каталог в начало `PATH` и
покажите, какой именно файл теперь выбирается и что он печатает.

**Пример:** `cat lookup.txt` → сначала строка вида `course-info: not found`, затем
`/home/student/seminar-05/b6/bin/course-info` и вывод самого скрипта.

## Среднее

### M1. Системные пакеты

**need:** Debian или Ubuntu с актуальным индексом APT.

Сохраните установленные системные пакеты в `installed-packages.txt`, доступные обновления — в
`upgradable-packages.txt`, ошибки — в `apt-errors.txt`. В файлах должны быть только пакеты:
служебную строку `Listing...` уберите, как в демке.

**Пример:** `head -1 installed-packages.txt` → строка вида
`adduser/noble,noble,now 3.137ubuntu1 all [installed,automatic]`; `wc -l < installed-packages.txt` →
число порядка сотен.

### M2. PYTHONPATH

**need:** каталог `modules` с модулем `course_module.py`.

Сделайте модуль доступным Python через `PYTHONPATH`. Сохраните импортированное значение и путь
загруженного файла.

**Пример:** для `course_module.py` с `VALUE = 42` файл `import.txt` содержит `42` и
`/home/student/seminar-05/m2/modules/course_module.py`.

### M3. Восстановление uv-окружения

**need:** `uv`; каталог `project-source` с `pyproject.toml`, `uv.lock` и прямой зависимостью `requests`.

Создайте чистый каталог `project-restored`, перенесите в него проект **без каталога `.venv`** и
восстановите окружение одной командой. Сохраните версии Python и `requests`.

**Пример:** `diff restored-versions.txt ../project-source/versions.txt` → пусто: версии совпали,
хотя `.venv` не копировали.

### M4. Динамические библиотеки

**need:** Linux с `ldconfig`.

Сохраните первые двадцать строк кэша динамических библиотек, а также список библиотек, которые
нужны команде `/usr/bin/head`.

**Пример:** `head -1 libraries.txt` → строка вида `NNN libs found in cache '/etc/ld.so.cache'`;
в `head-libs.txt` есть строка с `libc.so.6 =>`.

### M5. Systemd

**need:** Linux с systemd.

Сохраните версию systemd, состояние одной системной службы, последние двадцать строк её журнала и
список загруженных системных служб.

**Пример:** `head -1 systemd.txt` → `systemd 255 (255.4-1ubuntu8.17)`; в `system-services.txt` есть
строка со словом `.service` и состоянием `running`.

### M6. Окружение из `requirements.txt`

**need:** Python 3 с модулем `venv` (пакет `python3-venv`); сеть.

Вам дали проект с единственным файлом `requirements.txt` (например, со строкой `requests==2.31.0`).
Создайте окружение **средствами самого Python** (`python3 -m venv`), поставьте в него зависимости из
файла и сохраните итоговый снимок установленных версий. Системный Python при этом трогать нельзя.

**Пример:** `cat installed-versions.txt` → строка `requests==2.31.0` присутствует; `which python`
внутри активированного окружения → `~/seminar-05/m6/.venv/bin/python`.

## Сложное

### H1. Две версии Python

**need:** `uv`; доступ к Python 3.11 и 3.12.

Создайте два независимых окружения на Python 3.11 и 3.12. Сохраните версии интерпретаторов в
`python-versions.txt`, а пути к ним — в `python-paths.txt`.

**Пример:** `cat python-versions.txt` → `Python 3.11.x` и `Python 3.12.x` — две разные версии из
двух разных каталогов.

### H2. Обновление зависимости

**need:** `uv`; доступ к пакету `requests`.

Создайте uv-проект с `requests==2.31.0`. Сохраните исходную версию и lock-файл, затем разрешите
более новую совместимую версию и обновите только `requests`. Сохраните новую версию и изменения
lock-файла.

**Пример:** `cat before.txt` → `2.31.0`, `cat after.txt` → версия больше 2.31.0,
`lock-changes.txt` — непустой diff со строкой `version = "2.31.0"`.

### H3. PATH и приоритет

**need:** два каталога с одноимённой командой разного содержания.

Получите разные результаты команды при разном порядке каталогов в `PATH`. Сохраните применённый
путь в каждом случае.

**Пример:** `cat first.txt` → `one` и путь `.../bin-one/course-info`; `cat second.txt` → `two` и
путь `.../bin-two/course-info`.

### H4. Диагностика службы

**need:** Linux с systemd; переменная `SERVICE_NAME` с именем системной службы.

Сохраните unit-файл службы, её состояние и последние сто строк журнала. Ошибки сохраните отдельно.

**Пример:** для `SERVICE_NAME=systemd-journald` в `service-unit.txt` первая строка — комментарий с
путём вида `# /usr/lib/systemd/system/systemd-journald.service`, в `service-status.txt` есть
`Active:`.

### H5. Диагностика окружения

**need:** Linux, `uv`.

Создайте отчёт с `PATH`, `PYTHONPATH`, `LD_LIBRARY_PATH`, версией uv, найденным Python, системными
пакетами, доступными обновлениями, динамическими библиотеками и состоянием systemd.

**Пример:** `head -3 report/environment.txt` → строки `PATH=…`, `PYTHONPATH=…`,
`LD_LIBRARY_PATH=…` (две последние могут быть пустыми — это нормальный ответ, а не ошибка).
