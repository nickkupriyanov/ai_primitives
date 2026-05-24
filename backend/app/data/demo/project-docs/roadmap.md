# AI Primitives Playground — Roadmap

## Completed Modules

1. **Brief Parser** — Structured text analysis: input text → /analyze endpoint → topics, pain_points, risks, next_questions.
2. **AI Form Assistant** — Project form auto-fill: describe project → /form-assistant → suggested form values with user approval.
3. **Tool Calling Playground** — LLM decides which tool to call → user approves side-effect tools → tool executed.

## Architecture

- Backend: FastAPI on port 8000, Pydantic v2 schemas, service-layer pattern
- Frontend: Next.js 16, React 19, Tailwind v4, shadcn/ui
- AI: OpenAI-compatible API for LLM calls
- Testing: pytest for backend, Vitest for frontend

## Key Design Decisions

- AI logic stays in backend service layer, never in frontend routes
- Tool execution with safety approval: side-effect tools require `approved: true`
- All responses validated with Pydantic schemas
- Request logging middleware on every endpoint
