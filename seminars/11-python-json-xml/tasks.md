# Практическая работа

**Выход:** `.py` или `.ipynb`.

Работаем в домашнем каталоге — `~/seminar-11/`, а не в `/tmp`: `/tmp` вычищается при перезагрузке, а решения понадобятся на защите. Скопируйте в него **содержимое** каталога семинара (`cp -r <репозиторий>/seminars/11-python-json-xml/. ~/seminar-11/`) и все команды выполняйте из `~/seminar-11/` — там же лежит `generate.sh`.

Перед началом установите зависимости и подготовьте входные данные:

```bash
cd ~/seminar-11
uv init --python 3.12    # создаёт pyproject.toml; если проект уже есть — пропустите
uv add requests beautifulsoup4 lxml openai fastapi uvicorn
./generate.sh
```

`generate.sh` создаёт каталог `assets/`: входные файлы каждой задачи лежат в `assets/{ID}/`, учебный сервер — в `assets/api_server.py`. Пути в условиях даны относительно каталога семинара; результаты складывайте рядом, в текущий каталог.

Для сетевых задач (M3, H1, H4) в отдельном терминале запустите учебный сервер и не закрывайте его, пока решаете:

```bash
uv run uvicorn api_server:app --app-dir assets --port 8000
```

## База — 5 задач

### B1. Чтение JSON

**need:** `assets/B1/students.json`.

Пример входного JSON:

```json
[
  {"name": "Анна", "group": "ML-01", "score": 86},
  {"name": "Илья", "group": "ML-01", "score": 73}
]
```

Сохраните в `summary.json` количество студентов, средний балл и список имён.

Пример структуры результата:

```json
{
  "count": 4,
  "average_score": 78.5,
  "names": ["Анна", "Илья", "Мария", "Олег"]
}
```

### B2. Фильтрация JSON

**need:** `assets/B2/students.json`.

Входной JSON имеет ту же структуру, что в B1:

```json
[
  {"name": "Анна", "group": "ML-01", "score": 86},
  {"name": "Мария", "group": "ML-02", "score": 64}
]
```

Сохраните в `passed.json` студентов с результатом не меньше 70. Исходный файл не изменяйте.

Пример структуры результата:

```json
[
  {"name": "Анна", "group": "ML-01", "score": 86}
]
```

### B3. Вложенный JSON

**need:** `assets/B3/measurements.json`.

Пример структуры входного JSON:

```json
{
  "person": "Анна",
  "measurements": [
    {"date": "2025-01-15", "values": {"height_cm": 164, "weight_kg": 56.2}},
    {"date": "2025-05-18", "values": {"height_cm": 166}},
    {"date": "2025-11-03", "values": null}
  ]
}
```

`height_cm` и `weight_kg` могут отсутствовать или иметь неверный тип. Создайте `measurements-summary.json` с полями `person`, `measurement_count`, `timeline`, `dates_without_height`, `dates_without_weight`. В `timeline` оставьте только измерения, где рост и вес являются числами. Ошибочная запись не должна останавливать обработку остальных.

Пример структуры результата:

```json
{
  "person": "Анна",
  "measurement_count": 3,
  "timeline": [
    {"date": "2025-01-15", "height_cm": 164, "weight_kg": 56.2}
  ],
  "dates_without_height": ["2025-11-03"],
  "dates_without_weight": ["2025-05-18", "2025-11-03"]
}
```

### B4. Проверка структуры

**need:** `assets/B4/records.json`.

Пример входного JSON:

```json
[
  {"name": "Анна", "score": 82},
  {"name": "", "score": 70},
  {"name": "Илья"},
  ["not", "an", "object"]
]
```

Корректная запись содержит непустую строку `name` и число `score`. Сохраните корректные записи в `valid.json`, для остальных сохраните индекс и причину в `errors.json`.

Пример `valid.json`:

```json
[
  {"name": "Анна", "score": 82}
]
```

Пример `errors.json`:

```json
[
  {"index": 1, "reason": "invalid name"},
  {"index": 2, "reason": "invalid score"},
  {"index": 3, "reason": "record is not an object"}
]
```

### B5. Чтение XML

**need:** `assets/B5/books.xml`.

Пример структуры XML:

```xml
<library>
  <catalog kind="current">
    <book id="b1">
      <title>Python для начинающих</title>
      <author>А. Автор</author>
      <price>1200.50</price>
    </book>
  </catalog>
  <catalog kind="archive">
    <book id="b3">
      <title>Unix прошлого века</title>
      <author>В. Автор</author>
      <price>1500.00</price>
    </book>
  </catalog>
</library>
```

Создайте `books.json` с названием каталога, `id`, названием книги, автором и ценой. Цены должны быть числами. В `books-summary.json` сохраните количество книг в каждом каталоге и общую стоимость.

Пример структуры `books.json`:

```json
[
  {
    "catalog": "current",
    "id": "b1",
    "title": "Python для начинающих",
    "author": "А. Автор",
    "price": 1200.5
  }
]
```

Пример структуры `books-summary.json`:

```json
{
  "counts": {"current": 2, "archive": 1},
  "total_price": 3600.5
}
```

## Среднее — 5 задач

### M1. XPath

**need:** `assets/M1/books.xml`; `lxml`. Структура XML показана в B5.

Сохраните названия книг дороже 1000 из текущего каталога, названия всех архивных книг и автора книги с `id="b2"` в `xpath-result.json`.

Пример структуры результата:

```json
{
  "current_expensive_titles": ["Python для начинающих"],
  "archive_titles": ["Unix прошлого века"],
  "b2_authors": ["Б. Автор"]
}
```

### M2. Создание XML

**need:** `assets/M2/students.json`.

Пример входного JSON:

```json
[
  {"name": "Анна", "group": "ML-01", "score": 86},
  {"name": "Илья", "group": "ML-01", "score": 73}
]
```

Создайте `students.xml`. Корневой элемент — `students`, каждый студент — отдельный элемент `student` с тремя дочерними элементами.

Пример структуры результата:

```xml
<students>
  <student>
    <name>Анна</name>
    <group>ML-01</group>
    <score>86</score>
  </student>
</students>
```

### M3. REST API

**need:** запущенный `assets/api_server.py`; `requests`.

Строка запроса: `http://127.0.0.1:8000/repositories?q=python&page=2&per_page=3`.

- `q=python` — искать репозитории по слову `python`;
- `page=2` — получить вторую страницу;
- `per_page=3` — получить по три репозитория на странице.

Пример JSON-ответа API:

```json
{
  "total_count": 7,
  "incomplete_results": false,
  "page": 2,
  "per_page": 3,
  "items": [
    {"id": 4, "name": "python-tests", "description": "Testing Python programs"},
    {"id": 5, "name": "python-xml", "description": "Read XML with Python"},
    {"id": 6, "name": "python-tools", "description": "Useful Python tools"}
  ]
}
```

Выполните этот GET-запрос. Сохраните список `items` в `python-repositories.json`, а `total_count`, `incomplete_results`, код состояния и итоговый URL — в `response-meta.json`.

Пример структуры `python-repositories.json`:

```json
[
  {"id": 4, "name": "python-tests", "description": "Testing Python programs"},
  {"id": 5, "name": "python-xml", "description": "Read XML with Python"}
]
```

Пример структуры `response-meta.json`:

```json
{
  "total_count": 7,
  "incomplete_results": false,
  "status_code": 200,
  "url": "http://127.0.0.1:8000/repositories?q=python&page=2&per_page=3"
}
```

### M4. HTML и ссылки

**need:** `assets/M4/page.html`; базовый URL `https://example.test/catalog/page.html`; Beautiful Soup.

Сохраните заголовок и все ссылки в `page.json`. Для каждой ссылки сохраните текст и абсолютный адрес.

Пример структуры результата:

```json
{
  "title": "Каталог оборудования",
  "links": [
    {"text": "Клавиатура", "url": "https://example.test/items/keyboard"},
    {"text": "Мышь", "url": "https://example.test/catalog/mouse.html"}
  ]
}
```

### M5. Карточки товаров

**need:** `assets/M5/products.html`; Beautiful Soup.

Корректная карточка `.product` содержит `.name` и цену в `.price`; часть карточек ошибочна. Цена записана «как на витрине»: разделителем тысяч может стоять пробел, а десятичным разделителем — запятая (`2 100,50` — это `2100.5`). Прямой `float()` на такой строке падает, поэтому её надо привести к виду, который `float()` понимает.

Создайте `products.json`, где названия — строки, цены — числа. Некорректные карточки (нет `.name` или `.price`, либо цена не разбирается как число) сохраните в `product-errors.json`.

Пример `products.json`:

```json
[
  {"name": "Keyboard", "price": 4900.0},
  {"name": "Mouse", "price": 2100.5}
]
```

Пример `product-errors.json`:

```json
[
  {"index": 2, "reason": "invalid price"},
  {"index": 3, "reason": "missing name or price"}
]
```

## Сложное — 5 задач

### H1. QUERY и POST

**need:** запущенный `assets/api_server.py`; `requests`; адрес `http://127.0.0.1:8000/echo`.

Адрес принимает методы QUERY и POST с одинаковым JSON-телом:

```json
{"category": "books", "max_price": 1500}
```

Отправьте оба запроса. Сохраните в `query-post.json` для каждого ответа код состояния, метод и тело, которые увидел сервер, а также `hasBody`.

Пример структуры результата:

```json
{
  "query": {
    "status_code": 200,
    "method": "QUERY",
    "body": {"category": "books", "max_price": 1500},
    "hasBody": true
  },
  "post": {
    "status_code": 200,
    "method": "POST",
    "body": {"category": "books", "max_price": 1500},
    "hasBody": true
  }
}
```

### H2. JSON ↔ XML

**need:** `assets/H2/data.json`.

Пример входного JSON:

```json
[
  {
    "id": 1,
    "name": "alpha",
    "metrics": {"loss": 0.31, "accuracy": 0.91}
  },
  {
    "id": 2,
    "name": "beta",
    "metrics": {"loss": 0.27, "accuracy": 0.93}
  }
]
```

Преобразуйте данные в `data.xml`, затем восстановите `restored.json`. После обратного преобразования значения и числовые типы должны совпасть с исходными. Структура `restored.json` должна совпадать со структурой входного примера.

### H3. HTML-таблица

**need:** `assets/H3/table.html`; Beautiful Soup. Таблица содержит колонки `name`, `category`, `price`, `available`; цена записана с десятичной точкой.

Сохраните доступные товары в `available.json`. Проверьте число ячеек в каждой строке, приведите цены к числам и отсортируйте результат по цене.

Пример структуры результата:

```json
[
  {"name": "Mouse", "category": "input", "price": 2100.5},
  {"name": "Keyboard", "category": "input", "price": 4900.0}
]
```

### H4. Консольный чат

**need:** запущенный `assets/api_server.py`; `openai`; `OPENAI_BASE_URL=http://127.0.0.1:8000/v1`, `OPENAI_API_KEY=local`, `OPENAI_MODEL=seminar-chat`.

Создайте простой консольный чат. Программа читает сообщения пользователя до команды `exit`, отправляет серверу всю накопленную историю и печатает каждый ответ. После завершения сохраните сообщения пользователя и ассистента в `chat-history.json`. Секретный ключ в историю попадать не должен.

Пример структуры `chat-history.json`:

```json
[
  {"role": "user", "content": "Привет!"},
  {
    "role": "assistant",
    "content": "Вы написали: Привет!. Сообщений пользователя в истории: 1."
  }
]
```

### H5. Несколько HTML-страниц

**need:** `assets/H5/pages/`; Beautiful Soup. Ссылки на другие страницы имеют класс `.page` и корректный `href`, товары — класс `.product` со ссылкой.

Начиная с `assets/H5/pages/page1.html`, обойдите доступные страницы без повторного чтения. Соберите товары, сделайте ссылки абсолютными, удалите дубли по URL и сохраните `products.json`.

Пример структуры результата:

```json
[
  {
    "name": "Keyboard duplicate",
    "url": "file:///path/to/assets/H5/products/keyboard.html"
  },
  {
    "name": "Mouse",
    "url": "file:///path/to/assets/H5/products/mouse.html"
  }
]
```
