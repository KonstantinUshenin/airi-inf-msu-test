# Примеры решений

Все решения запускаются из каталога семинара (`~/seminar-11/`) после
`./generate.sh`: входные файлы читаются из `assets/{ID}/`, результаты
создаются в текущем каталоге. Для M3, H1 и H4 нужен запущенный учебный сервер
(`uv run uvicorn api_server:app --app-dir assets --port 8000`).

## База

### B1

```python
import json

with open("assets/B1/students.json", encoding="utf-8") as file:
    students = json.load(file)

scores = []
names = []
for student in students:
    names.append(student["name"])
    scores.append(student["score"])

summary = {
    "count": len(students),
    "average_score": sum(scores) / len(scores) if scores else None,
    "names": names,
}

with open("summary.json", "w", encoding="utf-8") as file:
    json.dump(summary, file, ensure_ascii=False, indent=2)
```

### B2

```python
import json

with open("assets/B2/students.json", encoding="utf-8") as file:
    students = json.load(file)

passed = []
for student in students:
    if student["score"] >= 70:
        passed.append(student)

with open("passed.json", "w", encoding="utf-8") as file:
    json.dump(passed, file, ensure_ascii=False, indent=2)
```

### B3

```python
import json

with open("assets/B3/measurements.json", encoding="utf-8") as file:
    diary = json.load(file)

timeline = []
dates_without_height = []
dates_without_weight = []
for measurement in diary["measurements"]:
    date = measurement["date"]
    values = measurement.get("values")
    if not isinstance(values, dict):
        dates_without_height.append(date)
        dates_without_weight.append(date)
        continue

    height = values.get("height_cm")
    weight = values.get("weight_kg")
    if type(height) not in (int, float):
        dates_without_height.append(date)
    if type(weight) not in (int, float):
        dates_without_weight.append(date)
    if type(height) in (int, float) and type(weight) in (int, float):
        timeline.append({
            "date": date,
            "height_cm": height,
            "weight_kg": weight,
        })

summary = {
    "person": diary["person"],
    "measurement_count": len(diary["measurements"]),
    "timeline": timeline,
    "dates_without_height": dates_without_height,
    "dates_without_weight": dates_without_weight,
}

with open("measurements-summary.json", "w", encoding="utf-8") as file:
    json.dump(summary, file, ensure_ascii=False, indent=2)
```

### B4

```python
import json

with open("assets/B4/records.json", encoding="utf-8") as file:
    records = json.load(file)

valid = []
errors = []
for index, record in enumerate(records):
    if not isinstance(record, dict):
        errors.append({"index": index, "reason": "record is not an object"})
        continue

    name = record.get("name")
    score = record.get("score")
    if not isinstance(name, str) or not name.strip():
        errors.append({"index": index, "reason": "invalid name"})
    elif type(score) not in (int, float):
        errors.append({"index": index, "reason": "invalid score"})
    else:
        valid.append(record)

with open("valid.json", "w", encoding="utf-8") as file:
    json.dump(valid, file, ensure_ascii=False, indent=2)

with open("errors.json", "w", encoding="utf-8") as file:
    json.dump(errors, file, ensure_ascii=False, indent=2)
```

### B5

```python
import json
import xml.etree.ElementTree as ET

root = ET.parse("assets/B5/books.xml").getroot()
books = []
counts = {}
for catalog in root.findall("catalog"):
    kind = catalog.get("kind")
    counts[kind] = len(catalog.findall("book"))
    for node in catalog.findall("book"):
        books.append({
            "catalog": kind,
            "id": node.get("id"),
            "title": node.findtext("title"),
            "author": node.findtext("author"),
            "price": float(node.findtext("price")),
        })

with open("books.json", "w", encoding="utf-8") as file:
    json.dump(books, file, ensure_ascii=False, indent=2)

summary = {
    "counts": counts,
    "total_price": sum(book["price"] for book in books),
}
with open("books-summary.json", "w", encoding="utf-8") as file:
    json.dump(summary, file, ensure_ascii=False, indent=2)
```

## Среднее

### M1

```python
import json
from lxml import etree

document = etree.parse("assets/M1/books.xml")
result = {
    "current_expensive_titles": document.xpath(
        "/library/catalog[@kind='current']/book[price > 1000]/title/text()"
    ),
    "archive_titles": document.xpath(
        "/library/catalog[@kind='archive']/book/title/text()"
    ),
    "b2_authors": document.xpath("//book[@id='b2']/author/text()"),
}

with open("xpath-result.json", "w", encoding="utf-8") as file:
    json.dump(result, file, ensure_ascii=False, indent=2)
```

### M2

```python
import json
import xml.etree.ElementTree as ET

with open("assets/M2/students.json", encoding="utf-8") as file:
    students = json.load(file)

root = ET.Element("students")
for student in students:
    node = ET.SubElement(root, "student")
    ET.SubElement(node, "name").text = student["name"]
    ET.SubElement(node, "group").text = student["group"]
    ET.SubElement(node, "score").text = str(student["score"])

ET.ElementTree(root).write(
    "students.xml",
    encoding="utf-8",
    xml_declaration=True,
)
```

### M3

```python
import json
import requests

url = "http://127.0.0.1:8000/repositories"
response = requests.get(
    url,
    params={"q": "python", "page": 2, "per_page": 3},
    timeout=10,
)
response.raise_for_status()
data = response.json()

with open("python-repositories.json", "w", encoding="utf-8") as file:
    json.dump(data["items"], file, ensure_ascii=False, indent=2)

metadata = {
    "total_count": data["total_count"],
    "incomplete_results": data["incomplete_results"],
    "status_code": response.status_code,
    "url": response.url,
}
with open("response-meta.json", "w", encoding="utf-8") as file:
    json.dump(metadata, file, ensure_ascii=False, indent=2)
```

### M4

```python
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup

base_url = "https://example.test/catalog/page.html"
with open("assets/M4/page.html", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

links = []
for link in soup.select("a"):
    links.append({
        "text": link.get_text(strip=True),
        "url": urljoin(base_url, link.get("href")),
    })

result = {
    "title": soup.title.get_text(strip=True),
    "links": links,
}
with open("page.json", "w", encoding="utf-8") as file:
    json.dump(result, file, ensure_ascii=False, indent=2)
```

### M5

```python
import json
from bs4 import BeautifulSoup

with open("assets/M5/products.html", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

products = []
errors = []
for index, card in enumerate(soup.select(".product")):
    name_node = card.select_one(".name")
    price_node = card.select_one(".price")

    if name_node is None or price_node is None:
        errors.append({"index": index, "reason": "missing name or price"})
        continue

    try:
        price = float(price_node.get_text(strip=True).replace(" ", "").replace(",", "."))
    except ValueError:
        errors.append({"index": index, "reason": "invalid price"})
        continue

    products.append({
        "name": name_node.get_text(strip=True),
        "price": price,
    })

with open("products.json", "w", encoding="utf-8") as file:
    json.dump(products, file, ensure_ascii=False, indent=2)

with open("product-errors.json", "w", encoding="utf-8") as file:
    json.dump(errors, file, ensure_ascii=False, indent=2)
```

## Сложное

### H1

```python
import json
import requests

url = "http://127.0.0.1:8000/echo"
body = {"category": "books", "max_price": 1500}

result = {}
for method in ("QUERY", "POST"):
    response = requests.request(
        method,
        url,
        json=body,
        timeout=10,
    )
    response.raise_for_status()
    echoed = response.json()
    result[method.lower()] = {
        "status_code": response.status_code,
        "method": echoed["method"],
        "body": echoed["body"],
        "hasBody": echoed["hasBody"],
    }

with open("query-post.json", "w", encoding="utf-8") as file:
    json.dump(result, file, ensure_ascii=False, indent=2)
```

### H2

```python
import json
import xml.etree.ElementTree as ET

with open("assets/H2/data.json", encoding="utf-8") as file:
    source = json.load(file)

root = ET.Element("records")
for record in source:
    node = ET.SubElement(root, "record", id=str(record["id"]))
    ET.SubElement(node, "name").text = record["name"]
    metrics = ET.SubElement(node, "metrics")
    ET.SubElement(metrics, "loss").text = str(record["metrics"]["loss"])
    ET.SubElement(metrics, "accuracy").text = str(record["metrics"]["accuracy"])

ET.ElementTree(root).write("data.xml", encoding="utf-8", xml_declaration=True)

restored = []
for node in ET.parse("data.xml").getroot().findall("record"):
    restored.append({
        "id": int(node.get("id")),
        "name": node.findtext("name"),
        "metrics": {
            "loss": float(node.findtext("metrics/loss")),
            "accuracy": float(node.findtext("metrics/accuracy")),
        },
    })

if restored != source:
    raise ValueError("restored data differs from source")

with open("restored.json", "w", encoding="utf-8") as file:
    json.dump(restored, file, ensure_ascii=False, indent=2)
```

### H3

```python
import json
from bs4 import BeautifulSoup

with open("assets/H3/table.html", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

products = []
for row in soup.select("tbody tr"):
    cells = row.select("td")
    if len(cells) != 4:
        continue

    name, category, price, available = [
        cell.get_text(" ", strip=True) for cell in cells
    ]
    if available.lower() == "yes":
        products.append({
            "name": name,
            "category": category,
            "price": float(price),
        })

products.sort(key=lambda item: item["price"])
with open("available.json", "w", encoding="utf-8") as file:
    json.dump(products, file, ensure_ascii=False, indent=2)
```

### H4

```python
import json
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["OPENAI_BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
)
model = os.environ["OPENAI_MODEL"]
messages = []

while True:
    text = input("Вы: ").strip()
    if text.lower() == "exit":
        break
    if not text:
        continue

    messages.append({"role": "user", "content": text})
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    answer = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    print("Ассистент:", answer)

with open("chat-history.json", "w", encoding="utf-8") as file:
    json.dump(messages, file, ensure_ascii=False, indent=2)
```

### H5

```python
import json
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

pages = Path("assets/H5/pages").resolve()
pending = [pages / "page1.html"]
visited = set()
products = {}

while pending:
    page_path = pending.pop()
    page_url = page_path.as_uri()
    if page_url in visited:
        continue
    visited.add(page_url)

    soup = BeautifulSoup(
        page_path.read_text(encoding="utf-8"),
        "html.parser",
    )

    for card in soup.select(".product"):
        link = card.select_one("a")
        product_url = urljoin(page_url, link.get("href"))
        products[product_url] = {
            "name": link.get_text(strip=True),
            "url": product_url,
        }

    for link in soup.select("a.page"):
        pending.append((page_path.parent / link.get("href")).resolve())

result = list(products.values())
with open("products.json", "w", encoding="utf-8") as file:
    json.dump(result, file, ensure_ascii=False, indent=2)
```
