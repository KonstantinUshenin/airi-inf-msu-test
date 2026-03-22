# Create seminar (bootstrap and expand)

When the user runs this command, **bootstrap a new seminar** or **expand an existing draft** for a given **seminar number** and **theme**.

Ask the user for:
- **Number** — seminar number (e.g. `6`, `12`). Must match a row in `seminars/README.md` (plan).
- **Theme** — short topic name in Russian for title and in English for folder slug (e.g. "Unix-terminal. Работа с сетью" + `network`).

Then create or expand the seminar file, following the **Seminar format and structure** documented below.

---

## Seminar format and structure (repo convention)

Use this as the single source of truth for how seminars are formatted in this repo.

### Folder naming and location

- **Path:** `seminars/NN_seminar_slug/README.md`
- **NN:** zero-padded 2-digit number (e.g. `01`, `06`, `12`).
- **slug:** lowercase English, words joined with `_`, no spaces (e.g. `os`, `network`, `docker`).
- **Example:** Seminar 6 "Unix-terminal. Работа с оборудованием" -> `seminars/06_seminar_os/README.md`.

### Heading and top sections (required)

Every seminar README starts with:

```markdown
# Семинар NN. <Тема>

## Цель

<1 paragraph with practical learning goals>

## Теоретический минимум

- ...
```

- Title format is fixed: `# Семинар NN. <Тема>`.
- `## Цель` should describe practical outcomes and artifacts students must keep.
- `## Теоретический минимум` should contain concise bullets with key concepts needed to defend the seminar.

### Main structure (order)

1. **Goal**
   - Heading: `## Цель`
   - 1 short paragraph, practical and measurable.

2. **Theory minimum**
   - Heading: `## Теоретический минимум`
   - 5-10 bullets with core terms and short explanations.

3. **Tasks**
   - Heading: `## Задачи`
   - Numbered list `1.`, `2.`, ... with detailed actionable subtasks.
   - Most items should include concrete tools/commands/libraries.
   - Keep wording checkable: what to run, what to capture, what to explain in report.

4. **Artifacts/report requirement**
   - After tasks, add a short paragraph requiring storage of report and artifacts (scripts, outputs, screenshots, notebooks, files).

5. **Bonus tasks**
   - Heading: `## Бонусные задачи`
   - 1-3 advanced items for extra points.

### Task design guidelines

These guidelines reflect the format already used in this repo.

1. **Hands-on first:** every major concept must map to an action (command, script, configuration, experiment).
2. **Traceable result:** each task must produce evidence (output, file, screenshot, measurement, short explanation).
3. **Defense-ready theory:** include just enough theory to let seminar tutors ask verification questions.
4. **Progressive complexity:** start with basic inspection/use, then move to scripting/automation, then analysis/debugging.
5. **Fallback path:** if hardware/tool is unavailable (e.g. GPU), specify how to skip or run on remote host.
6. **Concrete verbs:** use "вывести", "написать", "запустить", "зафиксировать", "объяснить".
7. **No placeholders:** avoid "TODO", "дописать позже", "и т.д." in student-facing tasks.
8. **Never leave trailing spaces.**

### Project context

- `seminars/README.md` contains the seminar plan table: `№`, `Блок`, `Тема`, `Содержание`.
- Use the `Содержание` column as mandatory topic seeds: every key item should be covered by at least one task or subtask.
- Seminar directories follow `NN_seminar_slug` convention and contain `README.md`.
- Currently available reference seminar: `seminars/06_seminar_os/README.md`.

### Bootstrap checklist

When creating a new seminar:

1. Read `seminars/README.md` and find the target row by number.
2. Extract topic seeds from `Содержание`.
3. Choose folder slug from theme (English, snake_case), create `seminars/NN_seminar_slug/`.
4. Create `seminars/NN_seminar_slug/README.md` with required sections in the required order:
   - `# Семинар NN. <Тема>`
   - `## Цель`
   - `## Теоретический минимум`
   - `## Задачи`
   - Artifacts/report paragraph
   - `## Бонусные задачи`
5. Generate 6-10 main tasks in `## Задачи`, each with 2-7 subtasks.
6. Ensure each topic seed from `Содержание` appears in at least one task.
7. Keep all instructions executable and checkable in a lab environment.
8. Check and remove trailing spaces.
9. Do not modify other seminar folders or `seminars/README.md` unless user asks.

### Expansion checklist

When expanding an existing seminar draft:

1. Read current `seminars/NN_seminar_slug/README.md`.
2. Compare existing coverage against `seminars/README.md` topic seeds.
3. Add missing tasks and deepen thin tasks with practical subtasks.
4. Improve task observability (explicit artifacts and expected outputs).
5. Add or refine 1-3 bonus tasks.
6. Keep section order and heading names unchanged.
7. Check and remove trailing spaces.
