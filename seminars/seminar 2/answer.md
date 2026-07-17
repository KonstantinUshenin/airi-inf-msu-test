# Примеры решений

## Basic

### B1

```bash
mkdir -p input work result
touch input/empty-1 input/empty-2
echo "$USER" > input/user.txt
cp input/* work/
rm -- work/empty-1
ls -l input work result
```

### B2

```bash
touch exists.txt
ls exists.txt missing.txt > stdout.txt 2> stderr.txt || echo "$?" > exit-code.txt
ls exists.txt missing.txt > all.txt 2>&1 || echo "$?" >> all.txt
echo 'done' >> all.txt
```

### B3

```bash
COURSE_NAME='Linux course'
echo "$COURSE_NAME"
bash -c 'echo "${COURSE_NAME:-missing}"'
export COURSE_NAME
bash -c 'echo "$COURSE_NAME"'
```

### B4

```bash
sleep 30 &
process_id=$!
echo "$process_id"
ps -p "$process_id"
kill -TERM "$process_id"
wait "$process_id"
ps -p "$process_id" || echo 'finished'
```

### B5

```bash
{
  uname -a
  cat /etc/os-release
  echo "USER=$USER"
  echo "HOME=$HOME"
  echo "PWD=$PWD"
} > system.txt

command -v top || echo 'top: not found'
command -v htop || echo 'htop: not found'
command -v nvidia-smi || echo 'nvidia-smi: not found'
```

### B6

```bash
student_full_name='Anna Smith'
student_group_name='ML 01'
PROJECT_DATA_DIRECTORY="$HOME/course data"
echo "${student_full_name}"
echo "${student_group_name}"
echo "${PROJECT_DATA_DIRECTORY}"
echo "${student_group_name}_report.txt"
```

### B7

```bash
cat parts/01.txt parts/02.txt parts/03.txt > document.txt
cp document.txt document-draft.txt
echo 'DRAFT' >> document-draft.txt
wc -l document.txt document-draft.txt
```

### B8

```bash
touch remove-me.txt
mkdir empty-directory
mkdir non-empty-directory
touch non-empty-directory/file.txt
rm -- remove-me.txt
rmdir empty-directory
rmdir non-empty-directory 2> rmdir-error.txt
```

### B9

```bash
chmod 744 run.sh
chmod 750 shared
ls -l run.sh
ls -ld shared
stat -c '%a %n' run.sh shared
```

### B10

```bash
cat /etc/os-release | tee os-release.txt | head -n 5 | wc -l

cat /missing-file | wc -l
echo "$?" > without-pipefail.txt

set -o pipefail
cat /missing-file | wc -l
echo "$?" > with-pipefail.txt
```

## Advanced

### A1

```bash
sleep 30 &
process_id=$!
ps -o pid,stat,cmd -p "$process_id"
kill -STOP "$process_id"
ps -o pid,stat,cmd -p "$process_id"
kill -CONT "$process_id"
ps -o pid,stat,cmd -p "$process_id"
kill -TERM "$process_id"
wait "$process_id"
```

### A2

```bash
mkdir -p destination
cp -r source/. destination/

source_count=$(ls source | wc -l)
destination_count=$(ls destination | wc -l)
test "$source_count" -eq "$destination_count" || exit 1

source_sizes=$(cd source && wc -c -- *)
destination_sizes=$(cd destination && wc -c -- *)
test "$source_sizes" = "$destination_sizes"
```

### A3

```bash
mkdir -p report
{
  uname -a
  cat /etc/os-release
  uptime
  free -h
  df -h "$HOME"
} > report/system.txt 2> report/errors.txt

ps -u "$USER" -o pid,ppid,stat,%cpu,%mem,cmd > report/processes.txt

command -v top > report/tools.txt || echo 'top: not found' >> report/tools.txt
command -v htop >> report/tools.txt || echo 'htop: not found' >> report/tools.txt
command -v nvidia-smi >> report/tools.txt || echo 'nvidia-smi: not found' >> report/tools.txt
```

### A4

`worker.sh`:

```bash
sleep "$1"
exit "$2"
```

```bash
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

### A5

```bash
mkdir backups/staging || exit 1
cp -r project/. backups/staging/

project_count=$(ls project | wc -l)
backup_count=$(ls backups/staging | wc -l)
test "$project_count" -eq "$backup_count" || exit 1

project_sizes=$(cd project && wc -c -- *)
backup_sizes=$(cd backups/staging && wc -c -- *)
test "$project_sizes" = "$backup_sizes" || exit 1
mv backups/staging backups/backup-ready
```
