# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

University course "Informatics. Foundations of Software Development" (MSU/AIRI). Contains Quarto-based Beamer lecture slides (.qmd) and seminar worksheets (Markdown READMEs). All content is in Russian with English slugs/filenames.

## Build commands

```bash
make              # Build all: plots then PDFs
make pdf          # Build lecture PDFs (requires plots built first)
make dot          # Build Graphviz plots (lectures/plots/*.dot → *.png)
make clean        # Remove all build artifacts

# Single lecture
quarto render lectures/lecture-10-encoding.qmd --output-dir pdf
```

**Requirements:** Quarto, XeLaTeX (`texlive-xetex`, `texlive-lang-cyrillic`), Graphviz, Inter font, DejaVu Sans Mono font.

## Repository structure

- `lectures/*.qmd` — Beamer slides rendered via Quarto (`slide-level: 2`, so `##` = slide)
- `lectures/README.md` — lecture plan table (№, theme, content seeds in Russian)
- `lectures/images/` — static images; `lectures/plots/` — Graphviz .dot diagrams
- `seminars/NN_seminar_slug/README.md` — seminar worksheets
- `seminars/README.md` — seminar plan table
- `styles/macros.tex` — shared LaTeX preamble (fonts, Beamer theme)
- `_quarto.yml` — Quarto config (Beamer, XeLaTeX, lang: ru, 16:9 aspect)

## CI/CD

GitHub Actions workflow (`.github/workflows/lectures-pdf-telegram.yml`): on push to `main` with changes in `lectures/`, builds changed lecture PDFs and sends them to Telegram. Uses secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

## Content creation conventions

Detailed conventions for creating lectures and seminars are in Cursor command files — use these as the authoritative reference:

- **Lectures:** `.cursor/commands/create-lecture.md` — file naming (`lectures/lecture-NN-slug.qmd`), YAML front matter, document structure (Plan → Author notes → Main content → Summary), slide patterns (two-column default with `::: columns`), content quality guidelines, target 25-35 slides for bootstrap.
- **Seminars:** `.cursor/commands/create-seminar.md` — folder naming (`seminars/NN_seminar_slug/`), required sections (Цель → Теоретический минимум → Задачи → Бонусные задачи), task design guidelines, 6-10 main tasks for bootstrap.

Key rules across both:
- `---` separator between every pair of `##` sections in lectures
- No trailing whitespace
- Derive all content from the README.md plan tables (Содержание column)
- Use concrete examples, real code, and comparison tables — no placeholders
