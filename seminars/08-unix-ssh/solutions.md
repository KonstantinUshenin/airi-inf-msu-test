# Примеры решений

Все решения работают в `~/seminar-08/`. Каталоги заводятся один раз:

```bash
mkdir -p ~/seminar-08/keys ~/seminar-08/ssh ~/seminar-08/logs ~/seminar-08/transfer
```

`course` — учебный сервер (`user@host` или псевдоним из `~/.ssh/config`),
`HOST` — его имя, `USER` — ваш логин на нём.

## База

### B1

```bash
cd ~/seminar-08 || exit 1
ssh -V > logs/ssh-client.txt 2>&1              # версия печатается в stderr
which ssh >> logs/ssh-client.txt
ssh -T -G student@server.example >> logs/ssh-client.txt   # -G: настройки без подключения
cat logs/ssh-client.txt
```

### B2

```bash
cd ~/seminar-08 || exit 1
ssh course '{ hostname; whoami; pwd; uname -a; cat /etc/os-release; }' \
  > logs/remote-system.txt 2> logs/remote-errors.txt
head -n 4 logs/remote-system.txt
```

### B3

```bash
cd ~/seminar-08 || exit 1
ssh course 'ls /etc/os-release /missing-file' \
  > logs/remote-stdout.txt 2> logs/remote-stderr.txt
echo "$?" > logs/remote-exit-code.txt          # код ls с сервера, а не код самого ssh-подключения
cat logs/remote-exit-code.txt logs/remote-stdout.txt logs/remote-stderr.txt
```

### B4

```bash
cd ~/seminar-08 || exit 1
echo 'local report' > transfer/local.txt
scp transfer/local.txt course:seminar08-file.txt
scp course:seminar08-file.txt transfer/returned.txt
wc -c transfer/local.txt transfer/returned.txt > logs/sizes.txt
cmp transfer/local.txt transfer/returned.txt && echo 'content: identical' > logs/verification.txt
cat logs/sizes.txt logs/verification.txt
```

### B5

```bash
cd ~/seminar-08 || exit 1
cat > ssh/course-config <<'EOF'
Host course
    HostName HOST
    User USER
    Port 22
EOF
chmod 600 ssh/course-config
ssh -T -F ssh/course-config -G course | grep -E '^(hostname|user|port) ' > logs/effective-config.txt
cat logs/effective-config.txt
```

### B6

```bash
cd ~/seminar-08 || exit 1
# двойные кавычки: $HOME раскрывает локальная оболочка, на сервер уедет готовый путь
ssh course "echo $HOME" > logs/quotes-double.txt
# одинарные: на сервер уедет буквальный $HOME, раскроет его удалённая оболочка
ssh course 'echo $HOME' > logs/quotes-single.txt
diff logs/quotes-double.txt logs/quotes-single.txt || echo 'пути разные — так и должно быть'
```

### B7

```bash
cd ~/seminar-08 || exit 1
eval "$(ssh-agent -s)" > /dev/null             # без eval переменные не попадут в текущую оболочку
ssh-add keys/course_ed25519
ssh-add -l > logs/agent-keys.txt               # отпечатки, которые агент готов предъявлять
cat logs/agent-keys.txt
ssh-agent -k > /dev/null                       # гасим агент
```

## Среднее

### M1

```bash
cd ~/seminar-08 || exit 1
ssh-keygen -q -t ed25519 -f keys/course_ed25519 -N '' -C 'course-key'
chmod 400 keys/course_ed25519                  # закрытый ключ — чтение только владельцу
ssh-keygen -lf keys/course_ed25519.pub > logs/key-fingerprint.txt
ls -l keys > logs/key-files.txt
cat logs/key-fingerprint.txt logs/key-files.txt
```

### M2

```bash
cd ~/seminar-08 || exit 1
ssh course 'tmux new-session -d -s course-worker "sleep 120"'
ssh course 'tmux list-sessions; tmux list-panes -t course-worker -F "#{pane_pid} #{pane_current_command}"' \
  > logs/tmux-running.txt
ssh course 'tmux kill-session -t course-worker'
ssh course 'tmux has-session -t course-worker' > logs/tmux-after.txt 2>&1 \
  || echo 'finished' >> logs/tmux-after.txt
cat logs/tmux-running.txt logs/tmux-after.txt
```

### M3

```bash
cd ~/seminar-08 || exit 1
mkdir -p sync/source
echo alpha > sync/source/a.txt
rsync -av sync/source/ course:seminar08-sync/ > logs/first-sync.txt
rsync -av sync/source/ course:seminar08-sync/ > logs/second-sync.txt   # второй прогон: передавать нечего
tail -n 3 logs/second-sync.txt
```

### M4

```bash
cd ~/seminar-08 || exit 1
rm -f ~/seminar-08/ssh/course-known-hosts      # чистый старт, чтобы записи не дублировались
ssh-keyscan -t ed25519 HOST >> ssh/course-known-hosts 2> logs/keyscan-errors.txt
ssh-keygen -F HOST -f ssh/course-known-hosts > logs/known-host.txt
cat logs/known-host.txt
```

### M5

```bash
cd ~/seminar-08 || exit 1
ssh -Tvvv course true > logs/connection.out 2> logs/connection-debug.txt
echo "$?" > logs/connection-exit-code.txt
grep -E 'Server host key|Offering public key|Authenticated to' logs/connection-debug.txt
```

### M6

```bash
cd ~/seminar-08 || exit 1
cat >> ssh/course-config <<'EOF'

Host lab
    HostName 10.0.0.7
    User USER
    ProxyJump course
EOF
# ProxyJump лучше входа в два приёма: сессия шифруется до lab, ключ на course не попадает,
# а scp/rsync/-L работают с lab как с обычным хостом
ssh -T -F ssh/course-config -G lab | grep -E '^(hostname|user|proxyjump) ' > logs/lab-effective.txt
cat logs/lab-effective.txt
```

### M7

```bash
cd ~/seminar-08 || exit 1
ssh-keygen -q -t ed25519 -N '' -C 'wrong' -f keys/wrong_key    # заведомо чужой ключ
# -F /dev/null: не читать ~/.ssh/config, иначе IdentityFile псевдонима подсунет правильный ключ,
# поэтому адрес сервера пишем полностью
ssh -vvv -F /dev/null -o BatchMode=yes -o IdentitiesOnly=yes -i keys/wrong_key USER@HOST true \
  > logs/fail.out 2> logs/fail-debug.txt
echo "код возврата: $?"                                        # 255 — клиент не смог войти
grep -E 'Offering public key|Authentications that can continue|Permission denied' logs/fail-debug.txt
```

## Сложное

### H1

```bash
cd ~/seminar-08 || exit 1
ssh-copy-id -i keys/course_ed25519.pub course
chmod 400 keys/course_ed25519
ssh-keygen -lf keys/course_ed25519.pub > logs/selected-key.txt
ssh -o IdentitiesOnly=yes -i keys/course_ed25519 course 'whoami' \
  > logs/remote-user.txt 2> logs/key-login-errors.txt
cat logs/selected-key.txt logs/remote-user.txt
```

### H2

```bash
cd ~/seminar-08 || exit 1
echo updated > sync/source/a.txt               # изменили
echo gamma > sync/source/c.txt                 # добавили
rm -f ~/seminar-08/sync/source/b.txt           # удалили
rsync -avni --delete sync/source/ course:seminar08-sync/ > logs/sync-plan.txt   # сначала план
rsync -avi --delete sync/source/ course:seminar08-sync/ > logs/sync-result.txt
ssh course 'ls -l seminar08-sync' > logs/remote-files.txt
cat logs/sync-plan.txt logs/remote-files.txt
```

### H3

```bash
cd ~/seminar-08 || exit 1
ssh -N -o ExitOnForwardFailure=yes -L 9000:127.0.0.1:8000 course \
  > logs/tunnel.out 2> logs/tunnel.err &
tunnel_pid=$!
sleep 2
curl -s http://127.0.0.1:9000 > logs/success.html                    # сервис доступен через туннель
ssh course 'kill -TERM "$(cat ~/http-server.pid)"' > logs/stop-service.txt 2>&1
curl -s http://127.0.0.1:9000 > logs/failed.html || echo "$?" > logs/failed-exit-code.txt   # обычно 56
kill -TERM "$tunnel_pid"
wait "$tunnel_pid" 2>/dev/null
```

### H4

```bash
cd ~/seminar-08 || exit 1
ssh course 'tmux new-session -d -s course-lab -n system "uname -a; sleep 300"'
ssh course 'tmux new-window -t course-lab -n worker "uptime; sleep 300"'
ssh course 'tmux list-windows -t course-lab' > logs/tmux-windows.txt
ssh course 'tmux capture-pane -p -t course-lab:system' > logs/system-pane.txt
ssh course 'tmux capture-pane -p -t course-lab:worker' > logs/worker-pane.txt
ssh course 'tmux kill-session -t course-lab'
cat logs/tmux-windows.txt logs/system-pane.txt logs/worker-pane.txt
```

### H5

```bash
cd ~/seminar-08 || exit 1
rsync -avn --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' \
  project/ course:project-backup/ > logs/backup-plan.txt          # сначала план
rsync -av --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' \
  project/ course:project-backup/ > logs/backup-result.txt
ls -laR project > logs/local-files.txt
ssh course 'ls -laR project-backup' > logs/remote-files.txt
grep -cE '\.git/|__pycache__/' logs/backup-plan.txt                # ожидаем 0
```

### H6

```bash
cd ~/seminar-08 || exit 1
python3 -m http.server 20080 --bind 127.0.0.1 > logs/local-service.log 2>&1 &
service_pid=$!
ssh -N -o ExitOnForwardFailure=yes -R 20090:127.0.0.1:20080 course \
  > logs/rtunnel.out 2> logs/rtunnel.err &
tunnel_pid=$!
sleep 2
ssh course 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:20090' > logs/remote-check.txt
kill -TERM "$tunnel_pid" "$service_pid"
cat logs/remote-check.txt
```

### H7

```bash
cd ~/seminar-08 || exit 1
sudo journalctl -u ssh --since '24 hours ago' --no-pager > logs/ssh-journal.txt
grep -c 'Failed password' logs/ssh-journal.txt > logs/failed-count.txt
grep -oE 'from [0-9.]+' logs/ssh-journal.txt | sort | uniq -c | sort -rn | head > logs/top-ips.txt
sudo fail2ban-client status sshd > logs/fail2ban-sshd.txt
# fail2ban тормозит перебор, но не спасает от украденного ключа или дыры в сервисе:
# базовая защита — вход только по ключам и PasswordAuthentication no
cat logs/failed-count.txt logs/top-ips.txt logs/fail2ban-sshd.txt
```
