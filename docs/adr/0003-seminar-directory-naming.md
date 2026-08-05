# Seminar directories are `NN-slug/`, and the micro-lecture is `demo.ipynb`

Seminars used to live in `seminars/seminar N/` with `lecture.ipynb`, `question.md` and `answer.md`. Every part of that naming had a concrete failure mode, so all of it changed at once — while only three seminars existed and the rename was cheap.

`lecture.ipynb` was the worst offender: the repo also holds real lectures in `lectures/lecture-01-history.qmd`, numbered on their own scale, so `seminars/seminar 2/lecture.ipynb` reads as "lecture 2" to a student and is not. The micro-lecture is now `demo.ipynb`, which cannot collide with `lectures/` no matter how the two numbering schemes drift. The glossary term stays **микро-лекция** — only the file name changed.

The directory name lost its space (`seminar 2` → `02-unix-files`) because this is a course teaching the Unix terminal: a path that needs quoting in every single command is a poor example to ship. It gained a leading zero because `seminar 10` sorts before `seminar 2`, and the plan runs to 16 seminars. It gained a slug because `08-unix-ssh` says what is inside and `seminar 8` does not; `NN` still matches the row number in `seminars/README.md`.

`question.md` → `tasks.md` and `answer.md` → `solutions.md` follow ADR 0002: each file holds a bank of 15–30 items, so the singular was misleading.

Renaming later would have meant rewriting cross-links in every seminar plus outstanding branches; renaming now cost one PR. `assets/` is documented as an optional per-seminar directory but is deliberately not created empty — Git does not track empty directories, and a placeholder file would be noise until a seminar actually ships data.
