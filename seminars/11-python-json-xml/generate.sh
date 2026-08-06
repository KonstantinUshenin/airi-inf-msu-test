#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
assets_dir="$script_dir/assets"

rm -rf -- "$assets_dir"
mkdir -p \
  "$assets_dir/B1" "$assets_dir/B2" "$assets_dir/B3" "$assets_dir/B4" "$assets_dir/B5" \
  "$assets_dir/M1" "$assets_dir/M2" "$assets_dir/M4" "$assets_dir/M5" \
  "$assets_dir/H2" "$assets_dir/H3" "$assets_dir/H5/pages" \
  "$assets_dir/HOME1" "$assets_dir/HOME2" "$assets_dir/HOME3/pages"

cat > "$assets_dir/api_server.py" <<'PY'
import json

from fastapi import FastAPI, Request


app = FastAPI(title="Seminar 11 API")

REPOSITORIES = [
    {"id": 1, "name": "python-basics", "description": "Python examples for beginners"},
    {"id": 2, "name": "learn-python", "description": "Short Python tasks"},
    {"id": 3, "name": "python-web", "description": "Web applications in Python"},
    {"id": 4, "name": "python-tests", "description": "Testing Python programs"},
    {"id": 5, "name": "python-xml", "description": "Read XML with Python"},
    {"id": 6, "name": "python-tools", "description": "Useful Python tools"},
    {"id": 7, "name": "linux-notes", "description": "Linux command notes"},
    {"id": 8, "name": "python-async", "description": "Async Python examples"},
]

ITEMS = [
    {"id": 1, "title": "JSON"},
    {"id": 2, "title": "XML"},
    {"id": 3, "title": "HTTP"},
    {"id": 4, "title": "HTML"},
    {"id": 5, "title": "OpenAI API"},
]


@app.get("/repositories")
def repositories(q: str, page: int = 1, per_page: int = 3):
    query = q.lower()
    found = [
        repository
        for repository in REPOSITORIES
        if query in repository["name"].lower()
        or query in repository["description"].lower()
    ]
    start = (page - 1) * per_page
    return {
        "total_count": len(found),
        "incomplete_results": False,
        "page": page,
        "per_page": per_page,
        "items": found[start:start + per_page],
    }


@app.api_route("/echo", methods=["QUERY", "POST"])
async def echo(request: Request):
    raw_body = await request.body()
    body = json.loads(raw_body) if raw_body else None
    return {
        "method": request.method,
        "body": body,
        "hasBody": bool(raw_body),
    }


@app.get("/items")
def items(page: int = 1, per_page: int = 2):
    start = (page - 1) * per_page
    selected = ITEMS[start:start + per_page]
    next_page = page + 1 if start + per_page < len(ITEMS) else None
    return {"items": selected, "next": next_page}


@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [{"id": "seminar-chat", "object": "model"}],
    }


@app.post("/v1/chat/completions")
def chat_completions(payload: dict):
    messages = payload.get("messages", [])
    user_messages = [
        message
        for message in messages
        if message.get("role") == "user"
    ]
    last_text = user_messages[-1].get("content", "") if user_messages else ""
    answer = (
        f"Вы написали: {last_text}. "
        f"Сообщений пользователя в истории: {len(user_messages)}."
    )
    return {
        "id": "chatcmpl-seminar",
        "object": "chat.completion",
        "created": 0,
        "model": payload.get("model", "seminar-chat"),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }
PY

cat > "$assets_dir/B1/students.json" <<'EOF'
[
  {"name": "Анна", "group": "ML-01", "score": 86},
  {"name": "Илья", "group": "ML-01", "score": 73},
  {"name": "Мария", "group": "ML-02", "score": 64},
  {"name": "Олег", "group": "ML-02", "score": 91}
]
EOF
cp "$assets_dir/B1/students.json" "$assets_dir/B2/students.json"
cp "$assets_dir/B1/students.json" "$assets_dir/M2/students.json"

cat > "$assets_dir/B3/measurements.json" <<'EOF'
{
  "person": "Анна",
  "measurements": [
    {"date": "2025-01-15", "values": {"height_cm": 164, "weight_kg": 56.2}},
    {"date": "2025-03-20", "values": {"height_cm": 165, "weight_kg": 57.0}},
    {"date": "2025-05-18", "values": {"height_cm": 166}},
    {"date": "2025-07-22", "values": {"weight_kg": 58.1}},
    {"date": "2025-09-10", "values": {"height_cm": "167", "weight_kg": false}},
    {"date": "2025-11-03", "values": null}
  ]
}
EOF

cat > "$assets_dir/B4/records.json" <<'EOF'
[
  {"name": "Анна", "score": 82},
  {"name": "", "score": 70},
  {"name": "Илья"},
  {"name": "Мария", "score": "90"},
  ["not", "an", "object"],
  {"name": "Олег", "score": 77.5}
]
EOF

cat > "$assets_dir/B5/books.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<library>
  <catalog kind="current">
    <book id="b1"><title>Python для начинающих</title><author>А. Автор</author><price>1200.50</price></book>
    <book id="b2"><title>Linux в работе</title><author>Б. Автор</author><price>900.00</price></book>
  </catalog>
  <catalog kind="archive">
    <book id="b3"><title>Unix прошлого века</title><author>В. Автор</author><price>1500.00</price></book>
  </catalog>
</library>
EOF
cp "$assets_dir/B5/books.xml" "$assets_dir/M1/books.xml"

cat > "$assets_dir/M4/page.html" <<'EOF'
<!doctype html>
<html lang="ru">
  <head><meta charset="utf-8"><title>Каталог оборудования</title></head>
  <body>
    <a href="/items/keyboard">Клавиатура</a>
    <a href="mouse.html">Мышь</a>
    <a href="https://example.org/help">Помощь</a>
  </body>
</html>
EOF

cat > "$assets_dir/M5/products.html" <<'EOF'
<!doctype html>
<html lang="ru"><body>
  <article class="product"><span class="name">Keyboard</span><span class="price">4900</span></article>
  <article class="product"><span class="name">Mouse</span><span class="price">2 100,50</span></article>
  <article class="product"><span class="name">Broken price</span><span class="price">unknown</span></article>
  <article class="product"><span class="name">Missing price</span></article>
</body></html>
EOF

cat > "$assets_dir/H2/data.json" <<'EOF'
[
  {"id": 1, "name": "alpha", "metrics": {"loss": 0.31, "accuracy": 0.91}},
  {"id": 2, "name": "beta", "metrics": {"loss": 0.27, "accuracy": 0.93}},
  {"id": 3, "name": "gamma", "metrics": {"loss": 0.44, "accuracy": 0.87}}
]
EOF

cat > "$assets_dir/H3/table.html" <<'EOF'
<!doctype html>
<html lang="ru"><body><table><tbody>
  <tr><td>Keyboard</td><td>input</td><td>4900.00</td><td>yes</td></tr>
  <tr><td>Mouse</td><td>input</td><td>2100.50</td><td>yes</td></tr>
  <tr><td>Monitor</td><td>display</td><td>23000.00</td><td>no</td></tr>
  <tr><td>Broken row</td><td>other</td><td>100.00</td></tr>
</tbody></table></body></html>
EOF

cat > "$assets_dir/HOME2/cache.json" <<'EOF'
[
  {"id": 1, "title": "cached item"}
]
EOF

cat > "$assets_dir/H5/pages/page1.html" <<'EOF'
<!doctype html><html><body>
  <article class="product"><a href="../products/keyboard.html">Keyboard</a></article>
  <a class="page" href="page2.html">Next</a>
</body></html>
EOF
cat > "$assets_dir/H5/pages/page2.html" <<'EOF'
<!doctype html><html><body>
  <article class="product"><a href="../products/mouse.html">Mouse</a></article>
  <article class="product"><a href="../products/keyboard.html">Keyboard duplicate</a></article>
  <a class="page" href="page1.html">Back</a>
  <a class="page" href="page3.html">Next</a>
</body></html>
EOF
cat > "$assets_dir/H5/pages/page3.html" <<'EOF'
<!doctype html><html><body>
  <article class="product"><a href="../products/monitor.html">Monitor</a></article>
  <a class="page" href="page2.html">Back</a>
</body></html>
EOF

cat > "$assets_dir/HOME1/catalog.json" <<'EOF'
[
  {"id": 1, "name": "Keyboard", "price": 4900},
  {"id": 2, "name": "", "price": 2100},
  {"id": 3, "name": "Monitor", "price": "23000"},
  {"id": 4, "name": "Mouse", "price": 2100.5}
]
EOF
cp -R "$assets_dir/H5/pages/." "$assets_dir/HOME3/pages/"

cat > "$assets_dir/README.md" <<'EOF'
# Входные данные

Подкаталоги совпадают с идентификаторами задач. Для `M3`, `H1`, `H4` и `HOME2` запустите локальный сервер:

```bash
uv run uvicorn api_server:app --app-dir assets --port 8000
```

Для H4 задайте `OPENAI_BASE_URL=http://127.0.0.1:8000/v1`, `OPENAI_API_KEY=local` и `OPENAI_MODEL=seminar-chat`.

Для `M4` используйте базовый URL `https://example.test/catalog/page.html`.
EOF

echo "Created $assets_dir"
