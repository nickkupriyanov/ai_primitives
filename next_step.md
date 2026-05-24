RAG и работа с документами
Цель: научиться строить AI-фичи поверх пользовательских данных.

Собери проект Document QA:

загрузка .md, .txt, .pdf или вставка текста;
ingestion;
вопрос по документам;
ответ с citations/evidence;
список failure cases, где retrieval ошибся.
Начни с простого пути:

текстовые документы;
локальное хранение или SQLite/Postgres;
embeddings + vector search;
citations на уровне source/chunk;
ручной список retrieval failures.
Hosted file search можно использовать как быстрый путь, но для роста тебе полезно хотя бы один раз собрать контролируемую версию на своем backend.

Практические задачи:

"Спроси по конспектам";
"Спроси по документации проекта";
"Сравни 3 документа и найди противоречия";
"Собери FAQ из набора заметок".
Минимальные сущности:

Source
  id
  filename
  content_type
  created_at

Chunk
  id
  source_id
  text
  position
  embedding_id

QuestionRun
  id
  question
  answer
  cited_chunk_ids
  latency_ms
Критерии готовности:

можно добавить минимум 5 документов;
вопрос возвращает ответ и evidence;
карточка ответа показывает источники;
есть 10-15 тестовых вопросов;
есть таблица "где retrieval ошибается и почему".
