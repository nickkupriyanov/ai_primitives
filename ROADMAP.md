## Шаг 1. Инициализация проекта

Создать структуру:

```txt
app/
tests/
.env.example
README.md
requirements.txt
````

Настроить FastAPI app в `app/main.py`.

---

## Шаг 2. Добавить config

Создать `app/config.py`.

Настройки:

- app name;
- app version;
- env;
- OpenAI API key;
- model;
- retries;
- timeout;
- CORS origins;
- log level.

---

## Шаг 3. Добавить schemas

Создать Pydantic-модели для:

- analyze;
- chat;
- tools;
- health;
- errors;
- meta.

---

## Шаг 4. Добавить health endpoint

Сначала сделать самый простой endpoint:

```txt
GET /health
```

Проверить запуск backend.

---

## Шаг 5. Добавить logging middleware

Сделать middleware, который логирует:

- method;
- path;
- status;
- latency_ms;
- request_id.

---

## Шаг 6. Добавить error handling

Сделать единый формат ошибок.

Покрыть:

- validation errors;
- custom app errors;
- unexpected errors.

---

## Шаг 7. Реализовать LLMService

Добавить методы:

```python
analyze_text(...)
chat(...)
```

Внутри сервиса:

- собрать messages;
- вызвать LLM;
- обработать retries;
- вернуть нормальный response.

---

## Шаг 8. Реализовать `/analyze`

Route вызывает только service-layer.

---

## Шаг 9. Реализовать `/chat`

Route вызывает только service-layer.

---

## Шаг 10. Реализовать ToolService

Создать whitelist tools.

Минимально:

```txt
summarize_text
classify_priority
extract_action_items
save_note
```

---

## Шаг 11. Реализовать `/tools/execute`

Проверить:

- allowed tools;
- approval;
- validation;
- response format.

---

## Шаг 12. Добавить README и OpenAPI descriptions

Убедиться, что `/docs` выглядит понятно.

---

# 21. Пример финального результата API

## Analyze

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Я хочу вынести AI-логику из React-компонентов в отдельный backend на FastAPI...",
    "language": "ru"
  }'
```

---

## Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Объясни зачем нужен service-layer"
  }'
```

---

## Tool execute

```bash
curl -X POST http://localhost:8000/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "classify_priority",
    "arguments": {
      "text": "Срочно исправить ошибку оплаты"
    },
    "approved": false
  }'
```

---

# 22. Итоговая формулировка задачи для Codex

```md
Реализуй FastAPI backend для AI workflow.

Нужно создать сервис со следующими endpoints:

- GET /health
- POST /analyze
- POST /chat
- POST /tools/execute

Структура проекта:

app/
main.py
config.py
schemas.py
routes/
analyze.py
chat.py
tools.py
health.py
services/
llm_service.py
tool_service.py
observability/
logging.py
core/
errors.py
middleware.py

Требования:

1. Использовать FastAPI и Pydantic v2.
2. Все request/response модели описать через Pydantic.
3. Route handlers должны быть тонкими.
4. LLM-вызовы должны быть только внутри LLMService.
5. Tool execution должен быть только внутри ToolService.
6. Добавить whitelist разрешенных tools.
7. Side-effect tools должны требовать approved=true.
8. Добавить единый формат ошибок:
   {
   "error": {
   "code": "...",
   "message": "...",
   "details": {}
   }
   }
9. Добавить logging middleware для latency, status code, path, method.
10. Добавить retries/backoff для LLM-вызовов.
11. Добавить .env.example.
12. Добавить README с запуском.
13. OpenAPI docs должны быть понятными.
14. Не хранить AI-логику в route handlers.
15. Не логировать пользовательский текст целиком и не логировать секреты.

Endpoints:

POST /analyze:

- request: text, language
- response: topics, pain_points, risks, next_questions, meta

POST /chat:

- request: message, conversation_id, history
- response: assistant message, conversation_id, meta

POST /tools/execute:

- request: tool_name, arguments, approved
- response: tool_name, status, result, meta

GET /health:

- response: status, service, version

Добавь базовые тесты для health, analyze validation, chat validation и tools approval logic.
```
