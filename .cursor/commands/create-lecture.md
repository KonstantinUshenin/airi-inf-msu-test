# Create lecture (bootstrap and expand)

When the user runs this command, **bootstrap a new lecture** or **expand an existing draft** for a given **lecture number** and **theme** (topic).

Ask the user for:
- **Number** — lecture number (e.g. `5`, `12`). Must match a row in `lectures/README.md` (plan).
- **Theme** — short topic name in English for the subtitle and filename slug (e.g. "Architecture of Computers", "Text Data").

Then create or expand the lecture file, following the **Lecture format and structure** documented below.

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
   - List of main parts as `###` subsections (3–6 items). Each `###` is one high-level block of the lecture and maps to a `#` section in the main content.

2. **Author notes**
   - Paragraph: `**Для авторов. Заметки:**` followed by a bullet list.
   - Content: key terms with translations (Russian↔English), list of diagrams/images referenced, summary of what was added or changed, TODOs for future expansion.
   - Example: `- Термины: прерывание (interrupt), режим ядра/пользователя (kernel/user mode).`

3. **Main content**
   - Multiple `#` titles — one per `###` item in the Plan. Each `#` is a **major part** of the lecture.
   - Several `##` sections under each `#` (each `##` is a **slide** in Beamer; `slide-level: 2` in `_quarto.yml`).
   - Use `---` (horizontal rule) between every two `##` sections for visual separation in source.
   - Deeper headings (`###`, `####`) only inside slides if needed (rarely).

4. **Summary slide** (required)
   - Last `##` section: `## Summary`.
   - Bullet list recapping key takeaways from each major part of the lecture. One bullet per `#` section, roughly.

### Target slide count

- **Bootstrap (initial creation):** generate **25–35 slides** (`##` sections) with real content — not placeholders. The `lectures/README.md` "Содержание" column for the lecture provides the topic seeds; expand each seed into 3–6 slides.
- **Full lecture:** aim for **30–40 slides**. Lectures 01, 03, 11, 12 in this repo range from 1200–2600 lines.
- A lecture with fewer than 20 slides is too thin. More than 50 slides may be too dense for a single session — consider splitting.

### Slide structure patterns

Every `##` slide should follow one of these patterns. **The two-column layout is the default** — use it for most slides.

**Pattern 1: Two-column (default, ~80% of slides)**

```markdown
## Slide title

::: columns
::: column

- **Concept** — definition or explanation.
  - Sub-point with detail.
- **Another concept** — …

:::
::: column

| Col A | Col B |
|-------|-------|
| …     | …     |

:::
:::
```

Left column = bullets, definitions, explanations.
Right column = one of: comparison table, code example, image/diagram, or secondary bullet list.

**Pattern 2: Full-width (for code-heavy or diagram-heavy slides)**

```markdown
## Slide title

- Brief context bullet.

\`\`\`python
# code example
\`\`\`
```

Use when a code block or diagram needs the full width.

**Pattern 3: Summary / bullet-only**

```markdown
## Summary

- Key takeaway 1.
- Key takeaway 2.
```

Used for the final summary slide or transitional slides.

### Content quality guidelines

These guidelines come from building lectures in this repo and reflect what makes slides effective.

**1. Start each `#` section with a "What is X?" or overview slide.**
The first `##` under a new `#` should orient the student: define the topic, explain why it matters, and preview what follows. Example: "What is an Operating System?" before diving into CPU modes.

**2. Include code examples on most slides.**
This is a CS course. Use real, runnable code snippets — not pseudocode. Prefer Python and C for systems topics; use `bash` for command-line tools. Keep examples short (5–20 lines) and self-contained.

**3. Use comparison tables liberally.**
Tables are an excellent way to contrast related concepts (e.g. threads vs processes, static vs dynamic linking, container vs VM). Use concrete values — never vague entries like "Large"; write "16 TiB" instead.

**4. Include practical/tool slides.**
For every major concept, consider a "how to observe/debug this" slide. Examples: `strace` for system calls, `readelf` for ELF files, `ps aux` for processes, `ls -i` for inodes, `ldd` for shared libraries.

**5. Include classic problems and attack/failure scenarios.**
For theory-heavy topics, add a concrete worked example or classic problem: buffer overflow anatomy, dining philosophers, producer-consumer, convoy effect demo, etc. These make abstract concepts tangible.

**6. One idea per slide.**
Each `##` should cover one concept. If a slide has more than 2 top-level bullet groups, it probably should be split. A slide that needs scrolling in the PDF is too long.

**7. Use bold for key terms on first introduction.**
Format: `**term** — definition or explanation.` This makes slides scannable.

**8. Separate `---` between every pair of `##` slides.**
Always place a `---` horizontal rule between consecutive `##` sections. This is required for correct Beamer rendering and visual separation in source.

**9. Never leave trailing spaces.**
Check for and remove trailing whitespace on every line.

### Content patterns (formatting)

- **Two-column layout (Quarto):**
  - Use `::: columns` / `::: column` / `:::` for side-by-side content.
  - Often: left column = bullets/definitions, right column = table, image, or code.

- **Lists:** Prefer `-` bullets; use nested `  -` for sub-items (2-space indent).

- **Images:** Paths like `![](images/Figure_Name.png)` or `![](plots/diagram.dot)`. Put image files under `lectures/images/` (create the directory if missing). For diagrams, `lectures/plots/` is also used.

- **Code:** Use fenced blocks with language (e.g. ` ```python `, ` ```bash `, ` ```c `). Keep examples short and runnable. Add brief comments inside code, not long explanations.

- **Tables:** Standard Markdown tables; they work inside columns. Use concrete values. Align columns with spaces for readability in source.

- **`text` code blocks:** Use ` ```text ` for non-code output (command output, file layouts, ASCII diagrams).

### Project context

- **Quarto:** `_quarto.yml` renders `lectures/*.qmd` to Beamer PDF (`pdf/`), `lang: ru`, `slide-level: 2`.
- **Plan of lectures:** `lectures/README.md` contains the full table (in Russian): №, Тема, Содержание. Use the "Содержание" column to derive ALL subsections and topic seeds — every bullet in that column should map to at least one `##` slide.
- **Reference lectures:** `lecture-03-os.qmd` (~35 slides, 1200 lines) and `lecture-11-hierarchy.qmd` (~60 slides, 2500 lines) are good examples of complete lectures.

### Bootstrap checklist

When creating a new lecture:

1. Read `lectures/README.md` to find the **number**, **theme**, and **content seeds** (Содержание column) for the target lecture.
2. Choose **slug** from theme (e.g. "Text Data" → `text-data` or reuse existing slug from README row).
3. Create `lectures/lecture-NN-slug.qmd` with:
   - Correct front matter (subtitle = "Lecture NN — Theme Name [EARLY DRAFT]").
   - `## Plan` with 3–6 `###` items derived from the README content seeds, grouped logically.
   - Author notes (`**Для авторов. Заметки:**`) with key terms and TODOs.
   - **Full content:** one `#` section per Plan item, each with 4–8 `##` slides of real content (not placeholders). Follow the slide structure patterns and content quality guidelines above.
   - A `## Summary` slide at the end.
   - `---` separators between every pair of `##` sections.
4. If the lecture will need images, ensure `lectures/images/` exists (create if needed); no need to add image files during bootstrap.
5. Do not modify other lectures or README unless the user asks.

### Expansion checklist

When expanding an existing draft:

1. Read the current lecture file to understand what exists.
2. Identify **gaps** — compare existing slides against the README "Содержание" column and the Plan `###` items. Every content seed should be covered by at least one slide.
3. For each major topic already present, consider adding:
   - A deeper dive slide (e.g. mechanism details, worked example).
   - A practical/tool slide (e.g. `strace`, `readelf`, `ldd`).
   - A classic problem or attack scenario slide.
   - A comparison table slide if two or more related concepts exist.
4. Add new slides at logical positions within the existing `#` sections. Maintain `---` separators.
5. Update the `## Summary` to reflect new content.
6. Update author notes to document what was added.
7. Check for trailing spaces.
