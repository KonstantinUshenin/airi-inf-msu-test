#!/usr/bin/env python3
"""Готовит каталог `data/` с учебной выгрузкой экспериментов для семинара 13.

    python3 assets/make_data.py               # создать ./data
    python3 assets/make_data.py ~/seminar-13  # создать ~/seminar-13/data

Содержимое фиксировано (никакой генерации случайных чисел): у всех студентов
одинаковые входные данные, поэтому тестовые примеры в `tasks.md` совпадают до
последней цифры. Скрипт можно запускать повторно — файлы перезаписываются.
Зависимостей нет: pandas для подготовки данных не нужен.

Что получается:

    data/runs.csv    — 14 запусков обучения: гиперпараметры и результат
    data/models.csv  — справочник моделей: семейство и число параметров
    data/epochs.csv  — метрики по эпохам для четырёх запусков
    data/notes.csv   — комментарии инженера, выгрузка в кодировке cp1251
"""

import sys
from pathlib import Path

# Итог запуска: val_acc пуст там, где обучение не доехало до конца
# (r06 разошёлся, r14 упал по памяти), gpu не записан у r11.
RUNS_CSV = """\
run_id,model,dataset,lr,batch_size,epochs,val_acc,train_min,gpu,status
r01,resnet18,cifar10,0.1,64,10,0.8720,12.5,a100,ok
r02,resnet18,cifar10,0.01,64,10,0.9010,12.8,a100,ok
r03,resnet18,cifar10,0.001,64,10,0.8840,13.0,a100,ok
r04,resnet50,cifar10,0.01,64,10,0.9150,31.2,a100,ok
r05,resnet50,cifar10,0.001,64,10,0.9080,30.9,a100,ok
r06,resnet50,cifar10,0.1,64,10,,29.7,a100,diverged
r07,vit_small,cifar10,0.001,128,10,0.9240,44.0,h100,ok
r08,vit_small,cifar10,0.0003,128,10,0.9310,43.5,h100,ok
r09,vit_small,imagenette,0.001,128,5,0.8600,88.0,h100,ok
r10,resnet18,imagenette,0.01,64,5,0.8150,25.0,a100,ok
r11,resnet50,imagenette,0.01,64,5,0.8390,60.0,,ok
r12,mobilenet_v3,cifar10,0.01,64,10,0.8480,8.0,a100,ok
r13,mobilenet_v3,imagenette,0.01,64,5,0.7710,16.0,a100,ok
r14,vit_small,imagenette,0.0003,128,5,,90.0,h100,oom
"""

# Справочник неполный: mobilenet_v3 в нём нет, зато есть efficientnet_b0,
# который ни разу не запускали. Так и бывает с чужими справочниками.
MODELS_CSV = """\
model,family,params_m
resnet18,cnn,11.7
resnet50,cnn,25.6
vit_small,transformer,22.0
efficientnet_b0,cnn,5.3
"""

# «Длинная» таблица: одна строка — одна эпоха одного запуска.
EPOCHS_CSV = """\
run_id,epoch,train_loss,val_acc
r01,1,1.9800,0.7200
r01,2,1.2400,0.8100
r01,3,0.8900,0.8500
r01,4,0.6700,0.8720
r01,5,0.6100,0.8650
r02,1,1.8500,0.7500
r02,2,1.1000,0.8400
r02,3,0.7600,0.8800
r02,4,0.5800,0.8950
r02,5,0.5100,0.9010
r04,1,2.1000,0.7000
r04,2,1.3000,0.8300
r04,3,0.8200,0.8900
r04,4,0.5500,0.9150
r04,5,0.4900,0.9100
r07,1,2.2500,0.6800
r07,2,1.4500,0.8000
r07,3,0.9500,0.8700
r07,4,0.6400,0.9100
r07,5,0.5200,0.9240
"""

# Выгрузка из старой системы: кодировка cp1251, запятые внутри значений.
NOTES_CSV = """\
run_id,comment
r06,"Разошлось на первой эпохе, lr слишком большой"
r08,"Лучший запуск недели, взяли в отчёт"
r11,"Имя GPU забыли записать"
r14,"Не хватило памяти, нужен batch_size поменьше"
"""


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".") / "data"
    root.mkdir(parents=True, exist_ok=True)

    (root / "runs.csv").write_text(RUNS_CSV, encoding="utf-8")
    (root / "models.csv").write_text(MODELS_CSV, encoding="utf-8")
    (root / "epochs.csv").write_text(EPOCHS_CSV, encoding="utf-8")
    (root / "notes.csv").write_text(NOTES_CSV, encoding="cp1251")

    print(f"готово: {root}")
    for path in sorted(root.iterdir()):
        print(f"  {path.name}: {path.stat().st_size} байт")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
