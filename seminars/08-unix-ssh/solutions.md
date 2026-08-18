# Примеры решений

## База

### B1

```bash
ssh -V > ssh-client.txt 2>&1
which ssh >> ssh-client.txt
ssh -G course >> ssh-client.txt        # -G только печатает параметры, подключения нет
```

### B2

```bash
ssh course '{ hostname; whoami; pwd; uname -a; cat /etc/os-release; }' > remote-system.txt 2> remote-errors.txt
```

### B3

```bash
ssh course 'ls /etc/os-release /missing-file' > remote-stdout.txt 2> remote-stderr.txt
echo "$?" > remote-exit-code.txt
```

### B4

```bash
scp assets/B4/local.txt course:~/seminar8-file.txt
scp course:~/seminar8-file.txt returned.txt
wc -c assets/B4/local.txt returned.txt > sizes.txt
cmp assets/B4/local.txt returned.txt && echo 'content: identical' > verification.txt
```

### B5

```bash
cat > course-config <<'EOF'
Host course
    HostName HOST
    User USER
    Port 22
EOF

ssh -F course-config -G course > effective-config.txt
```

## Среднее

### M1

```bash
mkdir -p assets/M1/keys
ssh-keygen -t ed25519 -f assets/M1/keys/course_ed25519 -N '' -C 'course-key'
chmod 400 assets/M1/keys/course_ed25519
ssh-keygen -lf assets/M1/keys/course_ed25519.pub > key-fingerprint.txt
ls -l assets/M1/keys > key-files.txt
```

### M2

```bash
ssh course 'tmux new-session -d -s course-worker "sleep 120"'
ssh course 'tmux list-sessions; tmux list-panes -t course-worker -F "#{pane_pid} #{pane_current_command}"' > tmux-running.txt
ssh course 'tmux kill-session -t course-worker'
ssh course 'tmux has-session -t course-worker' > tmux-after.txt 2>&1 || echo 'finished' >> tmux-after.txt
```

### M3

```bash
rsync -av assets/M3/local-data/ course:~/seminar8-sync/ > first-sync.txt
rsync -av assets/M3/local-data/ course:~/seminar8-sync/ > second-sync.txt
```

### M4

```bash
touch assets/M4/course-known-hosts
# Учебный стенд: ssh-keyscan берёт то, что ответила сеть, и подлинность НЕ подтверждает.
# В работе полученный отпечаток сверяют с доверенным источником, прежде чем сохранять:
ssh-keyscan HOST > keyscan.pub 2> keyscan-errors.txt
ssh-keygen -lf keyscan.pub > keyscan-fingerprint.txt   # это и сверяют глазами
cat keyscan.pub >> assets/M4/course-known-hosts
ssh-keygen -F HOST -f assets/M4/course-known-hosts > known-host.txt
```

### M5

```bash
ssh -Tvvv course true > connection.out 2> connection-debug.txt
echo "$?" > connection-exit-code.txt
```

## Сложное

### H1

```bash
ssh-copy-id -i assets/M1/keys/course_ed25519.pub course
chmod 400 assets/M1/keys/course_ed25519
ssh-keygen -lf assets/M1/keys/course_ed25519.pub > selected-key.txt
# Внимание: IdentitiesOnly=yes ограничивает ssh конфигом и -i, но НЕ отменяет
# IdentityFile из ~/.ssh/config для этого хоста — ключ оттуда тоже будет предложен.
# Какой ключ реально принял сервер, видно в выводе -v: строка "Server accepts key".
ssh -v -o IdentitiesOnly=yes -i assets/M1/keys/course_ed25519 course 'whoami' \
  > remote-user.txt 2> key-login-errors.txt
```

### H2

```bash
echo 'alpha updated' > assets/H2/local-data/a.txt
echo 'gamma' > assets/H2/local-data/c.txt
rm -- assets/H2/local-data/nested/b.txt

rsync -avni --delete assets/H2/local-data/ course:~/seminar8-sync/ > sync-plan.txt
rsync -avi --delete assets/H2/local-data/ course:~/seminar8-sync/ > sync-result.txt
ls -l assets/H2/local-data > local-files.txt
ssh course 'ls -l ~/seminar8-sync' > remote-files.txt
```

### H3

```bash
ssh -N -o ExitOnForwardFailure=yes -L 8080:127.0.0.1:8000 course > tunnel.out 2> tunnel.err &
tunnel_pid=$!
sleep 2
curl http://127.0.0.1:8080 > success.html 2> success.err
ssh course 'kill -TERM "$(cat ~/http-server.pid)"' > stop-service.txt 2>&1
curl http://127.0.0.1:8080 > failed.html 2> failed.err || echo "$?" > failed-exit-code.txt
kill -TERM "$tunnel_pid"
wait "$tunnel_pid" || true   # мы сами убили процесс: wait вернёт 143, это не ошибка
```

### H4

```bash
ssh course 'tmux new-session -d -s course-lab -n system "uname -a; sleep 300"'
ssh course 'tmux new-window -t course-lab -n worker "uptime; sleep 300"'
ssh course 'tmux list-windows -t course-lab' > tmux-windows.txt
ssh course 'tmux capture-pane -p -t course-lab:system' > system-pane.txt
ssh course 'tmux capture-pane -p -t course-lab:worker' > worker-pane.txt
ssh course 'tmux kill-session -t course-lab'
```

### H5

```bash
rsync -avn --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' assets/H5/project/ course:~/project-backup/ > backup-plan.txt
rsync -av --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' assets/H5/project/ course:~/project-backup/ > backup-result.txt
ls -laR assets/H5/project > local-files.txt
ssh course 'ls -laR ~/project-backup' > remote-files.txt
```
