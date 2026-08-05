# Примеры решений

Приведён один рабочий вариант на задачу. Решения базового и среднего уровней
продолжают друг друга и предполагают репозиторий из B1.

## База

### B1. Первый репозиторий

```bash
mkdir -p ~/seminar-04/git-tasks && cd ~/seminar-04/git-tasks

git config --global init.defaultBranch main   # один раз на машину
git init -q
git branch --show-current                     # main

git config user.name "Ваше Имя"
git config user.email "you@example.org"

cat > train.py <<'PY'
accuracy = 0.93
print("accuracy =", accuracy)
PY

git add train.py
git commit -m "feat(train): добавить baseline-эксперимент"

git log --oneline
git log -1 --format='полный: %H%nкороткий: %h%nавтор: %an%nдата: %ad%nсообщение: %s'
```

Без `init.defaultBranch` git назвал бы первую ветку `master` (и напечатал бы про
это подсказку). Флаг `git init -b main` делает то же самое разово, но на практике
настройку ставят один раз глобально и больше о ней не думают.

### B2. Три зоны и индекс

```bash
sed -i 's/0.93/0.95/' train.py

git status --short          # M train.py — репозиторий грязный
git diff                    # рабочая копия против индекса

git add train.py

git diff                    # пусто: рабочая копия и индекс совпали
git diff --cached           # индекс против последнего коммита
git diff HEAD               # рабочая копия против коммита, минуя индекс

git commit -m "feat(train): поднять accuracy до 0.95"
```

`git diff` без аргументов сравнивает рабочую копию с **индексом**. `git add`
скопировал изменение в индекс, поэтому сравнивать стало нечего — изменение
переехало на одну зону вперёд и видно через `--cached`.

### B3. Восстановление после катастрофы

```bash
rm -rf *.py
ls                          # пусто
git status --short          # D train.py
git restore .               # вернули из последнего коммита
cat train.py                # файл на месте

# вторая часть: файл, которого git не знает
echo "черновик" > draft.txt
rm draft.txt
git restore .               # ничего не произошло
ls draft.txt                # No such file or directory
```

`restore` восстанавливает файлы **из истории**. `draft.txt` не попадал ни в
индекс, ни в коммит, значит в истории его нет и восстанавливать нечего. Работа
сохранена не в момент записи файла на диск, а в момент коммита.

### B4. Уборка мусора

```bash
touch checkpoint.pt nohup.out
mkdir -p __pycache__ && touch __pycache__/x.pyc

git status --short          # ?? — git об этих файлах ничего не знает
git clean -nd               # только показать: Would remove ...
git clean -fd               # удалить

git status --short          # пусто
ls train.py                 # отслеживаемый файл на месте
```

`-n` — показать, `-f` — удалить (обязателен, это предохранитель), `-d` — вместе
с каталогами, `-x` — включая игнорируемое.

### B5. `.gitignore`

```bash
cat > .gitignore <<'EOF'
# отдельный файл
secrets.env

# каталог целиком
data/

# по маске
*.pt
*.log

# исключение из маски выше
!baseline.pt
EOF

mkdir -p data
touch secrets.env data/train.csv model.pt baseline.pt run.log

git status --short                     # видны только .gitignore и baseline.pt
git check-ignore -v secrets.env data/train.csv model.pt run.log

git add .gitignore
git commit -m "chore: добавить .gitignore"
```

Комментарий в `.gitignore` занимает всю строку: приписать `# ...` в конец
строки с правилом нельзя — это станет частью маски. Правило с `!` обязано идти
**после** маски, которую отменяет.

### B6. Ветка и слияние

```bash
git switch -c feature/plot
echo 'print("график сохранён")' >> train.py
git commit -am "feat(train): сохранять график обучения"

git switch main
git merge feature/plot        # Fast-forward, конфликта нет
git branch -d feature/plot

git log --oneline --graph --decorate
git branch                    # осталась только main
```

### B7. Читаемая история

```bash
git config --global alias.lg "log --oneline --graph --decorate --all"
git lg

git show --stat $(git log -1 --format=%h)
```

Алиас с `--global` попадает в `~/.gitconfig` и работает во всех репозиториях.

### B8. Что внутри `.git`

```bash
cat .git/HEAD                   # ref: refs/heads/main — где мы сейчас
cat .git/refs/heads/main        # хэш последнего коммита ветки
git rev-parse HEAD              # тот же хэш, полученный «официально»

git switch -c проба -q
cat .git/HEAD                   # ref: refs/heads/проба
ls .git/refs/heads/             # появился ещё один файл — main и проба
git switch -q main
git branch -d проба
```

`HEAD` — текстовый файл с указателем на ветку, ветка — текстовый файл с хэшем
коммита. Поэтому создание ветки стоит один маленький файл и не копирует ни
файлы проекта, ни историю.

Если файла `.git/refs/heads/main` не оказалось — git упаковал ссылки в
`.git/packed-refs` (это делает `git gc`); хэш ветки тогда лежит там.

### B9. Соглашения об именах

```bash
git switch -c мои-правки                    # git это разрешает, но так не делают
git branch -m мои-правки feature/augmentation
git branch --show-current                   # feature/augmentation

echo "# аугментации" >> train.py
git commit -qam "feat(train): добавить аугментации" \
    -m "Первая гипотеза: горизонтальный флип и случайный кроп."

git log --oneline -1        # видно только заголовок
git log -1                  # заголовок, пустая строка, тело
```

Исправление плохого сообщения:

```bash
echo "# ещё правка" >> train.py
git commit -qam "правки"
git log --oneline -1                        # a1b2c3d правки
git rev-parse HEAD                          # запомнили хэш

git commit -q --amend -m "feat(train): логировать метрику на валидации"
git log --oneline -1                        # новый заголовок
git rev-parse HEAD                          # хэш ДРУГОЙ
```

`--amend` не редактирует коммит, а создаёт новый (с новым хэшем) и передвигает
на него ветку; старый остаётся сиротой и находится через `git reflog`. Поэтому
для выложенного коммита `--amend` запрещён: у коллег в истории лежит прежний
хэш, после `amend` истории разойдутся, а `push` пройдёт только с `--force`,
затирая их работу. Пробел в имени ветки, кстати, git не позволит вообще:
`fatal: 'мои правки' is not a valid branch name`.

## Среднее

### M1. Конфликт слияния

```bash
git switch -c feature/augmentation
sed -i 's/accuracy = 0.95/accuracy = 0.97/' train.py
git commit -am "feat(train): добавить аугментации"

git switch main
sed -i 's/accuracy = 0.95/accuracy = 0.91/' train.py
git commit -am "feat(train): сменить оптимизатор"

git merge feature/augmentation
echo "код возврата: $?"       # 1
cat train.py                  # <<<<<<< HEAD ... ======= ... >>>>>>>

# разрешаем вручную: оставляем нужный вариант, маркеры убираем
cat > train.py <<'PY'
accuracy = 0.97
print("accuracy =", accuracy)
PY

git add train.py
git commit -m "Слить feature/augmentation: оставить аугментации"
git log --oneline --graph --decorate --all
```

Между `<<<<<<< HEAD` и `=======` — версия текущей ветки, ниже до `>>>>>>>` —
версия вливаемой. Файл после разрешения не должен содержать маркеров.

### M2. Файл в состоянии другой ветки

```bash
git switch -c experiment/lr
sed -i 's/accuracy = 0.97/accuracy = 0.88/' train.py
git commit -am "feat(train): попробовать lr=0.01"
git switch main

git restore --source=experiment/lr -- train.py
cat train.py                  # содержимое как на другой ветке
git branch --show-current     # main — ветку не меняли
git status --short            # M train.py
git restore .                 # откатили

git restore --source=HEAD~2 -- train.py    # то же из старого коммита
git restore .
```

### M3. `revert` против `reset`

```bash
# способ 1: сдвинуть ветку — коммит исчезает из истории
git log --oneline
git reset --hard HEAD~1
git log --oneline             # на строку меньше
git reset --hard HEAD@{1}     # вернули обратно

# способ 2: отменяющий коммит
git revert --no-edit HEAD
git log --oneline             # на строку БОЛЬШЕ: появился Revert "..."
```

Для ветки, уже выложенной на сервер, допустим только `revert`. `reset`
переписывает историю: у коллег эти коммиты уже есть, их ветки разойдутся с
вашей, и push пройдёт только с `--force`, затирая чужую работу. `revert`
историю не трогает — он добавляет новый коммит с обратными изменениями.

### M4. Отложить работу

```bash
sed -i 's/accuracy = .*/accuracy = 0.99  # недоделано/' train.py

git stash                     # отложили
git status --short            # пусто
git stash list                # stash@{0}: WIP on main: ...

git switch -c hotfix
# ... срочная правка, коммит ...
git switch main

git stash pop                 # вернули отложенное
git status --short            # M train.py
git restore .
```

`git stash pop` применяет и удаляет запись, `git stash apply` — применяет,
оставляя её в списке.

### M5. Перенос коммита

```bash
git switch -c feature/three
echo "# правка 1" >> train.py && git commit -am "Правка 1"
sed -i 's/accuarcy/accuracy/' train.py 2>/dev/null
echo "# исправлена опечатка" >> train.py && git commit -am "Исправили опечатку"
echo "# правка 3" >> train.py && git commit -am "Правка 3"

FIX=$(git log --format='%h %s' | grep 'опечатк' | cut -d' ' -f1)
git switch main
git cherry-pick "$FIX"

git log --oneline -2          # коммит с тем же сообщением, но другим хэшем
```

Хэш меняется, потому что у перенесённого коммита другой родитель, а родитель
входит в вычисление хэша.

### M6. Кто изменил эту строку

```bash
git blame train.py                       # весь файл
git blame -L 1,1 --date=short train.py   # только первая строка
git blame -w train.py                    # игнорируя правки пробелов и отступов

git log --oneline -S "accuracy" -- train.py   # где строка появлялась/исчезала
git log -p -S "accuracy" -- train.py          # то же с показом изменений
```

`-S` (pickaxe) ищет коммиты, в которых **изменилось число вхождений** подстроки,
то есть где её добавили или удалили. Это не то же самое, что `git log --grep`,
который ищет по тексту сообщений коммитов.

### M7. Лишний файл в репозитории

```bash
head -c 1000000 /dev/urandom > model.pt
git add -f model.pt && git commit -m "chore: добавить веса"     # упс

echo "*.pt" >> .gitignore
git add .gitignore && git commit -m "chore: игнорировать веса"

echo "новые веса" >> model.pt
git status --short            # M model.pt — файл всё ещё отслеживается

git rm --cached model.pt
git commit -m "chore: убрать веса из-под контроля версий"

git status --short            # пусто
ls model.pt                   # файл на диске остался
```

`.gitignore` отвечает на вопрос «начинать ли отслеживать», а не «продолжать ли».
Для уже отслеживаемого файла нужна связка: правило в `.gitignore` **плюс**
`git rm --cached`.

### M8. Работа с upstream

```bash
# форк делается кнопкой в веб-интерфейсе платформы
git clone <адрес вашего форка> && cd <repo>
git remote -v                                  # origin (fetch) и origin (push)

git remote add upstream <адрес оригинала>
git remote -v                                  # теперь четыре строки

git fetch upstream
git log --oneline HEAD..upstream/main          # что нового у них
git merge upstream/main

git switch -c my-feature
# ... правки, коммиты ...
git push -u origin my-feature
```

Дальше pull request открывается по ссылке, которую печатает `git push`, или
кнопкой в веб-интерфейсе. `-u` запоминает связь ветки с `origin/my-feature`,
после этого достаточно `git push`.

### M9. Настройка доступа

Вариант с SSH:

```bash
ssh-keygen -t ed25519 -C "you@example.org"     # Enter на все вопросы
cat ~/.ssh/id_ed25519.pub                      # содержимое — в настройки аккаунта

ssh -T git@github.com
# Hi <username>! You've successfully authenticated, but GitHub does not
# provide shell access.

git remote set-url origin git@github.com:<user>/<repo>.git
git push
```

Вариант с PAT: создать токен в настройках аккаунта с минимальными правами и
ограниченным сроком, затем

```bash
git config --global credential.helper store
git push        # логин — имя пользователя, пароль — токен; сохранится
```

Токен нельзя вписывать в адрес репозитория (`https://user:ТОКЕН@host/...`):
он остаётся открытым текстом в `.git/config`, печатается в выводе
`git remote -v` и попадает в любой скриншот, лог или пересланную команду. При
утечке токен нужно немедленно отозвать в настройках аккаунта.

### M10. Реверс-инженерия объектов

```bash
H=$(git rev-parse HEAD)
git cat-file -t "$H"                                   # commit
git cat-file -p "$H"                                   # tree, parent, author, сообщение

T=$(git cat-file -p "$H" | awk '/^tree /{print $2}')
git cat-file -p "$T"                                   # 100644 blob <хэш>	train.py

B=$(git cat-file -p "$T" | awk '$4 == "train.py" {print $3}')
git cat-file -p "$B"                                   # содержимое файла
```

Имя файла хранится в `tree`, а не в `blob`: `blob` — это только содержимое.
Поэтому два одинаковых файла с разными именами дают один и тот же `blob`.

Объект руками:

```bash
echo "привет" > scratch.txt
H=$(git hash-object -w scratch.txt)     # -w: не только посчитать хэш, но и записать
ls -l ".git/objects/${H:0:2}/"          # каталог из 2 символов, файл из 38

python3 - "$H" <<'PY'
import pathlib, sys, zlib

h = sys.argv[1]
raw = pathlib.Path(f".git/objects/{h[:2]}/{h[2:]}").read_bytes()
header, _, body = zlib.decompress(raw).partition(b"\0")
print(header.decode(), "|", body.decode().rstrip())     # blob 13 | привет
PY

git hash-object scratch.txt             # тот же хэш: адресация по содержимому
echo "привет!" > scratch.txt
git hash-object scratch.txt             # один символ — и хэш совершенно другой
rm scratch.txt
```

Формат объекта: `<тип> <длина>\0<содержимое>`, сжатое zlib. Хэш считается от
этой строки целиком, поэтому он не зависит ни от имени файла, ни от ветки, ни
от времени.

## Сложное

### H1. Поиск сломавшего коммита

```bash
# подготовка учебного репозитория
mkdir -p ~/seminar-04/bisect-demo && cd ~/seminar-04/bisect-demo
git init -q
git config user.name S && git config user.email s@e.org
for i in $(seq 1 12); do
    if [ "$i" -lt 8 ]; then acc=0.93; else acc=0.71; fi
    printf 'accuracy = %s\n# правка %s\nprint("accuracy =", accuracy)\n' "$acc" "$i" > train.py
    git add train.py && git commit -q -m "feat(train): правка $i"
done
```

Вручную:

```bash
git bisect start
git bisect bad                 # текущее состояние плохое
git bisect good HEAD~11        # одиннадцать коммитов назад было хорошо
# git показывает середину; на каждом шаге запускаем python3 train.py и отвечаем:
git bisect good                # или git bisect bad
# ... повторяем, пока не напечатает "is the first bad commit"
git bisect reset
```

Автоматически:

```bash
cat > check.sh <<'SH'
#!/bin/sh
acc=$(python3 train.py | awk '{print $3}')
awk -v a="$acc" 'BEGIN { exit (a >= 0.90) ? 0 : 1 }'
SH
chmod +x check.sh

git bisect start HEAD HEAD~11
git bisect run ./check.sh      # <хэш> is the first bad commit
git bisect reset
```

Подряд пришлось бы проверить до 11 коммитов, бинарным поиском — 4 шага
(`log₂ 11 ≈ 3.5`). На истории в 1000 коммитов разница уже 1000 против 10.
Скрипт-проверка должен возвращать 0 для «хорошего» состояния; код 125
зарезервирован под «не могу проверить, пропусти этот коммит».

### H2. Восстановление потерянного

```bash
# потеря 1: сдвинули ветку назад
git reset --hard HEAD~3
git log --oneline              # трёх коммитов нет
git reflog                     # находим строку до reset
git reset --hard HEAD@{1}      # или по хэшу из reflog

# потеря 2: удалили неслитую ветку
git switch -c lost-branch
echo "важное" >> train.py && git commit -am "Важная работа"
git switch main
git branch -D lost-branch      # -D удаляет даже неслитую

git reflog                     # находим хэш коммита "Важная работа"
git switch -c lost-branch <хэш>
git log --oneline -1           # коммит на месте
```

Reflog — локальный журнал перемещений `HEAD`, хранится около 90 дней. Он
спасает коммиты, но **не** спасает незакоммиченные изменения: то, что на момент
`reset --hard` лежало в рабочей копии, стирается безвозвратно.

### H3. Секрет в истории

```bash
echo "API_TOKEN=ghp_секретное_значение" > secrets.env
git add -f secrets.env && git commit -m "chore: добавить конфигурацию"
echo "# работа" >> train.py && git commit -am "Правка"

git rm secrets.env && git commit -m "chore: удалить секреты"
ls secrets.env                                  # файла нет

git log -p -- secrets.env | grep API_TOKEN      # но токен достаётся из истории
git show HEAD~1:secrets.env                     # и напрямую тоже
```

Чистим историю целиком:

```bash
pip install git-filter-repo
git filter-repo --path secrets.env --invert-paths --force

git log --all --oneline -- secrets.env          # пусто
git log --all -p | grep API_TOKEN               # ничего не находит
```

Обычный `git rm` удаляет файл только из **будущих** коммитов — в предыдущих он
остаётся, и любой, у кого есть клон, достаёт его одной командой.

В реальной ситуации чистки истории **недостаточно**. Порядок действий:
1. немедленно **отозвать** утёкший токен или ключ и выпустить новый — считайте,
   что он скомпрометирован с момента push;
2. только потом чистить историю;
3. предупредить всех, у кого есть клон: после `filter-repo` хэши всех коммитов
   изменились, старые клоны нужно пересоздать, иначе секрет вернётся обратно с
   первым же push;
4. проверить, не осталась ли копия в кэше платформы, в старых pull request и в
   логах CI.

### H4. Версионирование большого файла

```bash
git lfs install
git lfs track "*.pt"
cat .gitattributes             # *.pt filter=lfs diff=lfs merge=lfs -text
git add .gitattributes && git commit -m "chore(lfs): настроить LFS"

head -c 20000000 /dev/urandom > model.pt
git add model.pt && git commit -m "feat(model): версия 1"

head -c 20000000 /dev/urandom > model.pt
git add model.pt && git commit -m "feat(model): версия 2"

git show HEAD:model.pt | head -3
# version https://git-lfs.github.com/spec/v1
# oid sha256:...
# size 20000000

git lfs ls-files
```

В репозиторий попадает указатель на ~130 байт, сами данные лежат в отдельном
хранилище и скачиваются по требованию. Без LFS две версии дали бы +40 МБ в
истории навсегда.

### H5. Защита от собственной ошибки

```bash
cat > .git/hooks/pre-commit <<'SH'
#!/bin/sh
LIMIT=$((5 * 1024 * 1024))
status=0

for f in $(git diff --cached --name-only --diff-filter=AM); do
    case "$f" in
        *.pt|*.pth|*.ckpt|*.bin)
            echo "Отклонено: $f — веса моделей в git не коммитим, используйте Git LFS"
            status=1
            continue
            ;;
    esac
    size=$(git cat-file -s "$(git rev-parse ":$f")")
    if [ "$size" -gt "$LIMIT" ]; then
        echo "Отклонено: $f ($((size / 1024 / 1024)) МБ) — больше 5 МБ"
        status=1
    fi
done

exit $status
SH
chmod +x .git/hooks/pre-commit

echo "b = 1" > ok.py && git add ok.py && git commit -m "feat: добавить ok.py"   # проходит

head -c 100 /dev/urandom > model.pt
git add -f model.pt && git commit -m "chore: добавить веса"       # отклонено
```

Размер берётся не с диска, а из индекса (`git cat-file -s` по объекту из
`git rev-parse ":файл"`) — так учитывается ровно то, что попадёт в коммит.

Полагаться на хуки как на единственную защиту нельзя: каталог `.git/hooks` не
версионируется и не приезжает при `git clone`, а любой хук отключается флагом
`--no-verify`. Хук — это удобная подсказка себе, а не гарантия; настоящая
проверка должна стоять на сервере (CI или защищённая ветка).

### H6. Конфликт в ноутбуке

```bash
pip install nbdime
nbdime config-git --enable          # git будет звать nbdiff/nbmerge для .ipynb

# создать конфликт: изменить одну ячейку на двух ветках и слить
git merge other-branch
nbdiff base.ipynb other.ipynb       # различия по ячейкам, а не по JSON
git mergetool --tool=nbdime         # разрешение по ячейкам
```

Обычное разрешение неудобно, потому что `.ipynb` — это JSON, и в diff вместе с
текстом ячейки попадают `execution_count`, `id` ячеек и сохранённые выводы:
конфликтные маркеры оказываются внутри структуры JSON и легко превращают файл в
невалидный.

Правила, снижающие вероятность таких конфликтов:
- чистить выводы перед коммитом (`jupyter nbconvert --clear-output --inplace`
  или `nbstripout` как хук);
- не править один ноутбук вдвоём одновременно — делить по файлам;
- логику выносить в `.py`-модули, а в ноутбуке оставлять вызовы: обычный код
  сливается без всяких инструментов.

### H7. Конфликт в паре

Оба участника:

```bash
git clone <адрес общего репозитория> && cd <repo>
```

Участник A:

```bash
sed -i 's/accuracy = .*/accuracy = 0.97/' train.py
git commit -am "Вариант A"
git push                                  # проходит
```

Участник B (одновременно):

```bash
sed -i 's/accuracy = .*/accuracy = 0.91/' train.py
git commit -am "Вариант B"
git push
# ! [rejected]  main -> main (fetch first)

git pull                                  # скачал изменения A → конфликт
cat train.py                              # маркеры <<<<<<< / ======= / >>>>>>>
# разрешаем, сохраняя смысл обеих правок
git add train.py
git commit -m "Слить варианты A и B"
git push                                  # теперь проходит

git log --graph --oneline --all
```

Отказ означает: на сервере есть коммиты, которых нет у вас, и push «перемотать»
ветку вперёд не может — иначе чужая работа была бы потеряна. Правильная реакция
— скачать чужие изменения и слить их со своими. Делать в этой ситуации
`git push --force` нельзя: он затрёт коммиты участника A.

### H8. Распухший репозиторий

```bash
du -sh .git                                     # например 404K

head -c 20000000 /dev/urandom > checkpoint.pt
git add -f checkpoint.pt                        # -f, если действует маска *.pt
git commit -q -m "chore: добавить чекпойнт"   # упс
du -sh .git                                     # ~20M

git rm -q checkpoint.pt
git commit -q -m "chore: удалить чекпойнт"
du -sh .git                                     # всё ещё ~20M
git count-objects -vH                           # size-pack/size показывают те же 20 МБ

git gc -q                                       # упаковка не помогает:
du -sh .git                                     # случайные данные не сжимаются
```

Файл остаётся в базе, потому что на его `blob` по-прежнему ссылается `tree`
коммита, в котором файл ещё был. `git rm` добавляет новый коммит «файла больше
нет», но старые коммиты обязаны разворачиваться, значит объект нужен.

Чистка:

```bash
pip install git-filter-repo
git filter-repo --path checkpoint.pt --invert-paths --force

du -sh .git                                     # снова около 404K
git log --all --oneline -- checkpoint.pt        # пусто
```

`filter-repo` сам просрочивает reflog и вызывает сборку мусора. Если
`git-filter-repo` поставить не удалось, то же самое делается встроенным
`filter-branch`, но чистить ссылки и мусор придётся руками — иначе размер
`.git` не изменится:

```bash
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
    --index-filter 'git rm --cached --ignore-unmatch checkpoint.pt' \
    --prune-empty HEAD

# filter-branch оставляет резервные ссылки на СТАРУЮ историю —
# пока они есть, объект жив и место не освободится
git for-each-ref --format='%(refname)' refs/original | xargs -n1 git update-ref -d
git reflog expire --expire=now --all
git gc --prune=now -q

du -sh .git                                     # вот теперь снова ~404K
git count-objects -vH                           # count: 0
```

Чистка истории **переписывает все коммиты**, где встречался файл, то есть меняет
их хэши. У коллеги, склонировавшего репозиторий раньше, остаётся история со
старыми хэшами: его `git pull` увидит две несвязанные истории, а ваш `push`
пройдёт только с `--force`. Поэтому договариваются заранее: все выкладывают
работу, один человек чистит, остальные клонируют репозиторий заново. И поэтому
дешевле не допускать таких коммитов — `.gitignore` (раздел 6) и LFS
(раздел 13).

### H9. Проверка соглашений автоматикой

```bash
mkdir -p .githooks

cat > .githooks/commit-msg <<'EOF'
#!/bin/bash
# git передаёт хуку путь к файлу с сообщением коммита
head=$(head -1 "$1")
pattern='^(feat|fix|docs|refactor|test|chore)(\([a-z0-9_-]+\))?: .+$'

if ! grep -Eq "$pattern" <<< "$head"; then
    echo "commit-msg: заголовок не по Conventional Commits:" >&2
    echo "  '$head'" >&2
    echo "  нужно: тип(область): описание" >&2
    exit 1
fi
if (( ${#head} > 72 )); then
    echo "commit-msg: заголовок длиннее 72 символов (${#head})" >&2
    exit 1
fi
EOF

cat > .githooks/pre-push <<'EOF'
#!/bin/bash
# git подаёт на stdin строки: <local ref> <local sha> <remote ref> <remote sha>
allowed='^(feature|fix|exp|docs|refactor)/[a-z0-9._-]+$'

while read -r local_ref local_sha remote_ref remote_sha; do
    branch=${local_ref#refs/heads/}
    [[ "$branch" == "main" || -z "$branch" ]] && continue
    if ! grep -Eq "$allowed" <<< "$branch"; then
        echo "pre-push: имя ветки '$branch' не по соглашению <тип>/<описание>" >&2
        exit 1
    fi
done
EOF

chmod +x .githooks/commit-msg .githooks/pre-push
git config core.hooksPath .githooks          # искать хуки здесь, а не в .git/hooks
git add .githooks
git commit -m "chore: подключить хуки проверки соглашений"
```

Проверяем, что хуки работают:

```bash
echo "# правка" >> train.py
git commit -am "правки"                      # отбито, код возврата 1
git commit -am "fix: убрать лишний вывод"    # прошло

git init -q --bare ~/seminar-04/fake-remote.git    # «сервер» для проверки
git remote add origin ~/seminar-04/fake-remote.git
git push -q origin main                      # main разрешён

git switch -qc мои-правки
echo "# ещё" >> train.py
git commit -qam "fix: поправить опечатку"
git push origin мои-правки                   # отбито хуком pre-push

git branch -m мои-правки fix/typo-in-metric
git push origin fix/typo-in-metric           # прошло
```

Хуки лежат в `.githooks`, а не в `.git/hooks`, потому что каталог `.git` **не
версионируется** и не копируется при `clone`: хуки из `.git/hooks` есть только у
вас и исчезнут на другой машине. Каталог внутри репозитория коммитится, и
`core.hooksPath` подключает его одной командой (обычно её ставят в `make setup`
или в README проекта).

Гарантии локальные хуки не дают:

```bash
echo "# обход" >> train.py
git commit -am "правки" --no-verify          # хук не запускался, коммит создан
git push --no-verify origin fix/typo-in-metric
```

`--no-verify` отключает любые локальные хуки, а `core.hooksPath` вообще нужно
один раз включить руками — новый участник просто не будет ничего проверять.
Настоящая проверка живёт на **сервере**:

- **защищённая ветка + обязательные проверки** (branch protection / protected
  branches): в `main` нельзя пушить напрямую, только через pull request, а
  влить его можно лишь когда зелёный CI-джоб проверил сообщения коммитов
  (`commitlint`) и имя ветки. Нарушение не попадёт в основную ветку;
- **серверный хук `pre-receive`** (на своём GitLab или Gitea): выполняется до
  записи в репозиторий и отклоняет **сам push**, обойти его с клиента нечем.
  Именно так делают, когда нужно жёстко: «запушить нарушение невозможно».

Разница принципиальная: локальный хук — подсказка себе, серверный — правило для
всех. Поэтому в проектах ставят и то и другое: локальный, чтобы узнать об ошибке
за секунду до коммита, серверный — чтобы её нельзя было протащить.
