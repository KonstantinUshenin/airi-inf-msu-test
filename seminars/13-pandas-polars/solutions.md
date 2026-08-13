# Примеры решений

Все решения запускаются из каталога, где лежит `data/`, созданный
`python3 assets/make_data.py`. Каждый фрагмент самодостаточен: строку
`import pandas as pd` и чтение нужных файлов повторяем, чтобы решение можно было
скопировать целиком.

Проверено на pandas 3.0.5 и polars 1.43.2.

## База

### B1

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
print(runs.shape)
print(runs.dtypes)
print(runs.head(3))
```

`batch_size` — целые числа без пропусков, поэтому `int64`. `val_acc` дробный, да
ещё и с пропусками: `NaN` — значение типа `float`, целочисленный столбец его
хранить не умеет. Текстовые столбцы в pandas 3 получают тип `str` (в pandas 2 на
их месте был бы `object`).

### B2

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
print(runs.describe())
```

`count` — число непропущенных значений. У `val_acc` он равен `12.000000` при 14
строках: два запуска (`r06` и `r14`) до метрики не доехали. Средние по `lr`,
`batch_size` и `epochs` смысла не имеют — это категории, записанные числами.

### B3

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
mask = (runs["dataset"] == "cifar10") & (runs["val_acc"] > 0.9)
print(runs.loc[mask, ["run_id", "model", "val_acc"]])
print(runs.loc[mask, "run_id"].tolist())
```

Каждое условие обязательно в скобках: у `&` приоритет выше, чем у `>`. Питоновский
`and` здесь не работает — он требует одного `True`/`False`, а не массива.

### B4

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
print(runs.isna().sum())
print(runs.loc[runs["val_acc"].isna(), "run_id"].tolist())
print(runs.loc[runs["gpu"].isna(), "run_id"].tolist())
```

Ноль в `val_acc` означал бы «модель не угадала ни разу», а у нас метрики просто
нет: запуск `r06` разошёлся, `r14` упал по памяти. Подставив ноль, мы занизим
среднее по всем моделям и сделаем вид, что данные есть.

### B5

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
top = runs.sort_values("val_acc", ascending=False).head(3)
print(top[["run_id", "model", "val_acc"]])
```

Индекс слева сохранил метки исходной таблицы (`7`, `6`, `3`) — сортировка строки
не перенумеровывает. Тот же результат даёт `runs.nlargest(3, "val_acc")`.

### B6

```python
import pandas as pd

notes = pd.read_csv("data/notes.csv", encoding="cp1251")
print(notes.shape)
print(notes.loc[notes["run_id"] == "r06", "comment"].iloc[0])
```

`.iloc[0]` берёт из отобранного `Series` первое значение по позиции — то же
самое умеет `.item()`, но он требует, чтобы значение было ровно одно.
Без `encoding="cp1251"` чтение упало бы с `UnicodeDecodeError` (кодировки —
семинар 10). Разобрать файл через `split(",")` нельзя: комментарии взяты в
кавычки и сами содержат запятые, так что `split` порезал бы строку в неверном
месте. `read_csv` правило экранирования знает.

### B7

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
by_id = runs.set_index("run_id")
print(by_id.shape)
print(by_id.loc["r05"])
print(by_id.loc[["r02", "r08"], "val_acc"].tolist())
```

`run_id` ушёл из столбцов в индекс, поэтому столбцов стало 9 вместо 10. Обращение
`.loc["r05"]` не зависит от порядка строк: после сортировки или фильтрации ключ
продолжит указывать на тот же запуск, а `.iloc[4]` — уже на какой-то другой.
Вернуть ключ в обычный столбец можно через `reset_index()`.

## Среднее

### M1

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
img = runs[runs["dataset"] == "imagenette"]
print(img.index.tolist())
print(img.iloc[0]["run_id"])
try:
    print(img.loc[0])
except KeyError as exc:
    print("KeyError:", exc)
```

`iloc` работает по позиции, `loc` — по метке индекса. После фильтрации метки
остались от исходной таблицы (`[8, 9, 10, 12, 13]`), а строки с меткой `0` среди
них нет: `r01` считался на `cifar10`. Нужны позиции с нуля — `reset_index(drop=True)`.

### M2

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
bad = runs.copy()
bad[bad["gpu"].isna()]["gpu"] = "unknown"      # ChainedAssignmentError, эффекта нет
print(bad["gpu"].value_counts(dropna=False))
fixed = runs.copy()
fixed.loc[fixed["gpu"].isna(), "gpu"] = "unknown"
print(fixed["gpu"].value_counts(dropna=False))
```

`bad[маска]` — это временная копия отобранных строк: запись меняет её, а не
таблицу, после чего копия исчезает. В `.loc[маска, "gpu"]` отбор строк и выбор
столбца происходят в одном обращении, поэтому pandas пишет в саму таблицу. То же
самое без маски: `fixed["gpu"] = fixed["gpu"].fillna("unknown")`.

### M3

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
report = runs.groupby("model").agg(
    n=("run_id", "size"),
    scored=("val_acc", "count"),
    mean_acc=("val_acc", "mean"),
    best_acc=("val_acc", "max"),
    total_min=("train_min", "sum"),
).round(4)
print(report)
```

`size` считает строки группы, `count` — непропущенные значения `val_acc`. У
`resnet50` и `vit_small` они различаются: по одному запуску в каждой группе
завершилось без метрики. Среднее считается по `scored`, а не по `n`.

### M4

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
print(runs.groupby("dataset")["val_acc"].mean().round(4))
print(runs.groupby(["dataset", "model"])["val_acc"].mean().round(4))
```

`imagenette` сложнее: средняя точность `0.8212` против `0.8979` на `cifar10`.
Список столбцов в `groupby` даёт составной ключ; результат — `Series` с
двухуровневым индексом.

### M5

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
models = pd.read_csv("data/models.csv")
joined = runs.merge(models, on="model", how="left")
print(joined.shape)
print(joined["family"].isna().sum())
print(joined.loc[joined["family"].isna(), "run_id"].tolist())
print(joined.groupby("family")["val_acc"].agg(["count", "mean"]).round(4))
```

`how="left"` сохраняет все строки левой таблицы: 14 запусков остались на месте, а
`mobilenet_v3`, которого нет в справочнике, получил `NaN` в новых столбцах.
`how="inner"` выкинул бы эти два запуска молча. Обратите внимание, что
`groupby("family")` их всё равно не считает — строки с пропуском в ключе
группировки отбрасываются (вернуть их можно через `dropna=False`).

### M6

```python
import pandas as pd

epochs = pd.read_csv("data/epochs.csv")
report = epochs.groupby("run_id").agg(
    n_epochs=("epoch", "size"),
    min_loss=("train_loss", "min"),
    best_acc=("val_acc", "max"),
)
print(report)
```

Это «длинная» таблица: одна строка — одна эпоха одного запуска. Группировка по
`run_id` сворачивает её в одну строку на запуск.

### M7

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
runs.to_parquet("data/runs.parquet")
back = pd.read_parquet("data/runs.parquet")
print(back.shape, back.dtypes.equals(runs.dtypes))
two = pd.read_parquet("data/runs.parquet", columns=["run_id", "val_acc"])
print(two.shape)
```

Parquet хранит схему рядом с данными, поэтому типы после round-trip те же, а не
угаданные заново, как при чтении csv. И он колоночный: значения каждого столбца
лежат в файле отдельным куском, так что `columns=[...]` читает ровно два куска и
не трогает остальные восемь. В csv строка файла — это строка таблицы, и чтобы
добраться до второго столбца, придётся разобрать все.

## Сложное

### H1

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
models = pd.read_csv("data/models.csv")
joined = runs.merge(models, on="model", how="left")
joined["family"] = joined["family"].fillna("unknown")
report = joined.groupby(["dataset", "family"]).agg(
    n=("run_id", "size"),
    mean_acc=("val_acc", "mean"),
    total_min=("train_min", "sum"),
).round(4).reset_index()
print(report)
```

Ключевая строка — `fillna("unknown")` до группировки: без неё запуски
`mobilenet_v3` исчезли бы из отчёта, потому что `groupby` выбрасывает строки с
пропуском в ключе. Альтернатива — `groupby(..., dropna=False)`, но тогда в отчёте
останется группа с именем `NaN`, которую неудобно печатать. `reset_index()`
превращает составной ключ обратно в обычные столбцы.

### H2

```python
import pandas as pd

epochs = pd.read_csv("data/epochs.csv")
runs = pd.read_csv("data/runs.csv")
best = epochs.loc[epochs.groupby("run_id")["val_acc"].idxmax()]
best = best[["run_id", "epoch", "val_acc"]]
check = best.merge(runs[["run_id", "val_acc"]], on="run_id", suffixes=("_epoch", "_final"))
check["same"] = check["val_acc_epoch"] == check["val_acc_final"]
print(check)
```

`idxmax` внутри группы возвращает **метку строки** с максимумом, а `loc` по этим
меткам достаёт целые строки — так вместе с максимумом сохраняется номер эпохи.
У `r01` и `r04` лучшая эпоха четвёртая, а не последняя: под конец точность
просела. `suffixes` разводит два одноимённых столбца `val_acc` после `merge`.

### H3

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
per_lr = runs.groupby(["model", "lr"])["val_acc"].mean().reset_index()
per_lr = per_lr.dropna(subset=["val_acc"])
per_lr = per_lr.sort_values(["model", "val_acc"], ascending=[True, False])
print(per_lr)
print(per_lr.groupby("model").head(1))
```

`dropna(subset=["val_acc"])` убирает пару `resnet50` + `lr=0.1`: единственный
запуск с таким сочетанием разошёлся, среднее по нему — `NaN`. Приём «отсортировать
и взять `head(1)` в каждой группе» даёт лучшую строку группы целиком, а не только
значение максимума.

### H4

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
total = runs["train_min"].sum()
failed = runs[runs["status"] != "ok"]
wasted = failed["train_min"].sum()
print(total, wasted, round(100 * wasted / total, 2))
print(failed[["run_id", "status", "train_min"]])
```

Считать долю через `runs["val_acc"].isna()` тоже можно — здесь это те же две
строки. Но опираться лучше на `status`: пропуск метрики и явный статус ошибки —
разные признаки, и в реальной выгрузке они совпадают не всегда.

### H5

```python
import pandas as pd

runs = pd.read_csv("data/runs.csv")
notes = pd.read_csv("data/notes.csv", encoding="cp1251")
joined = runs.merge(notes, on="run_id", how="left", indicator=True)
print(joined["_merge"].value_counts())
print(joined.loc[joined["comment"].notna(), ["run_id", "status", "comment"]])
```

`indicator=True` добавляет служебный столбец `_merge` со значениями `left_only`,
`right_only`, `both` — это самый быстрый способ проверить склейку: `right_only 0`
означает, что все комментарии нашли свой запуск. Комментарии есть у обоих
неудачных запусков (`r06`, `r14`), у лучшего (`r08`) и у запуска без имени GPU
(`r11`).

### H6

```python
import polars as pl

q = (pl.scan_csv("data/runs.csv")
     .filter(pl.col("status") == "ok")
     .group_by("model")
     .agg(pl.len().alias("n"), pl.col("val_acc").mean().round(4).alias("mean_acc"))
     .sort("mean_acc", descending=True))
print(q.explain())
print(q.collect())
```

`scan_csv` файл не читает — он строит план, и данные поедут только на `collect`.
В плане видно, что оптимизатор перенёс работу внутрь чтения: `PROJECT 3/10
COLUMNS` — из десяти столбцов будут прочитаны три (`model`, `val_acc`, `status`),
`SELECTION: col("status") == "ok"` — фильтр применяется прямо при чтении, так что
неудачные запуски в память не попадут. На файле в 14 строк это незаметно, на
многогигабайтном — принципиально.
