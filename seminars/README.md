# Семинары

Программа семинаров курса «Практикум на ЭВM. Компьютерные технологии программирования».

## Как устроен каталог семинара

Каждый готовый семинар лежит в `seminars/NN-slug/`, где `NN` — номер строки из
таблицы ниже с ведущим нулём, а `slug` — короткое имя темы через дефис
(например, `08-unix-ssh`). Пробелов в именах каталогов нет: путь не должен
требовать кавычек в командной строке.

| Файл | Что содержит |
|------|--------------|
| `demo.ipynb` | Микро-лекция: мотивация, короткая демка, вопросы для коммуникации |
| `tasks.md` | Формулировки задач по уровням (база / среднее / сложное) |
| `solutions.md` | Примеры решений, по одному на каждую задачу |
| `assets/` | Необязательный: данные и файлы, нужные задачам |

Микро-лекция называется `demo.ipynb`, а не `lecture.ipynb`: настоящие лекции
курса живут в `lectures/` и нумеруются отдельно. Подробнее — `CONTEXT.md`,
`.claude/skills/seminar-format/SKILL.md` и `docs/adr/0003-seminar-directory-naming.md`.

## План

Номер в колонке `#` совпадает с префиксом каталога; ссылка стоит там, где
семинар уже готов.

| # | Блок | Тема | Содержание | «Забив» | Ревью |
| --- | --- | --- | --- | --- | --- |
| 1 | сентябрь | Jupyter Notebook. Практика по визуализации | conda jupyter, colab, matplotlib, numpy, магии ноутбука %% | Dmitrii | Максим |
| [2](02-unix-files/) | сентябрь | Unix-terminal. Работа с файлами | (ssh, bash, Ctrl+X, Ctrl+Z, Ctrl-C, \|, >, >>, &1, &2) Env Vars, Job, top, htop, ps, nvidia-smi, uname, os release, cat, history, mkdir, cd,  chown, chmod, cp, mv, pwd, ... | Николай | Dmitrii |
| 3 | сентябрь | Unix-terminal. Работа с текстами | vim, nano, diff, ed, vimdiff, csv, head, tail, wc, grep, find, sort, uniq. Далее аналоги переписанные на Rust: uutils coreutils, ripgrep, xsv | Максим | Николай |
| 4 | сентябрь | Система контроля версий Git | git | Dmitrii | Максим |
| [5](05-unix-env/) | октябрь | Unix-terminal. Настройка окружения и установка пакетов | source, virtualenv, apt/snap, pip/uv/conda, export,  ldconfig -p, systemd services, PATH, LD_LIBRARY_PATH, PYTHONPATH | Николай | Dmitrii |
| 6 | октябрь | Unix-terminal. Работа с оборудованием | lsblk, lsusb, fdisk, lspci -v<br>mount, fdisk,<br>/proc/cpuinfo, /proc/meminfo,<br>nvidia-smi, nvtop,<br>argparse, subprocesses, fork? | Максим | Николай |
| 7 | октябрь | Unix-terminal. Работа с сетью | nc, scp, ifconfig, ufw, ports, netstat, ss, nslookup, dig, ping, whois, wget, curl | Dmitrii | Максим |
| [8](08-unix-ssh/) | октябрь | Unix-terminal. ssh | ssh, scp, rsync, ssh-keygen, tunneling | Николай | Dmitrii |
| 9 | ноябрь | Контейнеризация и облачные технологии | Docker, Docker compose,<br>aws cli, boto3 (и аналоги), s3cmd, terraform (в клауде он пока очень сырой, невозможно пользоваться)<br>Знакомство с cloud.ru | Максим | Николай |
| 10 | ноябрь | Python. Работа с текстами | Кодировки. Операции над строками. Практикум по glob, Практикум по regexp | Dmitrii | Максим |
| 11 | ноябрь | Python. Работа с json и XML | Чтение jsom, xml. XPath.<br>REST API requests.<br>Скрапинг интеренет страниц -- Beautiful soup | Николай | Dmitrii |
| 12 | ноябрь | SQL | Select *, SQLite, SQLAlchemy | Максим | Николай |
| 13 | декабрь | Pandas/Polars | pandas | Dmitrii | Максим |
| 14 | декабрь | Python. Работа с бинарными данными | Чтение npy, hdfs, pickle, tar. Практикум по numpy | Николай | Dmitrii |
| 15 | декабрь | Python. Работа с изображениями | load image, normalize image, crop, gamma-correction | Максим | Николай |
| 16 | декабрь | Python. Работа с аудио и видео | librosa, построение спектрограмм, torch audio, torchvision | Dmitrii | Максим |
