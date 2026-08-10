# Примеры решений

Один рабочий вариант на задачу; студент вправе решить иначе, если результат
совпадает с тестовым примером. Все команды выполняются в `~/seminar-07/`.

Про `nc`: реализации различаются ключами. Здесь используется вариант из пакета
`netcat-openbsd` (стандартный в Ubuntu). Если `-z` не поддерживается, ту же
проверку даёт `timeout 3 bash -c '</dev/tcp/ХОСТ/ПОРТ'`.

## База

### B1. Паспорт сети

```bash
cd ~/seminar-07 || exit 1
{
    echo "--- интерфейсы и адреса ---"
    ip -brief address
    echo "--- шлюз по умолчанию ---"
    ip route show default
    echo "--- путь до 8.8.8.8 (интерфейс и src) ---"
    ip route get 8.8.8.8
    echo "--- как меня видит интернет ---"
    curl -s -m 5 https://ifconfig.me
    echo
} > net-passport.txt
cat net-passport.txt
```

### B2. Имя в адрес

```bash
cd ~/seminar-07 || exit 1
{
    echo "--- как это делают программы ---"
    getent hosts example.com
    echo "--- прямой запрос в DNS ---"
    dig example.com | sed -n '/ANSWER SECTION/,+2p'
    dig example.com | grep 'SERVER:'
} > dns.txt
cat dns.txt
```

Число перед `IN A` в ответе — TTL, время жизни записи в секундах: столько
резолвер имеет право держать её в кэше.

### B3. Достижимость

```bash
cd ~/seminar-07 || exit 1
ping -c 3 -W 2 example.com  > ping.txt 2>&1
ping -c 3 -W 2 192.0.2.1   >> ping.txt 2>&1
echo "example.com: ответы есть, 0% потерь, ~0.3 с." >> ping.txt
echo "192.0.2.1: 100% потерь, ~6 с — адрес не маршрутизируется." >> ping.txt
cat ping.txt
```

### B4. Свой сервер

```bash
cd ~/seminar-07 || exit 1
echo "привет из семинара 7" > index.html
nohup python3 -m http.server 8000 --bind 0.0.0.0 > server.log 2>&1 &
sleep 1
{
    ss -tlnp | grep ':8000'
    curl -s http://127.0.0.1:8000/
    curl -s -o /dev/null -w 'код ответа: %{http_code}\n' http://127.0.0.1:8000/
} > server.txt
cat server.txt
```

### B5. Три исхода

```bash
for target in "127.0.0.1:8000" "127.0.0.1:9" "192.0.2.1:80"; do
    host=${target%:*}
    port=${target##*:}
    start=$SECONDS
    out=$(nc -z -v -w 3 "$host" "$port" 2>&1 | tail -1)
    echo "$target -> $out ($((SECONDS - start)) c)"
done
```

Хост и порт разбираются в отдельные переменные намеренно: подстановка
`nc ... $target` с пробелом внутри переменной работает в bash, но ломается в
zsh, который не делает разбиения по словам.

### B6. Код ответа и заголовки

```bash
cd ~/seminar-07 || exit 1
{
    curl -sS -I -m 5 https://example.com | head -4
    curl -s -o /dev/null -m 5 -w 'существующая: %{http_code}\n' https://example.com/
    curl -s -o /dev/null -m 5 -w 'выдуманная:   %{http_code}\n' https://example.com/net-2026
} > http.txt
cat http.txt
```

### B7. Кто занял порт

```bash
cd ~/seminar-07 || exit 1
ss -tlnp | grep ':8000' > who-holds-8000.txt
pid=$(ss -tlnpH 'sport = :8000' | grep -oP 'pid=\K[0-9]+' | head -1)
echo "PID: $pid" >> who-holds-8000.txt
tr '\0' ' ' < "/proc/$pid/cmdline" >> who-holds-8000.txt
echo >> who-holds-8000.txt
cat who-holds-8000.txt
```

В `/proc/<pid>/cmdline` аргументы разделены нулевыми байтами, поэтому вывод
пропускается через `tr`.

## Среднее

### M1. Локально работает, снаружи нет

```bash
pkill -f "http.server 8000"
sleep 1
cd ~/seminar-07 || exit 1
nohup python3 -m http.server 8000 --bind 127.0.0.1 > server.log 2>&1 &
sleep 1
MY_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K\S+')
ss -tlnp | grep ':8000'
curl -s -m 3 http://127.0.0.1:8000/     || echo "петля: нет ответа"
curl -s -m 3 "http://$MY_IP:8000/"      || echo "внешний адрес: нет ответа"
```

Объяснение: `ss` показывает открытый порт в обоих случаях, потому что порт
действительно открыт — отличается только адрес привязки в колонке
`Local Address:Port`. Сокет с адресом `127.0.0.1` принимает соединения лишь
через петлю; пакет, пришедший на внешний интерфейс, до него не доходит, и ядро
отвечает отправителю RST — тот самый `Connection refused`.

### M2. Диагноз по симптому

Содержимое `diagnosis.md`:

| Симптом | Ступень | Следующая команда | Что подтверждаем |
|---|---|---|---|
| `Name or service not known` | 2. имя | `getent hosts ИМЯ` | имя вообще не превращается в адрес |
| мгновенный `Connection refused` | 4. порт | `ss -tlnp \| grep ПОРТ` на сервере | процесса на порту нет или он на другом адресе |
| зависание и таймаут | 4. порт | `ping -c 2 -W 2 ХОСТ`, затем правила фаервола | пакеты отбрасываются молча |
| `404 Not Found` | 5. приложение | `curl -I АДРЕС` | сеть в порядке, отвечает сам сервис |
| `ping` молчит, сайт открывается | 3. хост | `nc -z -v -w 3 ХОСТ 443` | ICMP режут, TCP при этом ходит |

### M3. Откуда программа берёт адрес

```bash
grep -w localhost /etc/hosts | head -2
echo "--- как ходят программы ---"
getent hosts localhost
echo "--- публичный DNS ---"
dig +short localhost @1.1.1.1
echo "--- кто ответил без указания сервера ---"
dig localhost | grep -E 'SERVER:|^localhost'
```

`getent hosts localhost` возвращает адрес петли, а публичный сервер `1.1.1.1` не
возвращает ничего: имени `localhost` в глобальном DNS нет. Программы берут адрес
из строки `127.0.0.1 localhost` файла `/etc/hosts` — `getaddrinfo` читает его
первым и, найдя запись, в DNS уже не идёт.

Ответ на вторую часть: `dig +short localhost` без `@` тоже возвращает
`127.0.0.1`, но это не DNS из интернета. Строка `SERVER: 127.0.0.53#53`
показывает, что ответил локальный stub-резолвер `systemd-resolved`, который
синтезирует `localhost` самостоятельно. Отсюда правило: у `dig` всегда полезно
смотреть, **какой именно** резолвер ответил.

Замечание: на машине с настроенным IPv6 `getent hosts localhost` может вернуть
`::1` вместо `127.0.0.1` — это тот же адрес петли, только в другом семействе.

### M4. Где тормозит

```bash
FMT='%{time_namelookup}\t%{time_connect}\t%{time_appconnect}\t%{time_starttransfer}\t%{time_total}\n'
printf 'сайт\t\t\tимя\tсоед.\tTLS\t1-й байт\tвсего\n'
for site in https://example.com https://ya.ru https://github.com; do
    printf '%-22s ' "$site"
    curl -s -o /dev/null -m 10 -w "$FMT" "$site"
done
echo "--- повторный замер того же сайта ---"
curl -s -o /dev/null -m 10 -w "$FMT" https://example.com
```

Разбор: `time_namelookup` при повторном вызове падает почти до нуля — ответ
DNS закэширован локальным резолвером на время TTL. Разность
`time_appconnect - time_connect` — цена TLS-рукопожатия, а
`time_starttransfer - time_appconnect` — время, которое думало само
приложение на той стороне.

### M5. Чекер порта

Файл `check-port.sh`:

```bash
#!/usr/bin/env bash
# Использование: ./check-port.sh ХОСТ ПОРТ
# Коды возврата: 0 — open, 1 — refused, 2 — timeout.
set -u

out=$(nc -z -v -w 3 "$1" "$2" 2>&1)
case "$out" in
    *succeeded*|*Connected*) echo open;    exit 0 ;;
    *refused*)               echo refused; exit 1 ;;
    *)                       echo timeout; exit 2 ;;
esac
```

Проверка:

```bash
chmod +x check-port.sh
./check-port.sh 127.0.0.1 8000 ; echo "код=$?"
./check-port.sh 127.0.0.1 9    ; echo "код=$?"
./check-port.sh 192.0.2.1 80   ; echo "код=$?"
```

### M6. Порт уже занят

```bash
cd ~/seminar-07 || exit 1
python3 -m http.server 8000 --bind 0.0.0.0 2>&1 | tail -2
ss -tlnp | grep ':8000'
pid=$(ss -tlnpH 'sport = :8000' | grep -oP 'pid=\K[0-9]+' | head -1)
echo "мешает процесс $pid"
kill "$pid"
sleep 1
ss -tlnp | grep ':8000' || echo "порт 8000 свободен"
```

Вторая попытка падает с `OSError: [Errno 98] Address already in use`: два
процесса не могут слушать одну пару «адрес + порт».

### M7. HTTP руками

```bash
printf 'GET / HTTP/1.0\r\n\r\n' | nc -w 3 127.0.0.1 8000 | head -6
```

В ответе: `HTTP/1.0 200 OK` — версия протокола и код,
`Server: SimpleHTTP/0.6 Python/3.12.3` — название сервера. Обратите внимание на
пустую строку в запросе: именно она сообщает серверу, что заголовки кончились,
и без неё он будет ждать продолжения до таймаута.

## Сложное

### H1. Чёрный ящик

```bash
cd ~/seminar-07 || exit 1
bash /путь/к/seminars/07-unix-net/assets/broken-lab.sh start
for t in 127.0.0.1:8101 127.0.0.1:8102 127.0.0.1:8103 127.0.0.1:8105; do
    host=${t%:*}
    port=${t##*:}
    printf '%-20s ' "$t"
    curl -sS -m 3 -o /dev/null -w 'код=%{http_code} ' "http://$t/health" 2>/dev/null
    nc -z -v -w 3 "$host" "$port" 2>&1 | tail -1
done
ss -tlnp | grep -E ':81[0-9][0-9]'
```

Ожидаемый отчёт `blackbox.md`:

| Цель | Симптом | Ступень | На чём основан диагноз | Что чинить |
|---|---|---|---|---|
| svc-a | код 200 | — | все ступени пройдены | ничего, контрольная цель |
| svc-b | мгновенный refused | 4. порт | `ss` порта 8102 не показывает вовсе | сервис не запущен |
| svc-c | мгновенный refused | 4. порт | `ss` показывает живой процесс на соседнем 8104 | объявлен не тот порт |
| svc-d | соединение есть, код 404 | 5. приложение | TCP установлен, ответ осмысленный | нет файла `health` в сервисе |
| svc-e | таймаут ~3 с | 3. хост | ответа нет вообще, адрес из RFC 5737 | неверный адрес, а не сервис |
| svc-f | refused по внешнему адресу, 200 по петле | 4. порт | в `ss` привязка `127.0.0.1:8107` | `--bind 0.0.0.0` либо туннель |

Сверка: `broken-lab.sh answers`. Снять стенд: `broken-lab.sh stop`.

### H2. Протокол диагностики

Пример протокола для `svc-f` (файл `protocol.md`):

```
Цель: http://10.0.2.15:8107/health — «не открывается».

1. Свой узел.  ip route get 10.0.2.15
   -> src 10.0.2.15, dev lo — адрес принадлежит мне самому. Идём дальше.
2. Имя.        адрес задан числом, разрешение имени не участвует. Пропускаем.
3. Хост.       ping -c 2 -W 2 10.0.2.15
   -> 0% packet loss. Хост жив. Идём дальше.
4. Порт.       nc -z -v -w 3 10.0.2.15 8107
   -> Connection refused, мгновенно. НАШЛИ: до хоста дошли, слушателя нет.
   Уточняем:   ss -tlnp | grep 8107
   -> 127.0.0.1:8107, процесс python3 жив.
   Проверяем:  curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8107/health
   -> 200. Через петлю сервис отвечает.

Причина: сервис привязан к 127.0.0.1, поэтому доступен только изнутри машины.
Починка: перезапустить с --bind 0.0.0.0, либо оставить как есть и пробросить
порт по SSH-туннелю, если сервис не должен быть виден сети.
```

Ключ к оценке: по протоколу видно, что проверка шла снизу вверх и остановилась
на первой ступени, ответившей не так, как ожидалось; каждый шаг подтверждён
выводом команды, а не рассуждением.

### H3. DROP против REJECT

На своей машине (сервер привязан к `0.0.0.0`):

```bash
sudo ufw status verbose
sudo ufw deny 8000/tcp          # молча отбрасывать
```

С машины соседа:

```bash
start=$SECONDS
nc -z -v -w 5 АДРЕС_СЕРВЕРА 8000 2>&1 | tail -1
echo "заняло $((SECONDS - start)) c"
```

Возвращаемся на свою машину и меняем правило:

```bash
sudo ufw delete deny 8000/tcp
sudo ufw reject 8000/tcp        # отвечать явным отказом
```

Сосед повторяет замер, после чего убираем правило:

```bash
sudo ufw delete reject 8000/tcp
sudo ufw status verbose
```

Результат: `deny` даёт зависание на 5 секунд и `timed out`; `reject` — мгновенный
`Connection refused`, внешне неотличимый от незапущенного сервиса. Отсюда вывод
для диагностики: `refused` не доказывает, что сервис не запущен, — он лишь
означает, что кто-то ответил отказом, и этим «кем-то» может быть фаервол.

Наблюдение про петлю: если стучаться с той же машины, правило не сработает.
Трафик к собственному адресу идёт через интерфейс `lo`, а `ufw` по умолчанию
пропускает всё на `lo` правилом `-i lo -j ACCEPT` до проверки пользовательских
правил.

### H4. Наблюдатель доступности

Файл `watch-targets.sh` (использует `check-port.sh` из M5):

```bash
#!/usr/bin/env bash
# Использование: ./watch-targets.sh targets.txt journal.log
# Формат файла целей: по одной строке «хост порт».
set -u

targets_file=$1
journal=$2
declare -A previous

while true; do
    while read -r host port; do
        [ -z "${host:-}" ] && continue
        state=$(./check-port.sh "$host" "$port")
        stamp=$(date --iso-8601=seconds)
        echo "$stamp $host:$port $state" >> "$journal"
        was=${previous["$host:$port"]:-}
        if [ -n "$was" ] && [ "$was" != "$state" ]; then
            echo "ИЗМЕНЕНИЕ: $host:$port $was -> $state"
        fi
        previous["$host:$port"]=$state
    done < "$targets_file"
    sleep 5
done
```

Демонстрация:

```bash
printf '127.0.0.1 8000\n127.0.0.1 9\n' > targets.txt
chmod +x watch-targets.sh
./watch-targets.sh targets.txt journal.log &
sleep 12
pkill -f "http.server 8000"     # роняем сервис на глазах у наблюдателя
sleep 12
tail -6 journal.log
```

В журнале видно переход `open` → `refused`, а в терминале — строка
`ИЗМЕНЕНИЕ: 127.0.0.1:8000 open -> refused`.

### H5. Чтение `curl -v`

```bash
curl -v -s -o /dev/null -m 5 http://127.0.0.1:8000/ 2>&1 | head -12
```

Разбор вывода по ступеням:

```
*   Trying 127.0.0.1:8000...                     <- (3) пробуем достучаться до хоста
* Connected to 127.0.0.1 (127.0.0.1) port 8000   <- (4) TCP-соединение установлено
> GET / HTTP/1.1                                 <- (5) отправили запрос приложению
> Host: 127.0.0.1:8000
> User-Agent: curl/8.5.0
>
< HTTP/1.1 200 OK                                <- (5) приложение осмысленно ответило
< Server: SimpleHTTP/0.6 Python/3.12.3
```

Ступени 2 (имя) в выводе нет, потому что адрес задан числом и разрешать было
нечего: при запросе к `http://example.com/` перед строкой `Trying` появилась бы
запись о разрешении имени.

Ступени TLS нет, потому что схема `http://`, а не `https://`. Для HTTPS между
строками `Connected to` и `> GET` появился бы блок с рукопожатием: обмен
`TLS handshake`, выбранная версия протокола и шифр, проверка сертификата.
Именно этот блок измеряется как `time_appconnect` в задаче M4.

### H6. Сервер на голом TCP

```bash
pkill -f "http.server 8000"
sleep 1
printf 'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nConnection: close\r\n\r\nпривет из nc\n' | nc -l 8000 -q 1 &
sleep 1
curl -s -m 3 http://127.0.0.1:8000/
```

Проверка кода ответа (`nc` обслуживает одно соединение, поэтому перед вторым
запросом сервер поднимается заново):

```bash
printf 'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nConnection: close\r\n\r\nпривет из nc\n' | nc -l 8000 -q 1 &
sleep 1
curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/
```

Заголовок `Connection: close` здесь обязателен: он разрешает клиенту считать
тело до закрытия соединения, и `Content-Length` можно не указывать.

Объяснение: HTTP — это просто текст, передаваемый по TCP-соединению. Клиенту
безразлично, что за программа слушает порт: пока она присылает корректную
строку статуса, заголовки, пустую строку и тело, для `curl` и браузера это
полноценный веб-сервер. Ровно поэтому диагностика делится на ступени —
«соединение установилось» и «сервис ответил осмысленно» это разные события,
и ломаться они могут независимо.
