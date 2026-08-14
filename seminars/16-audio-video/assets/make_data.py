#!/usr/bin/env python3
"""Готовит каталог `data/` с учебными аудио- и видеофайлами для семинара 16.

    python3 assets/make_data.py           # создать ./data
    python3 assets/make_data.py /tmp/s16  # создать /tmp/s16/data

Бинарных файлов в репозитории нет: всё генерируется здесь и **детерминированно**
— синусы заданных частот, чирп, шум с фиксированным seed. Поэтому числа в
тестовых примерах `tasks.md` (длительность, форма массива, номер частотного
бина) совпадают у всех до последней цифры. Скрипт можно запускать повторно:
файлы перезаписываются.

Нужны `numpy` и `soundfile`; видео собирается внешним `ffmpeg` (если его нет,
звук всё равно сгенерируется, а видеозадачи придётся пропустить).
"""

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SEED = 16          # seed шума: одинаковый шум у всех
VIDEO_W = 64       # ширина кадра учебного видео
VIDEO_H = 48       # высота кадра
VIDEO_FPS = 10     # кадров в секунду
VIDEO_FRAMES = 30  # ровно 3.0 секунды


def times(sr: int, seconds: float) -> np.ndarray:
    """Моменты времени сэмплов: N = sr * seconds точек, шаг 1/sr."""
    return np.arange(int(sr * seconds), dtype=np.float64) / sr


def tone(freq: float, sr: int, seconds: float, amp: float = 0.5) -> np.ndarray:
    """Синус частоты `freq` Гц с нулевой начальной фазой."""
    return amp * np.sin(2 * np.pi * freq * times(sr, seconds))


def write_audio(path: Path, data: np.ndarray, sr: int) -> None:
    """Записывает wav в 16-битном PCM — самый ходовой формат для учебных данных."""
    sf.write(path, data, sr, subtype="PCM_16")
    print(f"  {path.name}: sr={sr}, форма {np.shape(data)}")


def make_audio(root: Path) -> None:
    print("аудио:")

    # 1. Чистый тон 440 Гц (нота ля) на «музыкальной» частоте 44100.
    write_audio(root / "tone_440.wav", tone(440, 44100, 2.0), 44100)

    # 2. Аккорд: два тона сразу — во временной области их не различить.
    chord = tone(440, 22050, 3.0, amp=0.6) + tone(660, 22050, 3.0, amp=0.3)
    write_audio(root / "chord.wav", chord, 22050)

    # 3. Чирп: частота линейно растёт с 200 до 2000 Гц.
    t = times(22050, 4.0)
    phase = 2 * np.pi * (200 * t + (2000 - 200) / (2 * 4.0) * t**2)
    write_audio(root / "chirp.wav", 0.5 * np.sin(phase), 22050)

    # 4. Белый шум с фиксированным seed — у всех одинаковый.
    rng = np.random.default_rng(SEED)
    noise = np.clip(0.1 * rng.standard_normal(22050), -1.0, 1.0)
    write_audio(root / "noise.wav", noise, 22050)

    # 5. Стерео: слева 440 Гц, справа 880 Гц. Форма (N, 2) — канал последний.
    left = tone(440, 22050, 2.0, amp=0.5)
    right = tone(880, 22050, 2.0, amp=0.25)
    write_audio(root / "stereo.wav", np.stack([left, right], axis=1), 22050)

    # 6. Та же природа сигнала, но частота дискретизации 8000 — «телефонная».
    write_audio(root / "lowrate.wav", tone(300, 8000, 1.5), 8000)

    # 7. Очень тихая запись: пик 0.05 — материал для нормализации.
    write_audio(root / "quiet.wav", tone(220, 22050, 1.0, amp=0.05), 22050)

    # 8. Три коротких всплеска с тишиной между ними — материал для RMS по кадрам.
    bursts = np.zeros(int(22050 * 3.0))
    for start, freq in [(0.0, 440.0), (1.0, 880.0), (2.0, 1760.0)]:
        begin = int(start * 22050)
        bursts[begin:begin + int(0.5 * 22050)] = tone(freq, 22050, 0.5)
    write_audio(root / "bursts.wav", bursts, 22050)


def video_frames() -> np.ndarray:
    """Кадры учебного видео: белый квадрат 8×8 едет вправо по чёрному фону.

    На последних кадрах квадрат частично уезжает за правый край: срез numpy
    обрезается по ширине кадра, и белая полоса становится у́же 8 пикселей.
    """
    frames = np.zeros((VIDEO_FRAMES, VIDEO_H, VIDEO_W, 3), dtype=np.uint8)
    for i in range(VIDEO_FRAMES):
        x = 2 * i
        frames[i, 20:28, x:x + 8] = 255
    return frames


def make_video(root: Path) -> None:
    path = root / "clip.mp4"
    if shutil.which("ffmpeg") is None:
        print("видео: ffmpeg не найден, clip.mp4 пропущен")
        return
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{VIDEO_W}x{VIDEO_H}", "-r", str(VIDEO_FPS),
        "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
    ]
    subprocess.run(command, input=video_frames().tobytes(), check=True)
    print(f"видео:\n  {path.name}: {VIDEO_FRAMES} кадров, "
          f"{VIDEO_W}x{VIDEO_H}, {VIDEO_FPS} кадров/с")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".") / "data"
    root.mkdir(parents=True, exist_ok=True)
    make_audio(root)
    make_video(root)
    print(f"данные готовы: {root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
