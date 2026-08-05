# Примеры решений

## База

### B1

```bash
mkdir -p input work result
touch input/empty-1 input/empty-2
echo "$USER" > input/user.txt
cp input/empty-1 input/empty-2 input/user.txt work/
rm -- work/empty-1
ls -l input work result
```

### B2

```bash
student_full_name='Anna Smith'
student_group_name='ML 01'
PROJECT_DATA_DIRECTORY="$HOME/course data"
{
  echo "$student_full_name"
  echo "$student_group_name"
  echo "$PROJECT_DATA_DIRECTORY"
  echo "${student_group_name}_report.txt"
} > variables.txt
```

### B3

```bash
COURSE_NAME='Linux course'
echo "current=$COURSE_NAME" > environment.txt
bash -c 'echo "child-before=${COURSE_NAME:-missing}"' >> environment.txt
export COURSE_NAME
bash -c 'echo "child-after=$COURSE_NAME"' >> environment.txt
```

### B4

```bash
cat parts/01.txt parts/02.txt parts/03.txt > document.txt
cp document.txt document-draft.txt
echo 'DRAFT' >> document-draft.txt
```

### B5

```bash
rm -- remove-me.txt
rmdir empty-directory
rmdir non-empty-directory 2> rmdir-error.txt
ls -l non-empty-directory
```

## Среднее

### M1

```bash
ls exists.txt missing.txt > stdout.txt 2> stderr.txt || true
ls exists.txt missing.txt > all.txt 2>&1 || true
echo 'finished' >> all.txt
```

### M2

```bash
chmod 744 run.sh
chmod 750 shared
stat -c '%A %a %n' run.sh shared > permissions.txt
```

### M3

```bash
cat source.txt | cat > pipeline.txt

cat missing.txt | cat
echo "$?" > without-pipefail.txt

set -o pipefail
cat missing.txt | cat
echo "$?" > with-pipefail.txt
```

### M4

```bash
sleep 30 &
process_id=$!
ps -o pid,ppid,stat,cmd -p "$process_id" > process.txt
kill -TERM "$process_id"
wait "$process_id" 2>/dev/null || true
ps -p "$process_id" >> process.txt 2>&1 || echo 'finished' >> process.txt
```

### M5

```bash
{
  uname -a
  cat /etc/os-release
  echo "USER=$USER"
  echo "HOME=$HOME"
  echo "PWD=$PWD"
} > system.txt

which top > tools.txt || echo 'top: not found' > tools.txt
which htop >> tools.txt || echo 'htop: not found' >> tools.txt
which nvidia-smi >> tools.txt || echo 'nvidia-smi: not found' >> tools.txt
```

## Сложное

### H1

```bash
sleep 30 &
process_id=$!
ps -o pid,stat,cmd -p "$process_id" > states.txt
kill -STOP "$process_id"
ps -o pid,stat,cmd -p "$process_id" >> states.txt
kill -CONT "$process_id"
ps -o pid,stat,cmd -p "$process_id" >> states.txt
kill -TERM "$process_id"
wait "$process_id" 2>/dev/null || true
ps -p "$process_id" >> states.txt 2>&1 || echo 'finished' >> states.txt
```

### H2

```bash
mkdir -p destination
cp -r source/. destination/

source_count=$(ls source | wc -l)
destination_count=$(ls destination | wc -l)

source_sizes=$(cd source && wc -c -- *)
destination_sizes=$(cd destination && wc -c -- *)

{
  echo "source_count=$source_count"
  echo "destination_count=$destination_count"
  echo 'source sizes:'
  echo "$source_sizes"
  echo 'destination sizes:'
  echo "$destination_sizes"
} > verification.txt

test "$source_count" -eq "$destination_count" || exit 1
test "$source_sizes" = "$destination_sizes" || exit 1
```

### H3

```bash
mkdir -p report
{
  uname -a
  cat /etc/os-release
  uptime
  free -h
  df -h "$HOME"
} > report/system.txt 2> report/errors.txt

ps -u "$USER" -o pid,ppid,stat,%cpu,%mem,cmd \
  > report/processes.txt 2>> report/errors.txt

which top > report/tools.txt || echo 'top: not found' >> report/tools.txt
which htop >> report/tools.txt || echo 'htop: not found' >> report/tools.txt
which nvidia-smi >> report/tools.txt || echo 'nvidia-smi: not found' >> report/tools.txt
```

### H4

`worker.sh`:

```bash
#!/usr/bin/env bash

sleep "$1"
exit "$2"
```

`manager.sh`:

```bash
#!/usr/bin/env bash

chmod +x worker.sh

./worker.sh 2 0 > worker-1.log 2>&1 &
pid_1=$!
./worker.sh 3 1 > worker-2.log 2>&1 &
pid_2=$!
./worker.sh 4 0 > worker-3.log 2>&1 &
pid_3=$!

status=0
wait "$pid_1" || status=1
wait "$pid_2" || status=1
wait "$pid_3" || status=1
exit "$status"
```

### H5

```bash
mkdir backups/staging || exit 1
cp -r project/. backups/staging/

project_count=$(ls project | wc -l)
backup_count=$(ls backups/staging | wc -l)
test "$project_count" -eq "$backup_count" || exit 1

project_sizes=$(cd project && wc -c -- *)
backup_sizes=$(cd backups/staging && wc -c -- *)

{
  echo "project_count=$project_count"
  echo "backup_count=$backup_count"
  echo 'project sizes:'
  echo "$project_sizes"
  echo 'backup sizes:'
  echo "$backup_sizes"
} > backups/verification.txt

test "$project_sizes" = "$backup_sizes" || exit 1
mv backups/staging backups/backup-ready
```
