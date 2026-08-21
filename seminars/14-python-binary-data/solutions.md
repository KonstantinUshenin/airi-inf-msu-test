# Примеры решений

## База

### B1

```python
import json
import numpy as np

array = np.arange(24, dtype=np.float32).reshape(4, 6)
info = {
    "shape": list(array.shape),
    "ndim": array.ndim,
    "dtype": str(array.dtype),
    "size": array.size,
    "nbytes": array.nbytes,
}

with open("array-info.json", "w", encoding="utf-8") as file:
    json.dump(info, file, ensure_ascii=False, indent=2)
```

### B2

```python
import numpy as np

matrix = np.load("assets/B2/matrix.npy", allow_pickle=False)
np.savez_compressed(
    "slices.npz",
    second_row=matrix[1],
    third_column=matrix[:, 2],
    block=matrix[2:5, 3:7],
    reversed_rows=matrix[::-1],
)
```

### B3

```python
import numpy as np

data = np.load("assets/B3/measurements.npy", allow_pickle=False)
np.savez_compressed(
    "statistics.npz",
    mean=data.mean(axis=0),
    std=data.std(axis=0),
    minimum=data.min(axis=0),
    maximum=data.max(axis=0),
    median=np.median(data, axis=0),
    row_argmax=data.argmax(axis=1),
)
```

### B4

```python
import json
import numpy as np

first = np.random.default_rng(42).normal(size=100)
same = np.random.default_rng(42).normal(size=100)
different = np.random.default_rng(43).normal(size=100)

np.save("sample.npy", first)
report = {
    "same_seed_equal": bool(np.array_equal(first, same)),
    "different_seed_equal": bool(np.array_equal(first, different)),
}
with open("determinism.json", "w", encoding="utf-8") as file:
    json.dump(report, file, ensure_ascii=False, indent=2)
```

### B5

```python
import numpy as np

rng = np.random.default_rng(42)
first = rng.normal(size=(10, 2))
second = rng.normal(size=(8, 4))

all_values = np.concatenate([first.ravel(), second.ravel()])
combined = all_values.reshape(13, 4)

np.savez_compressed(
    "reshape-result.npz",
    first=first,
    second=second,
    combined=combined,
)
```

### B6

```python
import json
import h5py
import numpy as np

values = np.arange(60, dtype=np.float32).reshape(20, 3)

with h5py.File("experiment.h5", "w") as file:
    experiment = file.create_group("experiment")
    dataset = experiment.create_dataset("values", data=values)
    dataset.attrs["units"] = "mV"
    file.attrs["description"] = "Учебные измерения"

with h5py.File("experiment.h5", "r") as file:
    dataset = file["experiment/values"]
    info = {
        "name": dataset.name,
        "shape": list(dataset.shape),
        "dtype": str(dataset.dtype),
        "units": dataset.attrs["units"],
        "rows_10_12": dataset[10:13].tolist(),
    }

with open("hdf5-info.json", "w", encoding="utf-8") as file:
    json.dump(info, file, ensure_ascii=False, indent=2)
```

### B7

```python
import json
import pickle
import numpy as np

state = {
    "values": np.arange(10, dtype=np.float32).reshape(5, 2),
    "columns": ["left", "right"],
    "rows": 5,
}

with open("state.pkl", "wb") as file:
    pickle.dump(state, file)

with open("state.pkl", "rb") as file:
    restored = pickle.load(file)

report = {
    "keys": list(restored.keys()),
    "shape": list(restored["values"].shape),
    "dtype": str(restored["values"].dtype),
    "equal": bool(np.array_equal(state["values"], restored["values"])),
}
with open("pickle-report.json", "w", encoding="utf-8") as file:
    json.dump(report, file, ensure_ascii=False, indent=2)
```

## Среднее

### M1

```python
import numpy as np

data = np.load("assets/M1/sensors.npy", allow_pickle=False)
mean = data.mean(axis=0)
std = data.std(axis=0)
normalized = (data - mean) / std
anomaly_rows, anomaly_columns = np.where(np.abs(normalized) > 2)

np.savez_compressed(
    "normalized.npz",
    data=data,
    mean=mean,
    std=std,
    normalized=normalized,
    anomaly_rows=anomaly_rows,
    anomaly_columns=anomaly_columns,
)
```

### M2

```python
import json
import numpy as np

data = np.load("assets/M2/temperatures.npy", allow_pickle=False)

np.savez_compressed(
    "temperature-summary.npz",
    mean=data.mean(axis=0),
    std=data.std(axis=0),
    minimum=data.min(axis=0),
    maximum=data.max(axis=0),
)

flat_index = int(data.argmax())
day, station = np.unravel_index(flat_index, data.shape)
hottest = {
    "day": int(day),
    "station": int(station),
    "temperature": float(data[day, station]),
}
with open("hottest.json", "w", encoding="utf-8") as file:
    json.dump(hottest, file, ensure_ascii=False, indent=2)
```

### M3

```python
import numpy as np

raw = np.load("assets/M3/raw.npy", allow_pickle=False)
calibration = np.load("assets/M3/calibration.npy", allow_pickle=False)

calibrated = raw @ calibration
np.savez_compressed(
    "calibrated.npz",
    calibrated=calibrated,
    mean=calibrated.mean(axis=0),
    std=calibrated.std(axis=0),
    row_argmax=calibrated.argmax(axis=1),
)
```

### M4

```python
import numpy as np

part1 = np.load("assets/M4/part1.npy", allow_pickle=False)
part2 = np.load("assets/M4/part2.npy", allow_pickle=False)
part3 = np.load("assets/M4/part3.npy", allow_pickle=False)

combined = np.concatenate([part1, part2, part3], axis=0)
mean = combined.mean(axis=0)
std = combined.std(axis=0)
normalized = (combined - mean) / std

np.savez_compressed(
    "combined.npz",
    part1=part1,
    part2=part2,
    part3=part3,
    combined=combined,
    mean=mean,
    std=std,
    normalized=normalized,
)
```

### M5

```python
import json
import io
import tarfile
import numpy as np

with tarfile.open("assets/M5/dataset.tar.gz", "r:*") as archive:
    with archive.extractfile("dataset/features.npy") as file:
        features = np.load(io.BytesIO(file.read()), allow_pickle=False)
    with archive.extractfile("dataset/labels.npy") as file:
        labels = np.load(io.BytesIO(file.read()), allow_pickle=False)
    with archive.extractfile("dataset/metadata.json") as file:
        metadata = json.load(file)

class0 = features[labels == 0]
class1 = features[labels == 1]

np.savez_compressed(
    "class-statistics.npz",
    class0_mean=class0.mean(axis=0),
    class0_std=class0.std(axis=0),
    class1_mean=class1.mean(axis=0),
    class1_std=class1.std(axis=0),
)

info = {
    "shape": list(features.shape),
    "dtype": str(features.dtype),
    "class0_count": int(class0.shape[0]),
    "class1_count": int(class1.shape[0]),
    "metadata": metadata,
}
with open("archive-info.json", "w", encoding="utf-8") as file:
    json.dump(info, file, ensure_ascii=False, indent=2)
```

### M6

```python
import io
import json
import tarfile
import numpy as np

with tarfile.open("assets/M6/dataset.tar.gz", "r:*") as archive:
    with archive.extractfile("dataset/train.npy") as file:
        train = np.load(io.BytesIO(file.read()), allow_pickle=False)
    with archive.extractfile("dataset/test.npy") as file:
        test = np.load(io.BytesIO(file.read()), allow_pickle=False)
    with archive.extractfile("dataset/metadata.json") as file:
        metadata = json.load(file)

mean = train.mean(axis=0)
std = train.std(axis=0)

train_normalized = (train - mean) / std
test_normalized = (test - mean) / std

np.savez_compressed(
    "split-normalized.npz",
    train=train,
    test=test,
    mean=mean,
    std=std,
    train_normalized=train_normalized,
    test_normalized=test_normalized,
)

report = {
    "columns": metadata["columns"],
    "train_shape": list(train.shape),
    "test_shape": list(test.shape),
    "test_mean_after": test_normalized.mean(axis=0).tolist(),
}
with open("split-report.json", "w", encoding="utf-8") as file:
    json.dump(report, file, ensure_ascii=False, indent=2)
```

## Сложное

### H1

```python
import json
import tarfile
import numpy as np

with tarfile.open("assets/H1/temperatures.tar.gz", "r:*") as archive:
    with archive.extractfile("weather/temperatures.json") as file:
        values = json.load(file)

temperatures = np.asarray(values, dtype=np.float64)
np.save("temperatures.npy", temperatures)

report = {
    "days": int(temperatures.size),
    "mean": float(temperatures.mean()),
    "std": float(temperatures.std()),
    "median": float(np.median(temperatures)),
    "minimum": float(temperatures.min()),
    "maximum": float(temperatures.max()),
    "hottest_day": int(temperatures.argmax()),
}
with open("temperature-report.json", "w", encoding="utf-8") as file:
    json.dump(report, file, ensure_ascii=False, indent=2)
```

### H2

```python
import json
import tarfile
import numpy as np

with tarfile.open("assets/H2/weather.tar.gz", "r:*") as archive:
    with archive.extractfile("weather/records.json") as file:
        records = json.load(file)

dates = [record["date"] for record in records]
data = np.asarray(
    [
        [record["temperature"], record["humidity"], record["wind"]]
        for record in records
    ],
    dtype=np.float64,
)

mean = data.mean(axis=0)
std = data.std(axis=0)
np.savez_compressed(
    "weather.npz",
    data=data,
    mean=mean,
    std=std,
)

mask = (data[:, 0] > mean[0]) & (data[:, 1] < 60)
selected = []
for index in np.nonzero(mask)[0]:
    selected.append({
        "date": dates[index],
        "temperature": float(data[index, 0]),
        "humidity": float(data[index, 1]),
        "wind": float(data[index, 2]),
    })

with open("selected.json", "w", encoding="utf-8") as file:
    json.dump(selected, file, ensure_ascii=False, indent=2)
```

### H3

```python
import json
import tarfile
import numpy as np

names = [
    "batches/part1.json",
    "batches/part2.json",
    "batches/part3.json",
]
arrays = []
shapes = {}

with tarfile.open("assets/H3/batches.tar.gz", "r:*") as archive:
    for name in names:
        with archive.extractfile(name) as file:
            array = np.asarray(json.load(file), dtype=np.float64)
        if array.ndim != 2 or array.shape[1] != 4:
            raise ValueError(f"invalid shape in {name}: {array.shape}")
        arrays.append(array)
        shapes[name] = list(array.shape)

combined = np.concatenate(arrays, axis=0)
mean = combined.mean(axis=0)
std = combined.std(axis=0)
normalized = (combined - mean) / std

np.savez_compressed(
    "batches.npz",
    part1=arrays[0],
    part2=arrays[1],
    part3=arrays[2],
    combined=combined,
    mean=mean,
    std=std,
    normalized=normalized,
)
with open("batch-report.json", "w", encoding="utf-8") as file:
    json.dump({"shapes": shapes}, file, ensure_ascii=False, indent=2)
```

### H4

```python
import json
import tarfile
import numpy as np

with tarfile.open("assets/H4/stations.tar.gz", "r:*") as archive:
    with archive.extractfile("stations/records.json") as file:
        stations = json.load(file)

parts = []
station_ids = []
for station in stations:
    part = np.asarray(station["measurements"], dtype=np.float64)
    if part.ndim != 2 or part.shape[1] != 3:
        raise ValueError(f"invalid measurements for {station['id']}")
    parts.append(part)
    station_ids.extend([station["id"]] * part.shape[0])

data = np.concatenate(parts, axis=0)
station_ids = np.asarray(station_ids)

per_station = {}
for station in stations:
    station_data = data[station_ids == station["id"]]
    per_station[station["id"]] = {
        "count": int(station_data.shape[0]),
        "mean": station_data.mean(axis=0).tolist(),
        "std": station_data.std(axis=0).tolist(),
    }

np.savez_compressed(
    "stations.npz",
    data=data,
    station_ids=station_ids,
)
report = {
    "columns": ["temperature", "humidity", "pressure"],
    "global_mean": data.mean(axis=0).tolist(),
    "global_std": data.std(axis=0).tolist(),
    "stations": per_station,
}
with open("station-report.json", "w", encoding="utf-8") as file:
    json.dump(report, file, ensure_ascii=False, indent=2)
```

### H5

```python
import json
import tarfile
import numpy as np

with tarfile.open("assets/H5/experiment.tar.gz", "r:*") as archive:
    with archive.extractfile("experiment/manifest.json") as file:
        manifest = json.load(file)

    arrays = []
    shapes = {}
    for name in manifest["files"]:
        with archive.extractfile(name) as file:
            array = np.asarray(json.load(file), dtype=np.float64)
        if array.ndim != 2 or array.shape[1] != len(manifest["columns"]):
            raise ValueError(f"invalid shape in {name}: {array.shape}")
        arrays.append(array)
        shapes[name] = list(array.shape)

combined = np.concatenate(arrays, axis=0)
missing = np.isnan(combined)
mean = np.nanmean(combined, axis=0)

rows, columns = np.where(missing)
filled = combined.copy()
filled[rows, columns] = mean[columns]

std = filled.std(axis=0)
if np.any(std == 0):
    raise ValueError("constant column")

normalized = (filled - mean) / std
flat_index = int(np.abs(normalized).argmax())
max_row, max_column = np.unravel_index(flat_index, normalized.shape)

np.savez_compressed(
    "experiment.npz",
    filled=filled,
    normalized=normalized,
    mean=mean,
    std=std,
)

report = {
    "files": manifest["files"],
    "columns": manifest["columns"],
    "shapes": shapes,
    "filled_values": int(missing.sum()),
    "max_abs_coordinate": [int(max_row), int(max_column)],
    "value_at_coordinate": float(normalized[max_row, max_column]),
}
with open("experiment-report.json", "w", encoding="utf-8") as file:
    json.dump(report, file, ensure_ascii=False, indent=2)
```

### H6

```python
import json
import tarfile
import h5py
import numpy as np

with tarfile.open("assets/H6/dataset.tar.gz", "r:*") as archive:
    with archive.extractfile("dataset/manifest.json") as file:
        manifest = json.load(file)

    days = {}
    for number, name in enumerate(manifest["files"], 1):
        with archive.extractfile(name) as file:
            rows = json.load(file)
        # None превращается в NaN сам, если просить вещественный тип
        array = np.asarray(rows, dtype=np.float64)
        if array.ndim != 2 or array.shape[1] != len(manifest["columns"]):
            raise ValueError(f"invalid shape in {name}: {array.shape}")
        days[f"day{number}"] = (name, array)

combined = np.concatenate([array for _, array in days.values()], axis=0)

with h5py.File("days.h5", "w") as file:
    file.attrs["columns"] = manifest["columns"]
    for day, (name, array) in days.items():
        group = file.create_group(day)
        group.attrs["source"] = name
        group.create_dataset("values", data=array)
    file.create_dataset("combined", data=combined)

report = {
    "columns": manifest["columns"],
    "shapes": {day: list(array.shape) for day, (_, array) in days.items()},
    "missing_per_column": np.isnan(combined).sum(axis=0).tolist(),
    "column_mean": np.nanmean(combined, axis=0).tolist(),
}
with open("days-report.json", "w", encoding="utf-8") as file:
    json.dump(report, file, ensure_ascii=False, indent=2)
```
