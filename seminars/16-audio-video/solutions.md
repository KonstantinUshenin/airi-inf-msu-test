# Примеры решений

Все решения запускаются из каталога, где лежит `data/`, созданный
`python3 assets/make_data.py`.

## База

### B1

```python
import soundfile as sf

data, sr = sf.read("data/tone_440.wav")
print(sr, data.shape, len(data) / sr)
```

Длительность считается из данных: число сэмплов, делённое на частоту
дискретизации. Это единственный способ, который не врёт, — имя файла и его
размер о длительности ничего не гарантируют.

### B2

```python
import numpy as np
import soundfile as sf

data, sr = sf.read("data/stereo.wav")
print(data.shape, data.shape[1])
print(round(float(np.abs(data[:, 0]).max()), 4), round(float(np.abs(data[:, 1]).max()), 4))
mono = data.mean(axis=1)
print(mono.shape)
```

`soundfile` отдаёт стерео в форме `(сэмплы, каналы)`, поэтому канал выбирается
вторым индексом, а усреднение идёт по `axis=1`.

### B3

```python
import librosa

y_default, sr_default = librosa.load("data/tone_440.wav")
y_native, sr_native = librosa.load("data/tone_440.wav", sr=None)
print(sr_default, y_default.shape, len(y_default) / sr_default)
print(sr_native, y_native.shape, len(y_native) / sr_native)
```

По умолчанию `librosa.load` приводит запись к 22050 Гц, поэтому сэмплов вдвое
меньше. Длительность при этом не меняется: во столько же раз уменьшилось и
число сэмплов, и число сэмплов в секунде. `sr=None` оставляет файл как есть —
именно так стоит грузить, когда важна исходная частота.

### B4

```python
import librosa
import numpy as np

y, sr = librosa.load("data/quiet.wav", sr=None)
print(round(float(np.abs(y).max()), 4), round(float(np.sqrt(np.mean(y ** 2))), 4))
normalized = y / np.abs(y).max()
print(round(float(np.abs(normalized).max()), 4),
      round(float(np.sqrt(np.mean(normalized ** 2))), 4))
```

Нормализация по пику — это умножение всего сигнала на одно число, поэтому
отношение RMS к пику сохраняется: `0.0354 / 0.05` и `0.7068 / 1.0` — одна и та
же величина, примерно `1/√2` для синуса.

Именно «примерно»: у идеального синуса вышло бы `0.70711`, а получается
`0.70685`. Разница — след `PCM_16`. Самый громкий по модулю сэмпл в этой записи
отрицательный, а libsndfile при записи округляет **вниз** (к ближайшему меньшему
уровню сетки), — и вместо `-0.05` в файле оказалось `-0.050018`. Пик по модулю
подрос, RMS от такого смещения практически не изменился, поэтому отношение чуть
меньше `1/√2`. Числа в примере совпадают с выводом кода, а не с формулой.

### B5

```python
import numpy as np
import soundfile as sf
from pathlib import Path

sr = 16000
t = np.arange(int(sr * 0.5)) / sr
sf.write("tone_1000.wav", 0.5 * np.sin(2 * np.pi * 1000 * t), sr, subtype="PCM_16")
data, sr_read = sf.read("tone_1000.wav")
print(data.shape, sr_read, len(data) / sr_read)
print(Path("tone_1000.wav").stat().st_size, "байт")
```

`16044 = 8000 сэмплов × 2 байта + 44 байта заголовка wav`. В `PCM_16` на сэмпл
уходит ровно два байта, поэтому размер файла предсказуем заранее.

### B6

```python
import librosa
import numpy as np

y, sr = librosa.load("data/tone_440.wav", sr=None)
spectrum = np.abs(np.fft.rfft(y))
freqs = np.fft.rfftfreq(len(y), 1 / sr)
print(round(float(freqs[int(np.argmax(spectrum))]), 1), round(float(freqs[1]), 1))
```

Шаг частотной сетки равен `sr / N`, то есть `44100 / 88200 = 0.5` Гц. Запись
длится две секунды — чем длиннее окно, тем мельче шаг по частоте.

## Среднее

### M1

```python
import librosa
import numpy as np

y, sr = librosa.load("data/chord.wav", sr=None)
spectrum = np.abs(np.fft.rfft(y))
freqs = np.fft.rfftfreq(len(y), 1 / sr)
top = np.argsort(spectrum)[-2:]
peaks = sorted(top, key=lambda i: freqs[i])
print([round(float(freqs[i]), 1) for i in peaks])
print(round(float(spectrum[peaks[0]] / spectrum[peaks[1]]), 2))
```

Отношение амплитуд пиков `2.0` в точности повторяет то, как собран файл:
амплитуды тонов `0.6` и `0.3`. Спектр вернул исходный рецепт сигнала, которого
во временной области было не видно.

### M2

```python
import librosa

y, sr = librosa.load("data/chirp.wav", sr=None)
stft = librosa.stft(y, n_fft=2048, hop_length=512)
print(stft.shape)
print(2048 // 2 + 1, 1 + len(y) // 512)
```

Число строк задаётся размером окна, число столбцов — шагом между окнами. Обе
величины считаются заранее, до вызова: полезно, когда прикидываешь размер
признаков для модели.

### M3

```python
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

y, sr = librosa.load("data/chirp.wav", sr=None)
db = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=512)), ref=np.max)
librosa.display.specshow(db, sr=sr, hop_length=512, x_axis="time", y_axis="hz")
plt.savefig("chirp.png", dpi=100)

freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
peak = freqs[db.argmax(axis=0)]
print(*(round(float(peak[i]), 1) for i in (0, db.shape[1] // 2, -1)))
```

Числа `204.6 → 1098.2 → 1991.8` — это и есть диагональ на картинке, выраженная
числами: частота растёт примерно линейно от 200 к 2000 Гц.

### M4

```python
import librosa
import numpy as np

y, sr = librosa.load("data/bursts.wav", sr=None)
mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=512, n_mels=64)
db = librosa.power_to_db(mel, ref=np.max)
print(db.shape)
print(*(int(db[:, frame].argmax()) for frame in (10, 53, 96)))
```

Частоты всплесков растут вдвое (440 → 880 → 1760), а номера мел-полос — нет
(`8 → 16 → 29`): шаг мел-шкалы примерно логарифмический, поэтому удвоение
частоты даёт примерно одинаковый сдвиг по полосам.

### M5

```python
import librosa
import numpy as np


def main_frequency(y, sr):
    spectrum = np.abs(np.fft.rfft(y))
    return float(np.fft.rfftfreq(len(y), 1 / sr)[int(np.argmax(spectrum))])


for kwargs in ({"sr": None}, {}):
    y, sr = librosa.load("data/lowrate.wav", **kwargs)
    print(sr, y.shape, round(len(y) / sr, 4), round(main_frequency(y, sr), 1))
```

Ресемплинг меняет число сэмплов, но не меняет ни длительность, ни частоты
внутри сигнала: 300 Гц остаются 300 Гц. Здесь частота даже выросла — с 8000 до
22050, — но новых деталей в записи от этого не появилось.

### M6

```python
import librosa
import numpy as np

y, sr = librosa.load("data/chord.wav", sr=None)
loud = y * 2
outside = np.abs(loud) > 1.0
print(int(outside.sum()), len(loud), round(float(outside.mean()), 4))
clipped = np.clip(loud, -1, 1)
print(round(float(np.abs(loud).max()), 4), round(float(np.abs(clipped).max()), 4))
```

`np.clip` возвращает пик к единице, но срезанные вершины не восстановятся: 36%
сэмплов уже потеряли исходное значение. Правильный путь — нормализация до
записи, а не обрезка после.

### M7

```python
import librosa
import numpy as np

for name in ("noise.wav", "chord.wav"):
    y, sr = librosa.load("data/" + name, sr=None)
    spectrum = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1 / sr)
    ratio = float(spectrum.max() / spectrum.mean())
    print(name, round(ratio, 1), round(float(freqs[int(spectrum.argmax())]), 1))
```

У шума все частоты представлены примерно поровну: самый громкий бин выше
среднего всего в 3.7 раза, и его частота (9393 Гц) — случайность, при другом
seed она была бы другой. У аккорда тот же показатель — 22042: спектр не плоский,
а состоит из двух узких пиков, и максимум устойчиво стоит на 440 Гц. Отсюда
правило: «главная частота» осмысленна, только когда спектр не плоский.

## Сложное

### H1

Скрипт `spectrogram.py`:

```python
import sys

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

audio_path, image_path = sys.argv[1], sys.argv[2]
y, sr = librosa.load(audio_path, sr=None)
mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=512, n_mels=64)
features = librosa.power_to_db(mel, ref=np.max)

librosa.display.specshow(features, sr=sr, hop_length=512, x_axis="time", y_axis="mel")
plt.savefig(image_path, dpi=100)
print(sr, round(len(y) / sr, 4), features.shape)
```

Запуск:

```bash
python3 spectrogram.py data/chirp.wav chirp.png
python3 spectrogram.py data/bursts.wav bursts.png
```

Число мел-полос задаётся аргументом и потому одинаково у всех записей, а число
кадров зависит от длительности — отсюда `(64, 173)` и `(64, 130)`.

### H2

```python
import librosa
import numpy as np

y, sr = librosa.load("data/bursts.wav", sr=None)
rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
loud = rms > 0.1
times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)

# нули по краям + разность соседей: +1 — начало отрезка, -1 — сразу после конца
edges = np.diff(np.r_[0, loud.astype(int), 0])
starts = np.flatnonzero(edges == 1)
ends = np.flatnonzero(edges == -1) - 1
print("отрезков:", len(starts))
for begin, finish in zip(starts, ends):
    print(round(float(times[begin]), 2), round(float(times[finish]), 2))
```

Отрезки ищутся без цикла: булев массив превращается в 0/1, по краям приписываются
нули, и разность соседних элементов даёт +1 там, где отрезок начался, и -1 сразу
после того, как он кончился. Тот же результат даёт обычный цикл с флагом «мы
внутри отрезка» — берите то, что понятнее.

Границы смещены, потому что кадр длиной 2048 сэмплов (около 0.09 с) захватывает
и тишину, и звук: он становится «громким» чуть раньше настоящего начала
всплеска и остаётся таким чуть дольше его конца. Точность границ не может быть
лучше длины кадра — это плата за переход от отдельных сэмплов к кадрам.

### H3

```python
import librosa
import numpy as np
import torchaudio

y, sr = librosa.load("data/stereo.wav", sr=None, mono=False)
waveform, sr_torch = torchaudio.load("data/stereo.wav")
print(y.shape, tuple(waveform.shape), sr, sr_torch)
print(round(float(np.abs(y - waveform.numpy()).max()), 6))
```

`librosa` с `mono=False` и `torchaudio` дают форму `(каналы, сэмплы)` — канал
первой осью, в отличие от `soundfile`, у которого канал последний.
`torchaudio.load` возвращает `torch.Tensor` типа `float32`, а не массив
`numpy`; значения при этом совпадают побитово, расхождение `0.0`.

### H4

```python
import torch
import torchaudio

first, sr = torchaudio.load("data/chirp.wav")
second, _ = torchaudio.load("data/chord.wav")
length = min(first.shape[1], second.shape[1])
batch = torch.cat([first[:, :length], second[:, :length]])

mel = torchaudio.transforms.MelSpectrogram(sr, n_fft=2048, hop_length=512, n_mels=64)
to_db = torchaudio.transforms.AmplitudeToDB(stype="power", top_db=80)
features = to_db(mel(batch))
print(tuple(batch.shape), tuple(features.shape), features.dtype)
```

Преобразования `torchaudio` — обычные модули, они принимают батч и добавляют
оси признаков, не требуя цикла. Обрезка до общей длины обязательна: в один
тензор складываются только записи одинакового размера.

### H5

```python
import subprocess

import numpy as np

probe = subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "v:0",
     "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
     "-of", "csv=p=0", "data/clip.mp4"],
    capture_output=True, text=True, check=True).stdout.strip()
print(probe)
width, height, rate, count = probe.split(",")
fps = int(rate.split("/")[0]) / int(rate.split("/")[1])

raw = subprocess.run(
    ["ffmpeg", "-v", "error", "-i", "data/clip.mp4",
     "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
    capture_output=True, check=True).stdout
frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, int(height), int(width), 3)
print(frames.shape, round(len(frames) / fps, 4))
print(int(frames[10, 24, :, 0].argmax()))
```

Частота кадров приходит дробью `10/1`, а не числом, — её нужно вычислить.
Размеры кадра берутся из метаданных, поэтому тот же скрипт разберёт и другое
видео. Квадрат в кадре 10 стоит на `x = 20`: он сдвигается на два пикселя за
кадр.

### H6

```python
import librosa
import numpy as np

y, sr = librosa.load("data/chirp.wav", sr=None)
windows = [y[i:i + sr] for i in range(0, len(y) - sr + 1, sr)]
features = np.stack([
    librosa.power_to_db(
        librosa.feature.melspectrogram(y=w, sr=sr, n_fft=2048, hop_length=512, n_mels=64),
        ref=np.max)
    for w in windows])
print(features.shape)
print([int(f.mean(axis=1).argmax()) for f in features])
```

`f.mean(axis=1)` усредняет децибелы, то есть даёт средний **уровень** полосы, а
не её среднюю энергию; для ответа «какая полоса громче» этого достаточно. Нарезка
на окна одинаковой длины — стандартный способ подать запись переменной
длительности модели с фиксированным входом. Условие `len(y) - sr + 1` в
`range` отбрасывает неполный хвост: иначе последнее окно окажется короче
остальных, и `np.stack` откажется собирать массив.
