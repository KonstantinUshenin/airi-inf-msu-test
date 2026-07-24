# Примеры решений

## База

### B1

```bash
ssh -V > ssh-client.txt 2>&1
which ssh >> ssh-client.txt
ssh -G student@server.example >> ssh-client.txt
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
scp local.txt course:~/seminar8-file.txt
scp course:~/seminar8-file.txt returned.txt
wc -c local.txt returned.txt > sizes.txt
cmp local.txt returned.txt && echo 'content: identical' > verification.txt
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
mkdir -p keys
ssh-keygen -t ed25519 -f keys/course_ed25519 -N '' -C 'course-key'
chmod 400 keys/course_ed25519
ssh-keygen -lf keys/course_ed25519.pub > key-fingerprint.txt
ls -l keys > key-files.txt
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
rsync -av local-data/ course:~/seminar8-sync/ > first-sync.txt
rsync -av local-data/ course:~/seminar8-sync/ > second-sync.txt
```

### M4

```bash
touch course-known-hosts
ssh-keyscan HOST >> course-known-hosts 2> keyscan-errors.txt
ssh-keygen -F HOST -f course-known-hosts > known-host.txt
```

### M5

```bash
ssh -Tvvv course true > connection.out 2> connection-debug.txt
echo "$?" > connection-exit-code.txt
```

## Сложное

### H1

```bash
ssh-copy-id -i keys/course_ed25519.pub course
chmod 400 keys/course_ed25519
ssh-keygen -lf keys/course_ed25519.pub > selected-key.txt
ssh -o IdentitiesOnly=yes -i keys/course_ed25519 course 'whoami' > remote-user.txt 2> key-login-errors.txt
```

### H2

```bash
rsync -avni --delete local-data/ course:~/seminar8-sync/ > sync-plan.txt
rsync -avi --delete local-data/ course:~/seminar8-sync/ > sync-result.txt
ls -l local-data > local-files.txt
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
wait "$tunnel_pid"
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
rsync -avn --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' project/ course:~/project-backup/ > backup-plan.txt
rsync -av --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' project/ course:~/project-backup/ > backup-result.txt
ls -laR project > local-files.txt
ssh course 'ls -laR ~/project-backup' > remote-files.txt
```
