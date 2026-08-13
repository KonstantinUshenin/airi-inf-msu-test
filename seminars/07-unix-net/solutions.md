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
    dig example.com +noall +answer
    dig example.com | grep 'SERVER:'
} > dns.txt
cat dns.txt
```

Число перед `IN A` в ответе — TTL, время жизни записи в секундах: столько
резолвер имеет право держать её в кэше. Ключи `+noall +answer` печатают секцию
ответа целиком, сколько бы записей в ней ни оказалось: у сайтов за CDN их
обычно несколько, и вырезание фиксированного числа строк потеряло бы часть.

### B3. Достижимость

```bash
cd ~/seminar-07 || exit 1
start=$SECONDS
ping -c 3 -W 2 example.com > ping.txt 2>&1
echo "example.com: занял $((SECONDS - start)) c" >> ping.txt

start=$SECONDS
ping -c 3 -W 2 192.0.2.1 >> ping.txt 2>&1
echo "192.0.2.1: занял $((SECONDS - start)) c" >> ping.txt

echo "Разница: у первого 0% потерь и есть времена отклика," >> ping.txt
echo "у второго 100% потерь — ответа нет ни одного." >> ping.txt
cat ping.txt
```

На замере: отвечающий адрес занимает около двух-трёх секунд (три пакета с
паузой в секунду), неотвечающий — на секунду-две дольше, потому что к тем же
паузам добавляется ожидание ответа на последний пакет (`-W 2`). Точные числа
зависят от версии `ping` и настроек системы, поэтому их и меряют, а не
переписывают из методички. Важна качественная разница: в первом случае ответы
есть, во втором — ни одного.

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

Хост и порт разбираются в отдельные переменные потому, что `nc` ждёт их двумя
аргументами: `nc 127.0.0.1:8000` завершится с `missing port number`.
`${target%:*}` отрезает от строки всё начиная с последнего двоеточия, а
`${target##*:}` — наоборот, всё до него включительно.

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
pid=$(ss -tlnp | grep ':8000' | grep -oP 'pid=\K[0-9]+' | head -1)
echo "PID: $pid" >> who-holds-8000.txt
ps -p "$pid" -o cmd= >> who-holds-8000.txt
cat who-holds-8000.txt
```

`ps -p PID -o cmd=` печатает командную строку процесса без заголовка колонки —
тот же `ps` из семинара 2. Та же строка лежит в файле `/proc/<pid>/cmdline`, но
аргументы там разделены нулевыми байтами, и читать её приходится через
`tr '\0' ' ' < /proc/$pid/cmdline`.

Выражение `grep -oP 'pid=\K[0-9]+'` вытаскивает число после `pid=`: `-o` печатает
только совпадение, `-P` включает перловые регулярки, `\K` выбрасывает из
совпадения всё, что стояло до него.

### B8. Паспорт сертификата

```bash
cd ~/seminar-07 || exit 1
{
    timeout 15 openssl s_client -connect example.com:443 -servername example.com \
        < /dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
    echo "корневых УЦ в системе: $(grep -c 'BEGIN CERTIFICATE' /etc/ssl/certs/ca-certificates.crt)"
    echo "Верим не сайту, а цепочке подписей: сертификат подписан промежуточным УЦ,"
    echo "тот — корневым, а корневой уже лежит в системном хранилище."
} > tls.txt
cat tls.txt
```

Ключ `-servername` обязателен: на одном адресе живёт много сайтов, и без имени
сервер не поймёт, чей сертификат предъявлять (это то самое поле SNI).
Проверяются при этом три вещи сразу — подпись цепочки, имя в сертификате и срок
действия; провал любой из них разрывает соединение.

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
curl -s -m 3 http://127.0.0.1:8000/     || echo "loopback: нет ответа"
curl -s -m 3 "http://$MY_IP:8000/"      || echo "внешний адрес: нет ответа"
```

Объяснение: `ss` показывает открытый порт в обоих случаях, потому что порт
действительно открыт — отличается только адрес привязки в колонке
`Local Address:Port`. Сокет с адресом `127.0.0.1` принимает соединения лишь
через loopback; пакет, пришедший на внешний интерфейс, до него не доходит, и ядро
отвечает отправителю RST — тот самый `Connection refused`.

### M2. Диагноз по симптому

Содержимое `diagnosis.md`:

| Симптом | Ступень | Команда | Вывод подтверждает ступень | Вывод её исключает |
|---|---|---|---|---|
| (а) `Name or service not known` | 2. имя | `getent hosts ИМЯ` | пусто: имя действительно не превращается в адрес, смотрим `/etc/hosts` и `/etc/resolv.conf` | адрес получен: имя резолвится, дело было в опечатке или в кэше клиента |
| (б) мгновенный `Connection refused` | 4. порт | `ss -tlnp \| grep ПОРТ` на сервере | пусто: слушателя нет — сервис не запущен или занял другой порт | порт слушается: значит, отказ прислал не он, а фаервол с REJECT — идём в `ufw status` |
| (в) зависание и таймаут | 3–4. хост или порт | `ping -c 2 -W 2 ХОСТ` | молчит и `ping`: ниже, ступень 3 — адрес, маршрут, выключенная машина | хост отвечает: ступень 3 в порядке, молча отбрасывают именно порт, смотрим правила фаервола |
| (г) `SSL certificate problem` | 5. приложение | `openssl s_client -connect ХОСТ:443 -servername ИМЯ` | ошибка проверки: сертификат самоподписанный, просрочен или не на это имя | `Verify return code: 0`: с сертификатом всё в порядке, дело в клиенте — старый набор корневых УЦ или сбитые часы |
| (д) соединение мгновенно, ответа нет 30 с | 5. приложение | `curl -w '%{time_connect} %{time_total}'`, затем лог сервиса | в логе запрос есть: приложение его получило и думает — смотрим нагрузку и зависимости | в логе пусто: до приложения не дошло, возвращаемся на ступень порта |
| (е) `504 Gateway Timeout` | 5. приложение | логи обратного прокси и приложения | в логе приложения запрос есть и он долгий: тормозит само приложение | в логе приложения запроса нет: прокси до него не достучался — проблема между прокси и приложением |

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

`getent hosts localhost` возвращает адрес loopback, а публичный сервер `1.1.1.1` не
возвращает ничего: имени `localhost` в глобальном DNS нет. Программы берут адрес
из строки `127.0.0.1 localhost` файла `/etc/hosts` — `getaddrinfo` читает его
первым и, найдя запись, в DNS уже не идёт.

Ответ на вторую часть: `dig +short localhost` без `@` тоже возвращает
`127.0.0.1`, но это не DNS из интернета. Строка `SERVER: 127.0.0.53#53`
показывает, что ответил локальный stub-резолвер `systemd-resolved`, который
синтезирует `localhost` самостоятельно. Отсюда правило: у `dig` всегда полезно
смотреть, **какой именно** резолвер ответил.

Замечание: на машине с настроенным IPv6 `getent hosts localhost` может вернуть
`::1` вместо `127.0.0.1` — это тот же адрес loopback, только в другом семействе.

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
python3 -m http.server 8000 --bind 0.0.0.0 2>&1 | grep -i 'address already in use'
ss -tlnp | grep ':8000'
pid=$(ss -tlnp | grep ':8000' | grep -oP 'pid=\K[0-9]+' | head -1)
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

### M8. Три таймаута

```bash
cd ~/seminar-07 || exit 1
FMT='соединение %{time_connect} с, всего %{time_total} с, '

echo -n "(а) недостижимый адрес:  "
curl -s -o /dev/null --connect-timeout 3 --max-time 30 -w "$FMT" http://192.0.2.1/
echo "код $?"

nc -l 127.0.0.1 8001 > /dev/null 2>&1 &
srv=$!
sleep 1
echo -n "(б) сервер молчит:       "
curl -s -o /dev/null --connect-timeout 3 --max-time 5 -w "$FMT" http://127.0.0.1:8001/
echo "код $?"
kill "$srv" 2>/dev/null

timeout 2 nc -l 127.0.0.1 8001 > /dev/null 2>&1 &
sleep 1
echo -n "(в) сервер закрыл сам:   "
curl -s -o /dev/null --connect-timeout 3 --max-time 30 -w "$FMT" http://127.0.0.1:8001/
echo "код $?"
```

Содержимое `timeouts.md`:

| Случай | `time_connect` | Всего | Код `curl` | Кто сдался | Ступень, где чинить |
|---|---|---|---|---|---|
| (а) недостижимый адрес | 0 | 3 с (`--connect-timeout`) | 28 | клиент | 3–4: адрес, маршрут, фаервол |
| (б) сервер принял и молчит | ~0.0002 с | 5 с (`--max-time`) | 28 | клиент | 5: логи и нагрузка сервиса |
| (в) сервер закрыл соединение | ~0.0002 с | ~1 с | 52 | сервер | 5: таймауты на той стороне |

Главное различие — в `time_connect`. Ноль означает, что TCP-соединения не было
вовсе, и это сетевая поломка. Мгновенный ненулевой `time_connect` доказывает
обратное: сеть отработала, молчит приложение. Код 52 (`Empty reply from
server`) отличает третий случай: ожидание прекратил не клиент, поэтому общее
время меньше разрешённого `--max-time`.

### M9. Свой HTTPS и недоверенный сертификат

```bash
cd ~/seminar-07 || exit 1
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
    -keyout key.pem -out cert.pem -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost" 2>/dev/null
openssl x509 -in cert.pem -noout -subject -issuer

openssl s_server -accept 8443 -cert cert.pem -key key.pem -www > s_server.log 2>&1 &
sleep 1
curl -sS -m 5 -o /dev/null https://localhost:8443/
echo "обычный вызов: код возврата $?"
curl -sk -m 5 -o /dev/null -w 'с -k:       %{http_code}\n' https://localhost:8443/
curl -s -m 5 --cacert cert.pem -o /dev/null -w 'с --cacert: %{http_code}\n' https://localhost:8443/
pkill -f 's_server -accept 8443'
```

Разбор. В нашем сертификате `subject` и `issuer` совпадают (`CN = localhost`):
он подписан собственным ключом, то есть выдан сам себе. У `example.com` `issuer`
— промежуточный УЦ, чья подпись проверяется по цепочке до корня из системного
хранилища.

Первый исход — не поломка, а сработавшая защита. Сервер жив, шифрование
работает, отказ произошёл именно на проверке подлинности: клиент не может
отличить наш самоподписанный сертификат от сертификата злоумышленника, который
встал посередине, и поэтому отказывается разговаривать. Ключ `-k` снимает
проверку целиком и возвращает уязвимость к MITM; `--cacert` расширяет доверие
ровно на один известный сертификат, все прочие остаются недоверенными.

## Сложное

### H1. Чёрный ящик

```bash
cd ~/seminar-07 || exit 1
bash /путь/к/seminars/07-unix-net/assets/broken-lab.sh start
MY_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K\S+')
for t in 127.0.0.1:8101 127.0.0.1:8102 127.0.0.1:8103 127.0.0.1:8105 \
         192.0.2.1:8106 "$MY_IP:8107"; do
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
| svc-f | refused по внешнему адресу, 200 по loopback | 4. порт | в `ss` привязка `127.0.0.1:8107` | `--bind 0.0.0.0` либо туннель |

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
   -> 200. Через loopback сервис отвечает.

Причина: сервис привязан к 127.0.0.1, поэтому доступен только изнутри машины.
Починка: перезапустить с --bind 0.0.0.0, либо оставить как есть и пробросить
порт по SSH-туннелю, если сервис не должен быть виден сети.
```

Ключ к оценке: по протоколу видно, что проверка шла снизу вверх и остановилась
на первой ступени, ответившей не так, как ожидалось; каждый шаг подтверждён
выводом команды, а не рассуждением.

### H3. DROP против REJECT

На своей машине (сервер привязан к `0.0.0.0`). Сначала включаем фаервол — без
этого правила добавятся, но фильтровать не будут:

```bash
sudo ufw status verbose         # скорее всего Status: inactive
sudo ufw allow OpenSSH          # если ходите на машину по ssh — обязательно
sudo ufw enable
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

Сосед повторяет замер, после чего убираем правило и возвращаем фаервол в
исходное состояние:

```bash
sudo ufw delete reject 8000/tcp
sudo ufw disable                # если до опыта он был inactive
sudo ufw status verbose
```

Результат: `deny` даёт зависание на 5 секунд и `timed out`; `reject` — мгновенный
`Connection refused`, внешне неотличимый от незапущенного сервиса. Отсюда вывод
для диагностики: `refused` не доказывает, что сервис не запущен, — он лишь
означает, что кто-то ответил отказом, и этим «кем-то» может быть фаервол.

Наблюдение про loopback: если стучаться с той же машины, правило не сработает.
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
< HTTP/1.0 200 OK                                <- (5) приложение осмысленно ответило
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

### H7. Что видно в трафике

Нужны оба своих сервера: HTTP на порту 8000 и HTTPS на 8443. Если после
предыдущих задач они уже сняты, поднимаем заново — первый строкой ниже, второй
во втором блоке. Снимаем трафик к каждому и ищем в дампе один и тот же токен:

```bash
cd ~/seminar-07 || exit 1
pkill -f "http.server 8000"
nohup python3 -m http.server 8000 --bind 127.0.0.1 > server.log 2>&1 &
sleep 1
sudo timeout 5 tcpdump -i lo -A -n -q 'tcp port 8000' > dump-http.txt 2>/dev/null &
sleep 1
curl -s -H 'Authorization: Bearer SUPERSECRET123' http://127.0.0.1:8000/ > /dev/null
sleep 5
echo "--- HTTP ---"
grep -a -E 'GET /|Authorization' dump-http.txt
```

```bash
cd ~/seminar-07 || exit 1
openssl s_server -accept 8443 -cert cert.pem -key key.pem -www > s_server.log 2>&1 &
sleep 1
sudo timeout 5 tcpdump -i lo -A -n -q 'tcp port 8443' > dump-tls.txt 2>/dev/null &
sleep 1
curl -sk -m 5 -H 'Authorization: Bearer SUPERSECRET123' https://localhost:8443/ > /dev/null
sleep 5
echo "--- HTTPS ---"
echo "токен в дампе:     $(grep -ac SUPERSECRET dump-tls.txt) раз"
echo "имя сервера (SNI): $(grep -ac localhost dump-tls.txt) раз"
pkill -f 's_server -accept 8443'
```

Отчёт `sniff.md`. В HTTP-дампе читаются и строка запроса `GET / HTTP/1.1`, и
заголовок `Authorization: Bearer SUPERSECRET123` — расшифровывать нечего,
данные идут открытым текстом. В TLS-дампе токен не встречается ни разу, зато
один раз встречается имя `localhost`.

Имя сервера передаётся открытым текстом в самом начале рукопожатия, в
расширении **SNI** (Server Name Indication) сообщения `ClientHello`: сертификат
ещё не получен, шифрование не согласовано, а сервер уже должен понять, чей из
своих сертификатов предъявлять. Сколько раз имя попадётся в дампе, зависит от
версии протокола: в TLS 1.3 сертификат уже шифруется и остаётся только SNI, в
TLS 1.2 сертификат идёт открытым текстом и имя встретится ещё и в нём. Помимо имени наблюдателю остаются видны факт
соединения, адреса и порты сторон, объём и время передачи; скрыты путь,
заголовки, куки и тела запроса и ответа.

Оговорка про эксперимент: `-i lo` мы слушаем потому, что оба сервера свои и
локальные. В реальной сети точно так же выглядит трафик для любого, через чьё
оборудование он идёт, — точки доступа, провайдера, администратора сети.
