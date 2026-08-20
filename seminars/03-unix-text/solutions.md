# Примеры решений

## База

### B1

```bash
wc -l -w -c assets/train.log > size.txt
cat size.txt
```

### B2

```bash
head -n 3 assets/train.log > head-tail.txt
tail -n 2 assets/train.log >> head-tail.txt
```

### B3

```bash
grep -n ERROR assets/train.log > errors.txt
grep -c ERROR assets/train.log > errors-count.txt
```

### B4

```bash
grep -v INFO assets/train.log > problems.txt
grep -vc INFO assets/train.log >> problems.txt
```

### B5

```bash
tail -n +2 assets/students.csv | cut -d, -f2 | sort -u > groups.txt
```

### B6

```bash
find assets/project -type f -name '*.py' | sort > python-files.txt
```

### B7

```bash
grep -cE '^Иванов' assets/contacts.txt         # ^ — привязка к началу строки
grep -cE 'example\.org$' assets/contacts.txt   # $ — к концу; точка экранирована
```

Без `\.` точка означала бы «любой символ», и шаблон совпал бы, например, с
`exampleXorg`.

## Среднее

### M1

```bash
tail -n +2 assets/students.csv \
  | sort -t, -k3,3nr \
  | head -n 3 > top3.txt
```

### M2

```bash
tail -n +2 assets/students.csv \
  | cut -d, -f2 \
  | sort \
  | uniq -c \
  | sort -k1,1nr -k2,2 > group-sizes.txt
```

`sort -k1,1nr -k2,2` сортирует по числу по убыванию, а при равных числах — по
имени группы: результат не зависит от порядка строк во входном файле.

### M3

```bash
grep -oE 'loss=[0-9.]+' assets/train.log \
  | cut -d= -f2 \
  | sort -n > loss-all.txt

{
  echo "min=$(head -n 1 loss-all.txt)"
  echo "max=$(tail -n 1 loss-all.txt)"
} > loss.txt
```

### M4

```bash
diff -u assets/config-old.txt assets/config-new.txt > config.diff

{
  echo "added=$(grep -c '^+[^+]' config.diff)"
  echo "removed=$(grep -c '^-[^-]' config.diff)"
} > config-summary.txt
```

Шаблоны `^+[^+]` и `^-[^-]` пропускают заголовки `+++` и `---`.

### M5

```bash
grep -Fxvf assets/config-old.txt assets/config-new.txt > only-new.txt
```

`-f` берёт шаблоны из файла, `-F` сравнивает их как обычный текст, `-x`
требует совпадения строки целиком, `-v` оставляет несовпавшие строки.

### M6

```bash
grep -rn TODO assets/project | sort > todo-all.txt
grep -rn --include='*.py' TODO assets/project | sort > todo-python.txt
```

### M7

```bash
grep -oE '[0-9]{2} ?[0-9]{2} [0-9]{6}' assets/contacts.txt > passports.txt
wc -l < passports.txt

grep -vE '[0-9]{2} ?[0-9]{2} [0-9]{6}' assets/contacts.txt
```

`?` относится к предыдущему элементу — к пробелу — и делает его необязательным,
поэтому одно выражение покрывает обе формы записи. `-o` печатает только
совпавшую часть, `-v` с тем же шаблоном отвечает на обратный вопрос.

## Сложное

### H1

`log-report.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

log="$1"

echo "lines=$(wc -l < "$log")"
echo "errors=$(grep -c ERROR "$log" || true)"
echo "warnings=$(grep -c WARN "$log" || true)"
echo "last_epoch=$(grep -oE 'epoch=[0-9]+' "$log" | cut -d= -f2 | sort -n | tail -n 1)"
```

`grep -c` возвращает ненулевой код, когда совпадений нет; без `|| true` скрипт
с `set -e` завершился бы на пустом логе.

### H2

`top-groups.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

file="$1"
count="$2"

tail -n +2 "$file" \
  | cut -d, -f2 \
  | sort \
  | uniq -c \
  | sort -k1,1nr -k2,2 \
  | head -n "$count"
```

### H3

`check-csv.sh`:

```bash
#!/usr/bin/env bash

set -uo pipefail

file="$1"
bad=$(grep -nvE '^[^,]*,[^,]*,[^,]*$' "$file" || true)

if [ -n "$bad" ]; then
  echo "$bad"
  exit 1
fi
```

Шаблон `^[^,]*,[^,]*,[^,]*$` описывает строку ровно с двумя запятыми, `-v`
оставляет непохожие строки, `-n` добавляет их номера.

### H4

```bash
find assets/project -type f -name '*.csv' -print0 \
  | xargs -0 wc -l \
  | tail -n 1 > csv-lines.txt

find assets/project -type f -name '*.csv' \
  | xargs wc -l 2> unsafe.txt

cat csv-lines.txt unsafe.txt
```

`-print0` разделяет пути нулевым байтом, `xargs -0` читает их так же. Без этой
пары `old data.csv` разбивается по пробелу на `old` и `data.csv`.

### H5

```bash
tr -cs '[:alpha:]' '\n' < assets/train.log \
  | tr '[:upper:]' '[:lower:]' \
  | grep -v '^$' \
  | sort \
  | uniq -c \
  | sort -k1,1nr -k2,2 \
  | head -n 5 > top-words.txt
```

`tr -cs '[:alpha:]' '\n'` заменяет всё, кроме букв, на перевод строки и
сжимает повторы, поэтому каждое слово оказывается на своей строке.

### H6

```bash
rm -rf ~/seminar-03/project-copy
cp -r assets/project ~/seminar-03/project-copy

grep -rn TODO ~/seminar-03/project-copy | sort > by-grep.txt
rg -n TODO ~/seminar-03/project-copy | sort > by-rg.txt
diff by-grep.txt by-rg.txt

printf 'TODO: скрытая заметка\n' > ~/seminar-03/project-copy/.notes.txt

grep -rn TODO ~/seminar-03/project-copy | wc -l          # 4
rg -n TODO ~/seminar-03/project-copy | wc -l             # 3
rg -n --hidden TODO ~/seminar-03/project-copy | wc -l    # 4
```

`rg` по умолчанию пропускает скрытые файлы, а внутри git-репозитория — ещё и
пути из `.gitignore`. `grep -r` таких правил не знает и читает всё. Флаг
`--hidden` возвращает скрытые файлы в поиск, `-uu` снимает и остальные фильтры.
