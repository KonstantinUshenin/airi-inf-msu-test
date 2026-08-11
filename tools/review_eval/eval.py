#!/usr/bin/env python3
"""Замер качества промпта авторевью семинаров.

Эталон — замечания, которые преподаватель написал руками в pull request'ах
(`cases.json`). Прогон: для каждого семинара N раз запускается ревью с
проверяемым промптом, затем судья-модель сопоставляет замечания ревью с
эталонными и раскладывает остальные пункты на «важное» и «шум».

    python3 tools/review_eval/eval.py run   --prompt .github/seminar-review-prompt.md --tag base --runs 3
    python3 tools/review_eval/eval.py judge --tag base
    python3 tools/review_eval/eval.py report --tag base --tag v2

Судья ошибается на границе «важное/шум», поэтому его разметка — черновик:
итоговые цифры в отчёте проверяются глазами по `runs/<tag>/*.md`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from review_seminars import call_agent, call_model, join_passes  # noqa: E402
from seminar_context import build_context  # noqa: E402

CASES = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
RUNS_DIR = HERE / "runs"
MODEL = os.environ.get("REVIEW_MODEL", "deepseek-v4-pro")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", MODEL)

JUDGE_PROMPT = """Ты — строгий арбитр. Есть материал учебного семинара, список
замечаний преподавателя (эталон) и текст автоматического ревью. Нужно честно
сопоставить одно с другим.

Правила:
- Эталонное замечание считается НАЙДЕННЫМ, только если в ревью есть пункт про
  ту же самую проблему по сути. Совпадение темы («оба про ssh») не считается.
  Формулировки могут отличаться.
- Отдельно отмечай ЧАСТИЧНЫЕ попадания: ревью говорит про ту же проблему, но
  покрывает её не полностью или заходит с другой стороны. Пример: эталон — «не
  сказано, что rsync работает поверх ssh и чем отличается от scp», ревью —
  «демонстрация rsync локальная, надо показать удалённую». Это `partial`, не
  `matched` и не `extra`. Каждое эталонное замечание попадает максимум в один
  список.
- Каждый пункт ревью, не совпавший ни с одним эталонным, оцени сам. Эталон —
  это то, что преподаватель успел выписать, а не полный список того, что важно;
  пункт вне эталона вполне может быть ценным.
  - "important" — фактическая ошибка, неоднозначная формулировка задачи,
    отсутствие важной для темы вещи, противоречие внутри материала, опасный
    совет. Сюда же — **невоспроизводимость демки**: код упадёт при запуске с
    чистого листа, пропущен шаг подготовки (не создан каталог, не задан
    параметр), пример противоречит тому, что было в предыдущей ячейке, ячейки
    не проходят по порядку. Материал занятия исполняется вживую, поэтому такое
    ломает семинар и это важно, даже если выглядит мелкой технической правкой.
  - "minor" — мелочь или вкусовщина: переформулировать фразу, добавить
    необязательную деталь, стилистика.
  - "wrong" — неверно по факту, или требует того, что в материале уже есть,
    или противоречит правилам курса.
- Если ревью повторяет одно и то же разными словами, второй пункт — "minor".
- Не поддавайся на уверенный тон ревью: проверяй по тексту материала.

Ответ — ТОЛЬКО JSON без markdown-обрамления:
{"matched": [{"id": "...", "quote": "цитата из ревью"}],
 "partial": [{"id": "...", "quote": "цитата из ревью", "why": "чего не хватает"}],
 "extra": [{"text": "кратко пункт ревью", "verdict": "important|minor|wrong",
            "why": "одна строка"}]}
"""


# Второй судья — Claude в headless-режиме. Нужен не для экономии (запрос к
# DeepSeek стоит копейки), а чтобы судья не совпадал с ревьюером: одна и та же
# модель склонна засчитывать свои же формулировки. Токен берётся из юнита
# claude-relay, потому что ~/.claude/.credentials.json бывает просроченным.
CLAUDE_BIN = os.environ.get(
    "CLAUDE_BIN", "/home/dtarasov/workspace/pcc/node_modules/.bin/claude"
)
CLAUDE_JUDGE_MODEL = os.environ.get("CLAUDE_JUDGE_MODEL", "sonnet")
CLAUDE_REVIEW_MODEL = os.environ.get("CLAUDE_REVIEW_MODEL", "sonnet")
JUDGE_SUFFIX = {"api": ".judge.json", "claude": ".judge-claude.json"}


def claude_token() -> str:
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
    if token:
        return token
    unit = subprocess.run(
        ["systemctl", "--user", "show", "claude-relay", "-p", "Environment"],
        capture_output=True,
        text=True,
    ).stdout
    for item in unit.removeprefix("Environment=").split():
        if item.startswith("CLAUDE_CODE_OAUTH_TOKEN="):
            return item.split("=", 1)[1]
    raise SystemExit("нет CLAUDE_CODE_OAUTH_TOKEN (ни в env, ни в юните claude-relay)")


def call_claude(prompt: str, *, model: str, token: str, timeout: int = 900) -> str:
    """Один headless-вызов Claude Code. Тулзы запрещены: судье нечего открывать,
    весь материал уже в промпте, а Read по диску сделал бы прогон невоспроизводимым."""
    result = subprocess.run(
        [
            CLAUDE_BIN, "-p", "--model", model,
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--disallowed-tools", "Bash", "Read", "Write", "Edit", "Glob",
            "Grep", "WebFetch", "WebSearch", "Task", "Agent",
        ],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": token},
    )
    if result.returncode != 0:
        raise SystemExit(f"claude вернул {result.returncode}: {result.stderr[:500]}")
    return result.stdout


# Инструменты у Claude Code свои, родные. Промпт написан под наши
# list_files/read_file/grep, поэтому для этого бэкенда подменяем описание
# инструментов — всё остальное в промпте остаётся дословно тем же, иначе
# сравнение моделей превратится в сравнение двух разных промптов.
CLAUDE_TOOLS_BLURB = """- `Glob(pattern)` — что вообще есть, например `seminars/*` или
  `lectures/**/*.md`;
- `Read(file_path)` — прочитать файл (ноутбуки читаются по ячейкам);
- `Grep(pattern, glob)` — найти, где ещё встречается понятие."""

OUR_TOOLS_BLURB = """- `list_files(pattern)` — что вообще есть, например `seminars/*` или
  `lectures/**/*.md`;
- `read_file(path)` — прочитать файл; ноутбуки отдаются развёрнутыми в markdown
  с той же нумерацией ячеек, что и материал ниже;
- `grep(pattern, glob)` — найти, где ещё встречается понятие."""


def call_claude_agent(prompt: str, *, repo: Path, model: str, token: str) -> str:
    """Ревью силами Claude Code: те же критерии, та же выдача, другая модель.

    Работает из каталога репозитория, поэтому родные Read/Glob/Grep видят ровно
    тот же материал, что наши инструменты у DeepSeek. Правки и шелл запрещены.
    """
    prompt = prompt.replace(OUR_TOOLS_BLURB, CLAUDE_TOOLS_BLURB)
    result = subprocess.run(
        [
            CLAUDE_BIN, "-p", "--model", model,
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--allowed-tools", "Read", "Glob", "Grep",
            "--disallowed-tools", "Bash", "Write", "Edit", "WebFetch",
            "WebSearch", "Task", "Agent",
        ],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=1800,
        cwd=str(repo),
        env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": token},
    )
    if result.returncode != 0:
        raise SystemExit(f"claude вернул {result.returncode}: {result.stderr[:500]}")
    return result.stdout


def check_case_material(case: dict) -> Path:
    """Проверить, что кейс стоит на том состоянии материала, к которому писались
    замечания.

    Грабли, на которых замер один раз уже соврал: рабочая копия PR стояла на
    голове ветки, а автор к тому моменту уже починил всё по замечаниям. Ревью
    физически не могло их найти, и три кейса из четырёх показывали ноль не
    потому, что промпт плохой.
    """
    repo = Path(case["repo"])
    expected = case.get("commit")
    if not expected:
        raise SystemExit(f"{case['id']}: в cases.json не указан commit")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if head != expected:
        raise SystemExit(
            f"{case['id']}: {repo} стоит на {head[:8] or '???'}, "
            f"а замечания писались к {expected[:8]}. "
            f"Почини: git worktree add --detach {repo} {expected[:8]}"
        )
    return repo


def case_by_id(case_id: str) -> dict:
    for case in CASES:
        if case["id"] == case_id:
            return case
    raise SystemExit(f"нет кейса {case_id}")


def api_key() -> str:
    key = os.environ.get("REVIEW_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise SystemExit("нет REVIEW_API_KEY / DEEPSEEK_API_KEY")
    return key


def do_run(args: argparse.Namespace) -> None:
    # В --prompt можно передать несколько файлов через запятую: тогда ревью
    # идёт в несколько независимых проходов, у каждого свой список категорий и
    # свой потолок пунктов. Смысл — не дать дешёвым техническим замечаниям
    # съесть общий лимит: при одном проходе они находятся первыми и вытесняют
    # содержательные пробелы, которые надо думать.
    passes = [Path(part).resolve() for part in args.prompt.split(",")]
    criteria_parts = [path.read_text(encoding="utf-8") for path in passes]
    key = api_key() if args.backend == "api" else ""
    token = claude_token() if args.backend == "claude" else ""
    jobs = []
    for case in CASES:
        if args.case and case["id"] not in args.case:
            continue
        repo = check_case_material(case)
        context = build_context(repo, [repo / case["seminar"]])
        for index in range(1, args.runs + 1):
            out = RUNS_DIR / args.tag / f"{case['id']}.run{index}.md"
            if out.exists() and not args.force:
                continue
            jobs.append(
                (out, [c + "\n\n" + context for c in criteria_parts], repo)
            )

    def work(job):
        out, prompts, repo = job
        chunks = []
        for prompt in prompts:
            if args.backend == "claude":
                chunks.append(
                    call_claude_agent(
                        prompt, repo=repo, model=CLAUDE_REVIEW_MODEL, token=token
                    )
                )
            elif args.tools:
                chunks.append(
                    call_agent(
                        prompt,
                        repo=repo,
                        model=MODEL,
                        api_key=key,
                        temperature=args.temperature,
                    )
                )
            else:
                chunks.append(
                    call_model(
                        prompt,
                        model=MODEL,
                        api_key=key,
                        temperature=args.temperature,
                    )
                )
        text = join_passes(chunks)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        return out.name

    if not jobs:
        print("нечего запускать (используй --force для перезапуска)")
        return
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for name in pool.map(work, jobs):
            print("готово:", name)


def parse_judgement(raw: str) -> dict:
    """Вытащить JSON из ответа судьи.

    Судья иногда обрамляет ответ ```json, иногда дописывает фразу до или после.
    Берём самый внешний объект по первой `{` и последней `}`; если и он не
    разбирается — возвращаем пустую разметку с полем `_raw`, чтобы прогон было
    видно как испорченный, а не как «ревью ничего не нашло».
    """
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict) and "matched" in data and "extra" in data:
            return data
    return {"matched": [], "extra": [], "_raw": raw}


def do_judge(args: argparse.Namespace) -> None:
    suffix = JUDGE_SUFFIX[args.backend]
    key = api_key() if args.backend == "api" else ""
    token = claude_token() if args.backend == "claude" else ""
    files = sorted((RUNS_DIR / args.tag).glob("*.run*.md"))
    jobs = [f for f in files if args.force or not f.with_suffix(suffix).exists()]

    def work(path: Path):
        case = case_by_id(path.name.split(".")[0])
        repo = check_case_material(case)
        material = build_context(repo, [repo / case["seminar"]])
        remarks = "\n".join(
            f"- {r['id']}: {r['text']}" for r in case["remarks"]
        )
        prompt = (
            JUDGE_PROMPT
            + "\n\n# Замечания преподавателя (эталон)\n\n"
            + remarks
            + "\n\n# Текст автоматического ревью\n\n"
            + path.read_text(encoding="utf-8")
            + "\n\n# Материал семинара\n\n"
            + material
        )
        if args.backend == "claude":
            raw = call_claude(prompt, model=CLAUDE_JUDGE_MODEL, token=token)
        else:
            raw = call_model(prompt, model=JUDGE_MODEL, api_key=key, temperature=0.0)
        data = parse_judgement(raw)
        path.with_suffix(suffix).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if "_raw" in data:
            return f"{path.name} — НЕ РАЗОБРАН ответ судьи, считать нельзя"
        return path.name

    if not jobs:
        print("всё уже отсужено")
        return
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for name in pool.map(work, jobs):
            print("отсужено:", name)


def do_report(args: argparse.Namespace) -> None:
    suffix = JUDGE_SUFFIX[args.backend]
    rows = []
    for tag in args.tag:
        for case in CASES:
            judgements = sorted((RUNS_DIR / tag).glob(f"{case['id']}.run*{suffix}"))
            if not judgements:
                continue
            hits, important, minor, wrong, total = [], [], [], [], len(case["remarks"])
            partials: list[int] = []
            found_ids: set[str] = set()
            partial_ids: set[str] = set()
            broken = 0
            for path in judgements:
                data = json.loads(path.read_text(encoding="utf-8"))
                if "_raw" in data:  # ответ судьи не разобрался — не считаем
                    broken += 1
                    continue
                ids = {m["id"] for m in data.get("matched", [])}
                found_ids |= ids
                hits.append(len(ids))
                pids = {p["id"] for p in data.get("partial", [])} - ids
                partial_ids |= pids
                partials.append(len(pids))
                verdicts = [e.get("verdict") for e in data.get("extra", [])]
                important.append(verdicts.count("important"))
                minor.append(verdicts.count("minor"))
                wrong.append(verdicts.count("wrong"))
            if not hits:  # все ответы судьи испорчены — считать нечего
                print(f"! {tag}/{case['id']}: {broken} судейских ответов не разобрано")
                continue
            mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
            rows.append(
                {
                    "tag": tag,
                    "case": case["id"],
                    "runs": len(hits),
                    "broken": broken,
                    "gt_total": total,
                    "gt_hits_avg": round(mean(hits), 1),
                    "gt_hits_union": len(found_ids),
                    "recall_avg": round(100 * mean(hits) / total),
                    "partial_avg": round(mean(partials), 1),
                    "partial_union": len(partial_ids - found_ids),
                    "important_avg": round(mean(important), 1),
                    "noise_avg": round(mean(minor) + mean(wrong), 1),
                    "missed": ",".join(
                        r["id"]
                        for r in case["remarks"]
                        if r["id"] not in found_ids | partial_ids
                    ),
                }
            )
    print(f"судья: {args.backend}")
    header = (
        "| промпт | семинар | прогонов | эталон | нашла ср. | нашла ∪ | recall | "
        "частично ∪ | важное ср. | шум ср. | не нашла (∪ прогонов) |"
    )
    print(header)
    print("|---" * 11 + "|")
    for r in rows:
        print(
            f"| {r['tag']} | {r['case']} | {r['runs']} | {r['gt_total']} | "
            f"{r['gt_hits_avg']} | {r['gt_hits_union']} | {r['recall_avg']}% | "
            f"{r['partial_union']} | {r['important_avg']} | {r['noise_avg']} | "
            f"{r['missed']} |"
        )
    (RUNS_DIR / f"report-{args.backend}.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run")
    run.add_argument("--prompt", required=True)
    run.add_argument("--tag", required=True)
    run.add_argument("--runs", type=int, default=3)
    run.add_argument("--case", action="append")
    run.add_argument("--temperature", type=float, default=0.3)
    run.add_argument("--jobs", type=int, default=6)
    run.add_argument("--force", action="store_true")
    run.add_argument(
        "--backend",
        choices=("api", "claude"),
        default="api",
        help="кто пишет ревью: DeepSeek через API или Claude Code",
    )
    run.add_argument(
        "--tools",
        action="store_true",
        help="дать ревьюеру читать репозиторий (агентный режим)",
    )
    run.set_defaults(func=do_run)

    judge = sub.add_parser("judge")
    judge.add_argument("--tag", required=True)
    judge.add_argument("--backend", choices=("api", "claude"), default="api")
    judge.add_argument("--jobs", type=int, default=6)
    judge.add_argument("--force", action="store_true")
    judge.set_defaults(func=do_judge)

    report = sub.add_parser("report")
    report.add_argument("--tag", action="append", required=True)
    report.add_argument("--backend", choices=("api", "claude"), default="api")
    report.set_defaults(func=do_report)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
