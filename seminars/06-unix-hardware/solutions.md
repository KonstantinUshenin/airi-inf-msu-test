# Примеры решений

## База

### B1

```bash
{
  lscpu | grep -E '^(Architecture|Model name|CPU\(s\)|Core\(s\) per socket)'
  echo "nproc=$(nproc)"
} > cpu.txt

cat cpu.txt
```

### B2

```bash
{
  free -h
  grep -E '^(MemTotal|MemAvailable|SwapTotal)' /proc/meminfo
} > memory.txt

cat memory.txt
```

### B3

```bash
{
  lsblk -e 7 -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
  df -h .
} > disks.txt

cat disks.txt
```

`-e 7` убирает устройства с major-номером 7 — это loop-устройства, за которыми
стоят образы пакетов snap, а не настоящие диски.

### B4

```bash
{
  echo "pci_devices=$(lspci | wc -l)"
  lspci | grep -iE 'vga|3d controller' || echo 'vga: not found'
  echo "usb_devices=$(lsusb | wc -l)"
} > devices.txt

cat devices.txt
```

### B5

```bash
{
  echo "processors=$(grep -c '^processor' assets/cpuinfo.txt)"
  grep -m 1 '^model name' assets/cpuinfo.txt
} > saved-cpu.txt

cat saved-cpu.txt
```

### B6

`gpu-check.sh`:

```bash
#!/usr/bin/env bash

set -uo pipefail

if command -v nvidia-smi > /dev/null && nvidia-smi > gpu-check.txt 2>/dev/null; then
  : # вывод уже записан
else
  echo 'gpu=none' > gpu-check.txt
fi
```

Двух проверок мало по отдельности: `command -v` ловит случай «программы нет»,
но `nvidia-smi` бывает установлена при незагруженном драйвере — тогда она
существует, а завершается ненулевым кодом. Условие покрывает оба случая, и
скрипт в любом из них возвращает `0`, как требует задание.

## Среднее

### M1

```bash
{
  echo "logical=$(grep -c '^processor' assets/cpuinfo.txt)"
  echo "physical=$(grep -E '^(physical id|core id)' assets/cpuinfo.txt \
    | paste - - | sort -u | wc -l)"
} > cores.txt

cat cores.txt
```

`paste - -` склеивает соседние строки попарно, поэтому `physical id` и `core id`
одного процессора оказываются в одной строке; `sort -u` оставляет уникальные
пары, то есть физические ядра.

### M2

`meminfo.py`:

```python
#!/usr/bin/env python3
"""Печатает ключевые строки /proc/meminfo в гигабайтах."""

import sys

KEYS = ("MemTotal", "MemAvailable", "SwapTotal")


def read_meminfo(path):
    values = {}
    with open(path) as handle:
        for line in handle:
            name, _, rest = line.partition(":")
            if name in KEYS:
                values[name] = int(rest.split()[0])
    return values


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/proc/meminfo"
    values = read_meminfo(path)
    for key in KEYS:
        print(f"{key}={values[key] / 1024 / 1024:.1f} GiB")


if __name__ == "__main__":
    main()
```

```bash
python3 meminfo.py assets/meminfo.txt
```

### M3

`gpu-free.py`:

```python
#!/usr/bin/env python3
"""Находит видеокарту с наибольшим объёмом свободной памяти."""

import sys


def read_gpus(path):
    gpus = []
    with open(path) as handle:
        next(handle)
        for line in handle:
            if not line.strip():
                continue
            index, _, total, used, _ = [part.strip() for part in line.split(",")]
            free = int(total.split()[0]) - int(used.split()[0])
            gpus.append((int(index), free))
    return gpus


def main():
    index, free = max(read_gpus(sys.argv[1]), key=lambda item: item[1])
    print(f"gpu={index} free={free} MiB")


if __name__ == "__main__":
    main()
```

```bash
python3 gpu-free.py assets/nvidia-smi.csv
```

### M4

`hwinfo.py`:

```python
#!/usr/bin/env python3
"""Короткая сводка о машине."""

import subprocess


def logical_cpus():
    result = subprocess.run(["nproc"], capture_output=True, text=True, check=True)
    return int(result.stdout.strip())


def mem_total_gib():
    with open("/proc/meminfo") as handle:
        for line in handle:
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) / 1024 / 1024
    raise RuntimeError("в /proc/meminfo нет строки MemTotal")


def main():
    print(f"cpus={logical_cpus()}")
    print(f"mem_total_gib={mem_total_gib():.1f}")


if __name__ == "__main__":
    main()
```

`check=True` превращает ненулевой код команды в исключение — без него ошибка
`nproc` осталась бы незамеченной, а `int("")` упал бы с непонятным сообщением.

### M5

```bash
# Первый НАСТОЯЩИЙ диск: без фильтра по типу на Ubuntu первым идёт loop0 со snap.
disk=$(lsblk -dn -o PATH,TYPE | awk '$2 == "disk" {print $1; exit}')

{
  ls -l /dev/null /dev/random "$disk"   # первая буква: c — символьное, b — блочное
  lsblk -dn -o NAME,MAJ:MIN,TYPE "$disk"
} > devices.txt

cat devices.txt
```

Вместо размера у таких файлов стоят два числа: major говорит ядру, какой
драйвер обслуживает устройство, minor — какое именно устройство этого драйвера
имеется в виду. Данных в самом файле нет, это точка входа в драйвер.

### M6

`disks.py`:

```python
#!/usr/bin/env python3
"""Размеры дисков из вывода lsblk -J -b."""

import json
import sys

GIB = 1024 ** 3
TIB = 1024 ** 4


def main():
    with open(sys.argv[1]) as handle:
        data = json.load(handle)

    total = 0
    for device in data["blockdevices"]:
        if device["type"] != "disk":
            continue
        total += device["size"]
        print(f'{device["name"]} {device["size"] / GIB:.1f} GiB')

    print(f"total {total / TIB:.2f} TiB")


if __name__ == "__main__":
    main()
```

```bash
python3 disks.py assets/lsblk.json
```

### M7

`smart-report.sh`:

```bash
#!/usr/bin/env bash

set -uo pipefail

# Системный диск — тот, на котором смонтирован корень, а не первый в списке.
root_part=$(findmnt -n -o SOURCE /)                 # например /dev/nvme0n1p2
disk="/dev/$(lsblk -no PKNAME "$root_part")"        # PKNAME — родительское устройство раздела

if ! command -v smartctl > /dev/null; then
  echo 'smartctl не установлен: sudo apt install smartmontools' > smart.txt
elif ! sudo -n smartctl -H "$disk" > /dev/null 2>&1; then
  echo "нет прав на чтение SMART у $disk: запустите через sudo" > smart.txt
else
  sudo smartctl -H -A "$disk" \
    | grep -E 'result|Model|Power_On_Hours|Reallocated_Sector_Ct' > smart.txt
fi

cat smart.txt
```

Скрипт различает две разные причины неудачи: утилиты нет и прав не хватает.
В обоих случаях он завершается нулевым кодом — отсутствие `smartctl` не повод
ронять отчёт о машине.

## Сложное

### H1

`hw-report.py`:

```python
#!/usr/bin/env python3
"""Отчёт о железе машины."""

import json
import shutil
import subprocess
import sys


def run(command):
    """stdout команды или None, если её нет в системе или она завершилась ошибкой."""
    if shutil.which(command[0]) is None:
        return None

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return None

    return result.stdout.strip()


def cpu_section():
    model = None
    logical = 0

    with open("/proc/cpuinfo") as handle:
        for line in handle:
            if line.startswith("processor"):
                logical += 1
            elif line.startswith("model name") and model is None:
                model = line.split(":", 1)[1].strip()

    return {"logical_cpus": logical, "model": model}


def mem_section():
    values = {}

    with open("/proc/meminfo") as handle:
        for line in handle:
            name, _, rest = line.partition(":")
            if name in ("MemTotal", "MemAvailable"):
                values[name.lower()] = round(int(rest.split()[0]) / 1024 / 1024, 1)

    return values


def disk_section():
    output = run(["lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE"])
    if output is None:
        return None

    disks = [
        {"name": device["name"], "size_gib": round(device["size"] / 1024 ** 3, 1)}
        for device in json.loads(output)["blockdevices"]
        if device["type"] == "disk"
    ]
    return {"disks": disks}


def gpu_section():
    output = run(
        ["nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader"]
    )
    if output is None:
        return None

    return {"gpus": [line.strip() for line in output.splitlines()]}


SECTIONS = {
    "cpu": cpu_section,
    "mem": mem_section,
    "disk": disk_section,
    "gpu": gpu_section,
}


def main():
    section = sys.argv[1] if len(sys.argv) > 1 else "all"
    as_json = len(sys.argv) > 2 and sys.argv[2] == "json"

    if section != "all" and section not in SECTIONS:
        print(f"неизвестный раздел: {section}", file=sys.stderr)
        sys.exit(2)

    names = list(SECTIONS) if section == "all" else [section]
    report = {name: SECTIONS[name]() for name in names}

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for name, value in report.items():
            print(f"[{name}] {value}")


if __name__ == "__main__":
    main()
```

Раздел, для которого утилиты нет, получает `None`; остальные всё равно
собираются, и код возврата остаётся нулевым. Аргументы разбираются вручную:
`argparse` в этом семинаре не используется.

### H2

`suggest.py`:

```python
#!/usr/bin/env python3
"""Подбирает видеокарту, размер батча и число загрузчиков данных."""

import sys

RESERVE = 0.9


def read_gpus(path):
    gpus = []
    with open(path) as handle:
        next(handle)
        for line in handle:
            if not line.strip():
                continue
            index, _, total, used, _ = [part.strip() for part in line.split(",")]
            free = int(total.split()[0]) - int(used.split()[0])
            gpus.append((int(index), free))
    return gpus


def physical_cores(path):
    cores = set()
    physical_id = None

    with open(path) as handle:
        for line in handle:
            name, _, rest = line.partition(":")
            name = name.strip()
            if name == "physical id":
                physical_id = rest.strip()
            elif name == "core id":
                cores.add((physical_id, rest.strip()))

    return len(cores)


def main():
    if len(sys.argv) != 4:
        print("использование: suggest.py GPU_CSV CPUINFO ПАМЯТЬ_НА_ОБРАЗЕЦ", file=sys.stderr)
        sys.exit(2)

    gpu_csv, cpuinfo, per_sample = sys.argv[1], sys.argv[2], int(sys.argv[3])

    index, free = max(read_gpus(gpu_csv), key=lambda item: item[1])
    batch = int(free * RESERVE / per_sample)

    print(f"gpu={index} batch={batch} num_workers={physical_cores(cpuinfo)}")


if __name__ == "__main__":
    main()
```

```bash
python3 suggest.py assets/nvidia-smi.csv assets/cpuinfo.txt 512
```

### H3

`run-timeout.py`:

```python
#!/usr/bin/env python3
"""Запускает команду с ограничением по времени."""

import subprocess
import sys
import time


def main():
    if len(sys.argv) < 3:
        print("использование: run-timeout.py СЕК КОМАНДА...", file=sys.stderr)
        sys.exit(2)

    limit = float(sys.argv[1])
    command = sys.argv[2:]

    started = time.monotonic()

    try:
        result = subprocess.run(command, timeout=limit)
    except subprocess.TimeoutExpired:
        print(f"timeout after {limit:g} s")
        sys.exit(124)

    print(f"returncode={result.returncode} elapsed={time.monotonic() - started:.2f} s")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
```

Всё, что идёт после числа, считается командой вместе с её собственными флагами:
разбирать их нам не нужно. По соглашению код `124` означает «убито по
таймауту» — так же поступает утилита `timeout`.

### H4

`fork-workers.py`:

```python
#!/usr/bin/env python3
"""Порождает несколько процессов через os.fork()."""

import os
import sys


def main():
    count = int(sys.argv[1])
    failing = int(sys.argv[2]) if len(sys.argv) > 2 else None

    for number in range(count):
        if os.fork() == 0:
            print(
                f"child number={number} pid={os.getpid()} ppid={os.getppid()}",
                flush=True,
            )
            os._exit(1 if number == failing else 0)

    failed = 0
    for _ in range(count):
        _, status = os.wait()
        if os.waitstatus_to_exitcode(status) != 0:
            failed += 1

    print(f"parent: children={count} failed={failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
```

Ребёнок завершается через `os._exit`, а не `sys.exit`: он не должен выполнять
обработчики выхода родителя. По той же причине его `print` идёт с `flush=True` —
`os._exit` не сбрасывает буфер вывода.

### H5

`disk-alert.sh`:

```bash
#!/usr/bin/env bash

set -uo pipefail

threshold="$1"
status=0

while read -r source used target; do
  if [ "${used%\%}" -gt "$threshold" ]; then
    echo "$source $used $target"
    status=1
  fi
done < <(df --output=source,pcent,target -x tmpfs -x devtmpfs -x squashfs \
  | tail -n +2)

exit "$status"
```

`-x ТИП` исключает файловые системы по типу, `tail -n +2` убирает заголовок,
`${used%\%}` отрезает знак процента, чтобы сравнить значение как число.

### H6

`check-tools.sh`:

```bash
#!/usr/bin/env bash

set -uo pipefail

required='lscpu lsblk df lspci'
optional='nvidia-smi'
status=0

for tool in $required; do
  if command -v "$tool" > /dev/null; then
    echo "$tool found"
  else
    echo "$tool missing"
    status=1
  fi
done

for tool in $optional; do
  if command -v "$tool" > /dev/null; then
    echo "$tool found"
  else
    echo "$tool missing"
  fi
done

exit "$status"
```
