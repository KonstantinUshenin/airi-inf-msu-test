# Create lecture (bootstrap)

When the user runs this command, bootstrap a **new lecture** for a given **lecture number** and **theme** (topic).

Ask the user for:
- **Number** — lecture number (e.g. `5`, `12`). Must match a row in `lectures/README.md` (plan).
- **Theme** — short topic name in English for the subtitle and filename slug (e.g. "Architecture of Computers", "Text Data").

Then create the lecture file and optional assets as below, following the **Lecture format and structure** documented in this file.

---

## Lecture format and structure (repo convention)

Use this as the single source of truth for how lectures are formatted in this repo.

### File naming and location

- **Path:** `lectures/lecture-NN-slug.qmd`
- **NN:** zero-padded 2-digit number (e.g. `01`, `10`, `12`).
- **slug:** lowercase English, words hyphenated, no spaces (e.g. `history`, `encoding`, `hierarchy`, `tables`).
- **Example:** Lecture 5 "Technologies of programming" → `lectures/lecture-05-programming.qmd`.

### YAML front matter (required)

Every lecture starts with:

```yaml
---
title: "Informatics. Foundations of Software Development"
subtitle: "Lecture NN — Theme Name [EARLY DRAFT]"
author: "Konstantin Ushenin"
date: "2026"
---
```

- **subtitle:** `Lecture NN — Theme Name [EARLY DRAFT]` (or drop `[EARLY DRAFT]` when not draft). Theme is short, in English.
- **author** and **date** are fixed as above unless the user specifies otherwise.

### Document structure (order)

1. **Plan block**
   - Heading: `## Plan`
   - List of main parts as `###` subsections (3–6 items). Each `###` is one high-level block of the lecture (will map to `#` sections later).

2. **Optional author notes**
   - Paragraph: `**Для авторов. Заметки:**` followed by a short bullet list (translations, TODOs, ideas). Can be omitted in bootstrap.

3. **Main content**
   - One `#` title (lecture theme or first big part).
   - Several `##` sections (each is a **slide** in Beamer; `slide-level: 2` in `_quarto.yml`).
   - Use `---` between sections for visual separation in source.
   - Deeper headings (`###`, `####`) only inside slides if needed.

4. **Repeated big parts**
   - If the Plan has several major blocks, each can be a separate `#` title with its own `##` sections (see `lecture-01-history.qmd`: History of Computers, History of OS, History of Languages, etc.).

### Content patterns

- **Two-column layout (Quarto):**
  - Use `::: columns` / `::: column` / `:::` for side-by-side content.
  - Often: left column = bullets/definitions, right column = table, image, or code.

- **Lists:** Prefer `-` bullets; use nested `  -` for sub-items.

- **Images:** Paths like `![](images/Figure_Name.png)` or `![](plots/diagram.dot)`. Put image files under `lectures/images/` (create the directory if missing). For diagrams, `lectures/plots/` is also used.

- **Code:** Use fenced blocks with language (e.g. ` ```python `, ` ```bash `).

- **Tables:** Standard Markdown tables; they work inside columns.

### Project context

- **Quarto:** `_quarto.yml` renders `lectures/*.qmd` to Beamer PDF (`pdf/`), `lang: ru`, `slide-level: 2`.
- **Plan of lectures:** `lectures/README.md` contains the full table (in Russian): №, Тема, Содержание. Use it to align theme and number and to derive section ideas for the Plan.

### Bootstrap checklist

When creating a new lecture:

1. Resolve **number** and **theme** (and optional slug override).
2. Choose **slug** from theme (e.g. "Text Data" → `text-data` or reuse existing like `encoding` from README).
3. Create `lectures/lecture-NN-slug.qmd` with:
   - Correct front matter (subtitle = "Lecture NN — Theme Name [EARLY DRAFT]").
   - `## Plan` with 3–6 `###` items (aligned to `lectures/README.md` content for that lecture).
   - One `#` title and 2–4 placeholder `##` sections with short bullet content or "TBD".
   - At least one `::: columns` / `::: column` block as example.
4. If the lecture will need images, ensure `lectures/images/` exists (create if needed); no need to add files in bootstrap.
5. Do not modify other lectures or README unless the user asks.
