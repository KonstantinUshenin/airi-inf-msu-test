"""Генерирует учебные изображения семинара.

Все файлы в этом каталоге синтетические и собраны этим скриптом:
реальных снимков пациентов в репозитории нет. Запуск из каталога assets:

    pip install pillow numpy tifffile pydicom
    python3 make_assets.py
"""

import os

import numpy as np
from PIL import Image
import tifffile

import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)


def grid(size):
    y, x = np.mgrid[0:size, 0:size]
    return y, x


# --- 1. «Фотография»: градиент, фигуры, резкая граница и мелкая текстура ------
SIZE = 128
y, x = grid(SIZE)

red = (x * 255 // (SIZE - 1)).astype(np.int32)
green = (y * 255 // (SIZE - 1)).astype(np.int32)
blue = np.full((SIZE, SIZE), 40, dtype=np.int32)

photo = np.dstack([red, green, blue])

circle = (x - 42) ** 2 + (y - 42) ** 2 < 24 ** 2
photo[circle] = (250, 250, 250)

photo[80:115, 74:114] = (10, 10, 10)
photo[:, 64] = (255, 0, 0)

texture = np.random.default_rng(15).integers(-24, 25, size=photo.shape)
photo = np.clip(photo + texture, 0, 255).astype(np.uint8)

Image.fromarray(photo).save(f"{OUT}/photo.png", optimize=True)
Image.fromarray(photo).save(f"{OUT}/photo.jpg", quality=30)
Image.fromarray(photo).convert("P", palette=Image.ADAPTIVE, colors=64).save(
    f"{OUT}/photo.gif"
)

# --- 2. Анимированный GIF: четыре кадра ---------------------------------------
frames = []
for step in range(4):
    frame = np.zeros((64, 64), dtype=np.uint8)
    side = 8 + step * 8
    frame[4 : 4 + side, 4 + step * 6 : 4 + step * 6 + side] = 255
    frames.append(Image.fromarray(frame).convert("P"))

frames[0].save(
    f"{OUT}/animation.gif",
    save_all=True,
    append_images=frames[1:],
    duration=200,
    loop=0,
)

# --- 3. Шестнадцатибитный TIFF -------------------------------------------------
SIZE16 = 128
y, x = grid(SIZE16)

scan = (x.astype(np.uint32) * 65535 // (SIZE16 - 1)).astype(np.uint16)
spot = (x - 90) ** 2 + (y - 40) ** 2 < 20 ** 2
scan[spot] = 65535
scan[100:120, 10:60] = 1200

tifffile.imwrite(f"{OUT}/scan16.tif", scan)

# --- 4. Многостраничный TIFF ---------------------------------------------------
pages = np.stack(
    [np.full((64, 64), value, dtype=np.uint8) for value in (30, 120, 210)]
)
pages[0, 10:30, 10:30] = 200
pages[1, 20:40, 20:40] = 20
pages[2, 30:50, 30:50] = 90

page_images = [Image.fromarray(page) for page in pages]
page_images[0].save(
    f"{OUT}/stack.tif", save_all=True, append_images=page_images[1:]
)

# --- 5. Синтетический КТ-срез в DICOM ------------------------------------------
CT = 128
y, x = grid(CT)

hu = np.full((CT, CT), -1000, dtype=np.int16)          # воздух

body = ((x - 64) / 52.0) ** 2 + ((y - 64) / 44.0) ** 2 < 1.0
hu[body] = 40                                          # мягкие ткани

fat = ((x - 64) / 46.0) ** 2 + ((y - 64) / 38.0) ** 2 < 1.0
hu[body & ~fat] = -90                                  # подкожный жир

lung_left = (x - 45) ** 2 + (y - 60) ** 2 < 18 ** 2
lung_right = (x - 83) ** 2 + (y - 60) ** 2 < 18 ** 2
hu[lung_left | lung_right] = -750                      # лёгкие

spine = (x - 64) ** 2 + ((y - 100) / 0.8) ** 2 < 10 ** 2
hu[spine] = 900                                        # позвонок

INTERCEPT = -1024
stored = (hu.astype(np.int32) - INTERCEPT).astype(np.uint16)

file_meta = FileMetaDataset()
file_meta.MediaStorageSOPClassUID = pydicom.uid.CTImageStorage
file_meta.MediaStorageSOPInstanceUID = generate_uid()
file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

ds = Dataset()
ds.file_meta = file_meta
ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
ds.StudyInstanceUID = generate_uid()
ds.SeriesInstanceUID = generate_uid()

ds.PatientName = "PHANTOM^COURSE"
ds.PatientID = "COURSE-0001"
ds.PatientBirthDate = ""
ds.Modality = "CT"
ds.StudyDate = "20260901"
ds.SeriesDescription = "synthetic teaching phantom"
ds.BodyPartExamined = "CHEST"

ds.Rows, ds.Columns = stored.shape
ds.SamplesPerPixel = 1
ds.PhotometricInterpretation = "MONOCHROME2"
ds.BitsAllocated = 16
ds.BitsStored = 16
ds.HighBit = 15
ds.PixelRepresentation = 0
ds.PixelSpacing = [1.5, 1.5]
ds.SliceThickness = 2.5
ds.ImagePositionPatient = [-96.0, -96.0, 0.0]
ds.RescaleIntercept = INTERCEPT
ds.RescaleSlope = 1
ds.WindowCenter = 40
ds.WindowWidth = 400
ds.PixelData = stored.tobytes()

ds.save_as(f"{OUT}/ct-slice.dcm", enforce_file_format=True)

# --- 6. Маска сегментации ------------------------------------------------------
mask = np.zeros((CT, CT), dtype=np.uint8)
mask[body] = 128
mask[spine] = 255

Image.fromarray(mask, mode="L").save(f"{OUT}/mask.png", optimize=True)

for name in sorted(os.listdir(OUT)):
    print(f"{name:16} {os.path.getsize(f'{OUT}/{name}'):>7} байт")
