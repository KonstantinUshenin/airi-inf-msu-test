# Примеры решений

Все решения запускаются из каталога, где лежит `data/`, созданный
`python3 assets/make_data.py`.

## База

### B1

```python
text = "Отчёт готов"
print(len(text))
print(len(text.encode("utf-8")))
print(len(text.encode("cp1251")))
```

В utf-8 кириллическая буква занимает два байта, поэтому 10 букв дают 20 байт
плюс байт пробела. В однобайтовой cp1251 число байт совпадает с числом символов.

### B2

```python
text = "Модель обучена"
broken = text.encode("utf-8").decode("cp1251")
print(broken)
print(broken.encode("cp1251").decode("utf-8"))
```

Восстановление работает потому, что при чтении cp1251 ни один байт не потерялся:
каждому байту нашёлся символ. Если бы вместо этого использовался
`errors="ignore"`, вернуть исходный текст было бы уже нельзя.

### B3

```python
from pathlib import Path

path = Path("data/report-cp1251.txt")
try:
    path.read_text(encoding="utf-8")
except UnicodeDecodeError as exc:
    print(exc)
print(path.read_text(encoding="utf-8", errors="replace").splitlines()[0])
print(path.read_text(encoding="cp1251").splitlines()[0])
```

### B4

```python
line = "2026-11-03 12:04:12 INFO epoch=1 loss=0.7100 acc=0.6210"
date, time, level, *pairs = line.split()
values = {}
for pair in pairs:
    key, _, value = pair.partition("=")
    values[key] = value
print(date, level, values)
```

Распаковка со звёздочкой отделяет три фиксированных поля от переменного числа
пар; `partition` разбивает пару ровно на две части даже без знака `=`.

### B5

```python
from pathlib import Path

runs = Path("data/runs")
found = sorted(runs.rglob("metrics.csv"))
print(len(found))
for path in found:
    print(path.relative_to(runs))
```

### B6

```python
import re

line = "2026-11-03 12:04:12 INFO epoch=1 loss=0.7100 acc=0.6210"
print(re.findall(r"\d+\.\d+", line))
```

Дата и время не совпадают с шаблоном: в них разделителями служат дефис и
двоеточие, а не точка.

## Среднее

### M1

```python
from pathlib import Path

path = Path("data/excel-bom.csv")
print(repr(path.read_text(encoding="utf-8").split(",")[0]))
print(repr(path.read_text(encoding="utf-8-sig").split(",")[0]))
```

Верен `utf-8-sig`: он снимает BOM. При чтении как `utf-8` в начало имени колонки
попадает невидимый символ `﻿`, и обращение по имени `epoch` не работает.

### M2

```python
from pathlib import Path

names = sorted(Path("data/names").glob("*.csv"))
for path in names:
    print(path.name, "->", path.name.removesuffix(".csv").lower().replace("-", "_"))
print("обработано:", len(names))
print("metrics.csv".strip(".csv"), "vs", "metrics.csv".removesuffix(".csv"))
```

`strip(".csv")` даёт `metri`: он снимает с концов любые символы из набора
`{'.', 'c', 's', 'v'}`, а не суффикс целиком.

### M3

```python
from pathlib import Path

rows = []
for path in Path("data/runs").rglob("train.log"):
    lines = path.read_text(encoding="utf-8").splitlines()
    rows.append((path.parent.name, len(lines)))
for name, count in sorted(rows):
    print(name, count)
```

### M4

```python
import re
from pathlib import Path

row_re = re.compile(
    r"(?P<time>\S+ \S+) (?P<level>\w+) "
    r"epoch=(?P<epoch>\d+) loss=(?P<loss>[\d.]+) acc=(?P<acc>[\d.]+)")
found = []
for raw in Path("data/train.log").read_text(encoding="utf-8").splitlines():
    match = row_re.search(raw)
    if match:
        found.append(match.groupdict())
print("распознано:", len(found))
print(found[0])
```

Распознано 4 строки из 5 с `epoch=`: строка с `loss=nan` не подходит под
`[\d.]+`. Это нормальный результат, но о нём нужно знать — отсюда требование
считать нераспознанные строки в H1.

### M5

```python
import re
from pathlib import Path

text = Path("data/train.log").read_text(encoding="utf-8")
safe = re.sub(r"(user|token)=\S+", r"\1=***", text)
Path("data/train-safe.log").write_text(safe, encoding="utf-8")
print(safe.splitlines()[-1])
```

Группа `(user|token)` возвращается в замену через `\1`, поэтому имя поля
сохраняется, а значение заменяется.

### M6

```python
import re
from collections import Counter
from pathlib import Path

text = Path("data/train.log").read_text(encoding="utf-8")
levels = re.findall(r"^\S+ \S+ (INFO|WARNING|ERROR)\b", text, re.MULTILINE)
for level, count in Counter(levels).most_common():
    print(level, count)
```

`re.MULTILINE` заставляет `^` совпадать с началом каждой строки. Привязка к
началу нужна, чтобы слово `ERROR` внутри текста сообщения не считалось уровнем.

## Сложное

### H1

```python
import re
from pathlib import Path

row_re = re.compile(r"epoch=(\d+) loss=([\d.]+) acc=([\d.]+)")
rows = []
skipped = []
for raw in Path("data/train.log").read_text(encoding="utf-8").splitlines():
    match = row_re.search(raw)
    if match:
        rows.append(",".join(match.groups()))
    else:
        skipped.append(raw)

table = "\n".join(["epoch,loss,acc"] + rows) + "\n"
Path("data/metrics.csv").write_text(table, encoding="utf-8")

print("строк данных:", len(rows))
print("нераспознано:", len(skipped))
print(skipped[0])
```

Файл собран из строк методом `join`, потому что значения простые и запятых
внутри них нет. Как только в поле может появиться запятая или перевод строки,
собирать csv руками нельзя — нужен модуль `csv`, который расставит кавычки.

### H2

```python
import re
from pathlib import Path

records = []
for raw in Path("data/train.log").read_text(encoding="utf-8").splitlines():
    if re.match(r"\d{4}-\d{2}-\d{2} ", raw) or not records:
        records.append([raw])
    else:
        records[-1].append(raw)

print("записей:", len(records))
for record in records:
    if " ERROR " in record[0]:
        print("строк в записи:", len(record))
        print("\n".join(record))
```

Признак новой записи — дата в начале строки, поэтому используется `re.match`, а
не `re.search`. Условие `not records` защищает от файла, который начинается со
строки продолжения.

### H3

```python
from pathlib import Path


def read_text_guess(path):
    for encoding in ("utf-8", "cp1251"):
        try:
            return encoding, Path(path).read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"ни одна кодировка не подошла: {path}")


for name in ("data/report-cp1251.txt", "data/train.log"):
    encoding, text = read_text_guess(name)
    print(name, encoding, text.splitlines()[0])
```

Порядок важен: `utf-8` проверяется первой, потому что она единственная из двух
падает на чужих данных. Отличить `cp1251` от `koi8-r` тем же приёмом нельзя:
обе однобайтовые, в них допустим любой байт, поэтому `decode` не выбросит
исключение ни в одной — различие видно только по осмысленности текста, а для
этого нужны частотные эвристики или библиотека вроде `chardet`.

### H4

```python
import re
from pathlib import Path

loss_re = re.compile(r"loss=([\d.]+)")
best = {}
for path in Path("data/runs").rglob("train.log"):
    values = [float(x) for x in loss_re.findall(path.read_text(encoding="utf-8"))]
    if values:
        best[path.parent.name] = min(values)

for name, value in sorted(best.items(), key=lambda item: item[1]):
    print(f"{name} — {value:.4f}")
print("лучший:", min(best, key=best.get))
```

### H5

```python
import re
from pathlib import Path

name_re = re.compile(r"run-\d{2}_\d{4}-\d{2}-\d{2}\.csv")
good = []
bad = []
for path in sorted(Path("data/names").iterdir()):
    if name_re.fullmatch(path.name):
        good.append(path.name)
    else:
        bad.append(path.name)
print("подходят:", good)
print("нарушители:", bad)
```

`fullmatch` требует совпадения всей строки, поэтому `run-06_2026-11-06.txt`
отсеивается по расширению, а `RUN-05_2026-11-05.csv` — по регистру. С `search`
такой проверки не получится: он найдёт подходящий кусок внутри неподходящего
имени.

### H6

```python
import re

line = 'model="resnet 18" batch_size=64 note="loss=nan on 17"'
pair_re = re.compile(r'(\w+)=(?:"([^"]*)"|(\S+))')
values = {}
for key, quoted, plain in pair_re.findall(line):
    values[key] = quoted if quoted else plain
print(values)
```

Альтернатива в скобках сначала пробует вариант в кавычках, поэтому пробелы и
знак `=` внутри значения не ломают разбор. Группа `(?:...)` не захватывающая:
она нужна только для группировки альтернатив и не попадает в результат
`findall`. Класс `[^"]*` не даёт значению «перепрыгнуть» через закрывающую
кавычку.
