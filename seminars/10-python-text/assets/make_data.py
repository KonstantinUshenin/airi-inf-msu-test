#!/usr/bin/env python3
"""Готовит каталог `data/` с учебными файлами для задач семинара 10.

    python3 assets/make_data.py          # создать ./data
    python3 assets/make_data.py /tmp/s10 # создать /tmp/s10/data

Содержимое фиксировано: у всех студентов одинаковые входные данные, поэтому
тестовые примеры в `tasks.md` совпадают до последней цифры. Скрипт можно
запускать повторно — файлы перезаписываются.
"""

import sys
from pathlib import Path

TRAIN_LOG = """\
2026-11-03 12:00:01 INFO run started model=resnet18 batch_size=64
2026-11-03 12:04:12 INFO epoch=1 loss=0.7100 acc=0.6210
2026-11-03 12:08:45 WARNING nan detected in batch 17
2026-11-03 12:08:46 INFO epoch=2 loss=0.4213 acc=0.8104
2026-11-03 12:13:02 ERROR failed to save checkpoint
Traceback (most recent call last):
  File "train.py", line 88, in save
    torch.save(state, path)
OSError: No space left on device
2026-11-03 12:17:30 INFO epoch=3 loss=0.3390 acc=0.8620
2026-11-03 12:21:55 INFO epoch=4 loss=nan acc=0.1000
2026-11-03 12:26:11 INFO epoch=5 loss=0.3102 acc=0.8801
2026-11-03 12:30:00 INFO run finished user=ivanov token=s3cr3t-9f2a
"""

RUN_LOGS = {
    "run-01": "2026-11-01 09:00:00 INFO epoch=1 loss=0.9100 acc=0.5010\n"
              "2026-11-01 09:10:00 INFO epoch=2 loss=0.6400 acc=0.7002\n",
    "run-02": "2026-11-02 09:00:00 INFO epoch=1 loss=0.8800 acc=0.5300\n"
              "2026-11-02 09:10:00 INFO epoch=2 loss=0.2500 acc=0.9100\n",
    "run-03": "2026-11-03 09:00:00 INFO epoch=1 loss=0.7700 acc=0.5800\n"
              "2026-11-03 09:10:00 INFO epoch=2 loss=0.5100 acc=0.7600\n",
}

METRICS_CSV = "epoch,loss,acc\n1,0.9100,0.5010\n2,0.6400,0.7002\n"

FILE_NAMES = [
    "run-01_2026-11-01.csv",
    "run-02_2026-11-02.csv",
    "run-2_2026-11-03.csv",
    "run-04_03-11-2026.csv",
    "RUN-05_2026-11-05.csv",
    "run-06_2026-11-06.txt",
]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".") / "data"
    root.mkdir(parents=True, exist_ok=True)

    # Текст в однобайтовой кодировке cp1251 — как выгрузка из старой системы.
    (root / "report-cp1251.txt").write_text(
        "Отчёт по эксперименту\nМодель обучена\n", encoding="cp1251")

    # csv «из Excel»: те же данные, но с BOM в начале файла.
    (root / "excel-bom.csv").write_text(
        "epoch,loss\n1,0.7100\n2,0.4213\n", encoding="utf-8-sig")

    (root / "train.log").write_text(TRAIN_LOG, encoding="utf-8")

    # Дерево запусков: два свежих запуска и один в архиве.
    for name, body in RUN_LOGS.items():
        directory = root / "runs" / name if name != "run-03" else root / "runs" / "archive" / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "train.log").write_text(body, encoding="utf-8")
        (directory / "metrics.csv").write_text(METRICS_CSV, encoding="utf-8")
    (root / "runs" / "run-02" / "notes.txt").write_text(
        "смотреть глазами\n", encoding="utf-8")
    (root / "runs" / ".hidden.csv").write_text("epoch,loss\n", encoding="utf-8")

    # Имена файлов для проверки соглашения run-NN_YYYY-MM-DD.csv.
    names = root / "names"
    names.mkdir(exist_ok=True)
    for file_name in FILE_NAMES:
        (names / file_name).write_text("", encoding="utf-8")

    print(f"данные готовы: {root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
