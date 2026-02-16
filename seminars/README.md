# Семинары

## Основной язык программирования

`Python`, но допустимы вставки `C`

## Формат занятий

Семинары предполагают гибридный формат:

1) Сначала преподаватель семинаров знакомит с темой занятия (скорее напоминает, что бы ло на лекции). Показывает пример, как выполнить какую-то часть занятия.
2) Затем студенты должны сами воспроизвести результаты работы преподавателя по инструкции в формате лабораторной работы. Результаты должны фиксироваться в отчет. И артефакты работы должны сохраниться на диске (сами лабоработные работы будут проходить или в jupyter notebook или на удаленном сервере)
3) Для тех, кто справился быстро, есть возможность пройти дополнительные очень сложные, но интересные задания на дополнительные баллы.

## Защита семинаров:

- все студенты должны защитить семинаристам сделанные задания
- если студент не отвечает на вопрос из теор минимума, без которого нельзя было получить результаты работы, за работу ставится 0 баллов
- если студент не отвечает на **дополнительный** вопрос, балл может быть снижен

## Темы занятий

| № | Блок | Тема | Содержание |
|---|------|------|------------|
| 1 | сентябрь | Jupyter Notebook. Практика по визуализации | colab, matplotlib, numpy |
| 2 | сентябрь | Unix-terminal. Работа с файлами | (ssh, bash, Ctrl+X, Ctrl+Z, Ctrl-C, \|, >, >>, &1, &2) Env Vars, jobs, top, htop, ps, nvidia-smi, uname, os release, cat, history, mkdir, cd, chown, chmod, cp, mv, pwd, ... |
| 3 | сентябрь | Unix-terminal. Работа с текстами | vim, nano, diff, ed, vimdiff, csv, head, tail, wc, grep, find, sort, uniq. Далее аналоги переписанные на Rust: uutils coreutils, ripgrep, xsv |
| 4 | сентябрь | Система контроля версий Git | git |
| 5 | октябрь | Unix-terminal. Настройка окружения и установка пакетов | source, virtualenv, apt/snap, pip/uv/conda, export, ldconfig -p, services, PATH, LD_LIBRARY_PATH, PYTHONPATH |
| 6 | октябрь | Unix-terminal. Работа с оборудованием | lsblk, lsusb, fdisk, lspci -v, mount, fdisk, /proc/cpuinfo, /proc/meminfo, nvidia-smi, nvtop, argparse, subprocesses, fork, strace |
| 7 | октябрь | Unix-terminal. Работа с сетью | nc, scp, ifconfig, ufw, ports, netstat, ss, nslookup, dig, ping, whois, wget, curl |
| 8 | октябрь | Unix-terminal. ssh | ssh, scp, rsync, ssh-keygen |
| 9 | ноябрь | Контейнеризация и облачные технологии | Docker, Docker compose, aws cli, boto3 (и аналоги), Знакомство с cloud.ru |
| 10 | ноябрь | Python. Работа с текстами | Кодировки. Операции над строками. Практикум по glob, Практикум по regexp |
| 11 | ноябрь | Python. Работа с json и XML | Чтение json, xml. XPath. REST API requests. Скрапинг интернет страниц — Beautiful soup |
| 12 | ноябрь | SQL | Select *, SQLite, SQLAlchemy |
| 13 | декабрь | Pandas/Polars | pandas |
| 14 | декабрь | Python. Работа с бинарными данными | Чтение npy, hdfs, pickle, tar. Практикум по numpy |
| 15 | декабрь | Python. Работа с изображениями | load image, normalize image, crop, gamma-correction |
| 16 | декабрь | Python. Работа с аудио и видео | librosa, построение спектрограмм, torch audio, torchvision |
