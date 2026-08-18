# Примеры решений

## База

### B1

```python
import numpy as np
from PIL import Image

image = Image.open("assets/photo.png")
print(image.format, image.size, image.mode)

array = np.asarray(image)
print(array.shape, array.dtype, array.min(), array.max())
```

### B2

```python
import os

import numpy as np
from PIL import Image

print(os.path.getsize("assets/photo.png"), os.path.getsize("assets/photo.jpg"))

png = np.asarray(Image.open("assets/photo.png")).astype(int)
jpg = np.asarray(Image.open("assets/photo.jpg")).astype(int)
print(np.abs(png - jpg).max())
```

Приводить к `int` обязательно: у `uint8` вычитание уходит в переполнение, и
разница `10 - 20` даёт `246`.

### B3

```python
from PIL import Image

photo = Image.open("assets/photo.gif")
print(photo.mode, len(photo.getpalette()) // 3)

animation = Image.open("assets/animation.gif")
print(animation.n_frames, animation.size)
```

### B4

```python
import tifffile

scan = tifffile.imread("assets/scan16.tif")
print(scan.dtype, scan.min(), scan.max())

stack = tifffile.imread("assets/stack.tif")
print(stack.shape[0], stack.shape[1:])
```

### B5

```python
import pydicom

ds = pydicom.dcmread("assets/ct-slice.dcm")
print(ds.Modality, ds.Rows, ds.Columns, ds.PixelSpacing)

pixels = ds.pixel_array
print(pixels.dtype, pixels.min(), pixels.max())
```

### B6

```python
import numpy as np
from PIL import Image

image = np.asarray(Image.open("assets/photo.png")).astype(np.float32) / 255.0
print(image.dtype, image.min(), image.max(), round(float(image.mean()), 4))
```

`astype(np.float32)` до деления, а не после: `array / 255` сразу даёт `float64`
и вдвое больше памяти на тот же датасет.

## Среднее

### M1

```python
import numpy as np
import pydicom

ds = pydicom.dcmread("assets/ct-slice.dcm")
hu = ds.pixel_array * ds.RescaleSlope + ds.RescaleIntercept

print(hu.min(), hu.max())
print(np.unique(hu))
```

### M2

```python
import numpy as np
import pydicom

ds = pydicom.dcmread("assets/ct-slice.dcm")
hu = ds.pixel_array * ds.RescaleSlope + ds.RescaleIntercept

low = float(ds.WindowCenter) - float(ds.WindowWidth) / 2
high = float(ds.WindowCenter) + float(ds.WindowWidth) / 2
windowed = np.clip((hu - low) / (high - low), 0, 1)
result = (windowed * 255).round().astype(np.uint8)

print(low, high)
print(np.unique(result))
```

`np.clip` и делает обрезку по границам окна: всё ниже `low` становится нулём,
всё выше `high` — единицей.

### M3

```python
import numpy as np
from PIL import Image

animation = Image.open("assets/animation.gif")

for number in range(animation.n_frames):
    animation.seek(number)
    frame = animation.convert("L")
    frame.save(f"frame-{number}.png")
    print(number, round(float(np.asarray(frame).mean()), 2))
```

`seek` переводит объект на нужный кадр; `convert("L")` превращает индексы
палитры в яркость — усреднять индексы бессмысленно.

### M4

```python
import numpy as np
from PIL import Image

array = np.asarray(Image.open("assets/photo.png"))

size = 64
top = (array.shape[0] - size) // 2
left = (array.shape[1] - size) // 2
crop = array[top : top + size, left : left + size]

print(crop.shape)
Image.fromarray(crop).save("crop.png")
```

### M5

```python
import numpy as np
from PIL import Image

array = np.asarray(Image.open("assets/photo.png"))


def gamma_correction(image, gamma):
    return np.clip(255 * (image / 255) ** gamma, 0, 255).astype(np.uint8)


print(round(float(array.mean()), 1))
for gamma in (0.5, 2.2):
    print(gamma, round(float(gamma_correction(array, gamma).mean()), 1))
```

### M6

```python
import numpy as np
import tifffile
from PIL import Image

scan = tifffile.imread("assets/scan16.tif")
print(len(np.unique(scan)))

via_convert = np.asarray(Image.open("assets/scan16.tif").convert("L"))
print(len(np.unique(via_convert)))

scaled = (scan - scan.min()) / (scan.max() - scan.min())
print(len(np.unique((scaled * 255).round().astype(np.uint8))))
```

`convert("L")` у Pillow для режима `I;16` не растягивает диапазон, а обрезает
его — от снимка остаются два уровня. Восьмибитную версию шестнадцатибитных
данных всегда делают явным масштабированием.

## Сложное

### H1

`convert.py`:

```python
#!/usr/bin/env python3
"""Конвертирует изображение между форматами."""

import argparse

import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description="Конвертация изображений.")
    parser.add_argument("source", help="исходный файл")
    parser.add_argument("target", help="куда сохранить; формат берётся из расширения")
    parser.add_argument("--quality", type=int, default=75, help="качество JPEG")
    parser.add_argument("--gamma", type=float, default=None, help="гамма-коррекция")
    args = parser.parse_args()

    image = Image.open(args.source).convert("RGB")

    if args.gamma is not None:
        array = np.asarray(image)
        corrected = np.clip(255 * (array / 255) ** args.gamma, 0, 255)
        image = Image.fromarray(corrected.astype(np.uint8))

    if args.target.lower().endswith((".jpg", ".jpeg")):
        image.save(args.target, quality=args.quality)
    else:
        image.save(args.target)


if __name__ == "__main__":
    main()
```

### H2

`report.py`:

```python
#!/usr/bin/env python3
"""Печатает CSV со сведениями об изображениях в каталоге."""

import argparse
import csv
import os
import sys

from PIL import Image, UnidentifiedImageError


def describe(path):
    try:
        with Image.open(path) as image:
            return [
                image.format,
                image.size[0],
                image.size[1],
                image.mode,
                getattr(image, "n_frames", 1),
            ]
    except (UnidentifiedImageError, OSError):
        return ["не распознан", "", "", "", ""]


def main():
    parser = argparse.ArgumentParser(description="Отчёт по каталогу с изображениями.")
    parser.add_argument("directory", help="каталог с файлами")
    args = parser.parse_args()

    writer = csv.writer(sys.stdout)
    writer.writerow(["name", "format", "width", "height", "mode", "frames"])

    for name in sorted(os.listdir(args.directory)):
        writer.writerow([name, *describe(os.path.join(args.directory, name))])


if __name__ == "__main__":
    main()
```

### H3

`dicom2png.py`:

```python
#!/usr/bin/env python3
"""Переводит срез DICOM в PNG с оконным преобразованием."""

import argparse

import numpy as np
import pydicom
from PIL import Image


def window_from_tags(ds, hu):
    if "WindowCenter" in ds and "WindowWidth" in ds:
        center = float(getattr(ds.WindowCenter, "value", ds.WindowCenter))
        width = float(getattr(ds.WindowWidth, "value", ds.WindowWidth))
        return center, width

    low, high = np.percentile(hu, [1, 99])
    return (low + high) / 2, high - low


def main():
    parser = argparse.ArgumentParser(description="DICOM в PNG.")
    parser.add_argument("source", help="файл DICOM")
    parser.add_argument("target", help="куда сохранить PNG")
    parser.add_argument("--center", type=float, default=None, help="центр окна, HU")
    parser.add_argument("--width", type=float, default=None, help="ширина окна, HU")
    args = parser.parse_args()

    ds = pydicom.dcmread(args.source)
    hu = ds.pixel_array * ds.RescaleSlope + ds.RescaleIntercept

    center, width = window_from_tags(ds, hu)
    if args.center is not None:
        center = args.center
    if args.width is not None:
        width = args.width

    low, high = center - width / 2, center + width / 2
    windowed = np.clip((hu - low) / (high - low), 0, 1)
    result = (windowed * 255).round().astype(np.uint8)

    Image.fromarray(result).save(args.target)
    print(f"center={center} width={width} levels={len(np.unique(result))}")


if __name__ == "__main__":
    main()
```

Ширину окна берут из тегов, а не считают по срезу: у КТ шкала физическая, и
`min`/`max` конкретного среза зависят от того, попал ли в него металл или воздух.

### H4

`verify.py`:

```python
#!/usr/bin/env python3
"""Проверяет, что все изображения каталога читаются и имеют нужный размер."""

import argparse
import os
import sys

from PIL import Image, UnidentifiedImageError


def main():
    parser = argparse.ArgumentParser(description="Проверка датасета изображений.")
    parser.add_argument("directory", help="каталог с изображениями")
    parser.add_argument(
        "--expected-size",
        type=int,
        nargs=2,
        metavar=("ШИРИНА", "ВЫСОТА"),
        required=True,
    )
    args = parser.parse_args()

    expected = tuple(args.expected_size)
    problems = 0

    for name in sorted(os.listdir(args.directory)):
        path = os.path.join(args.directory, name)
        try:
            with Image.open(path) as image:
                if image.size != expected:
                    print(f"{name}: размер {image.size}, ожидался {expected}")
                    problems += 1
                image.load()
        except UnidentifiedImageError:
            print(f"{name}: не распознан как изображение")
        except OSError as error:
            print(f"{name}: файл не читается ({error})")
            problems += 1

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
```

`image.load()` здесь обязателен. `Image.open` читает только заголовок, поэтому
у обрезанного файла размер прочитается нормально и проверка ничего не заметит —
ошибка вылезет позже, во время обучения. Пиксели нужно декодировать явно.

Нераспознанный формат и битый файл — разные истории: `ct-slice.dcm` просто не
картинка, а обрезанный PNG означает испорченные данные.

### H5

`resize_pair.py`:

```python
#!/usr/bin/env python3
"""Согласованно уменьшает изображение и маску сегментации."""

import argparse
import sys

import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description="Ресайз изображения вместе с маской.")
    parser.add_argument("--image", default="assets/photo.png")
    parser.add_argument("--mask", default="assets/mask.png")
    parser.add_argument("--size", type=int, required=True, help="сторона результата")
    args = parser.parse_args()

    size = (args.size, args.size)

    image = Image.open(args.image).resize(size, Image.BILINEAR)
    image.save("image-resized.png")

    mask = Image.open(args.mask)
    before = set(np.unique(np.asarray(mask)).tolist())

    resized = mask.resize(size, Image.NEAREST)
    after = set(np.unique(np.asarray(resized)).tolist())
    resized.save("mask-resized.png")

    print("значения маски до:", sorted(before))
    print("значения маски после:", sorted(after))

    wrong = set(np.unique(np.asarray(mask.resize(size, Image.BILINEAR))).tolist())
    print("а так было бы с BILINEAR:", len(wrong), "значений")

    if not after <= before:
        print("в маске появились новые значения")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

Маска хранит номера классов, а не яркость. Любая интерполяция, кроме
ближайшего соседа, усредняет соседние номера и создаёт классы, которых в
разметке не было.

### H6

`jpeg_quality.py`:

```python
#!/usr/bin/env python3
"""Показывает, как качество JPEG влияет на размер файла и PSNR."""

import argparse
import io

import numpy as np
from PIL import Image

QUALITIES = (10, 30, 50, 70, 90, 95)


def psnr(original, decoded):
    mse = ((original - decoded) ** 2).mean()
    if mse == 0:
        return float("inf")
    return 10 * np.log10(255 ** 2 / mse)


def main():
    parser = argparse.ArgumentParser(description="Качество JPEG против PSNR.")
    parser.add_argument("--source", default="assets/photo.png")
    parser.add_argument("--psnr", type=float, required=True, help="порог PSNR, дБ")
    args = parser.parse_args()

    image = Image.open(args.source).convert("RGB")
    original = np.asarray(image).astype(np.float64)

    chosen = None
    for quality in QUALITIES:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        decoded = np.asarray(Image.open(io.BytesIO(buffer.getvalue()))).astype(np.float64)

        value = psnr(original, decoded)
        print(f"quality={quality} size={buffer.getbuffer().nbytes} psnr={value:.2f}")

        if chosen is None and value >= args.psnr:
            chosen = quality

    print("минимальное подходящее качество:", chosen)


if __name__ == "__main__":
    main()
```
