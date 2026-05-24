# AI Primitives Architecture

## Backend Structure

The backend follows a layered architecture:
- `routes/` — HTTP handlers, thin controllers
- `services/` — Business logic, LLM calls, tool execution
- `core/` — Error classes, middleware
- `schemas.py` — Pydantic models for request/response validation

## Frontend Structure

The frontend uses Next.js App Router:
- `app/<module>/page.tsx` — Client components with state management
- `app/<module>/actions.ts` — Server actions wrapping backend API calls
- `components/ai/` — Reusable AI UI components (ApprovalCard, ErrorState, etc.)
- `components/ui/` — shadcn/ui primitives

## API Flow

Frontend server action → fetch() to FastAPI backend → Pydantic validation → service layer → OpenAI API → response → Zod validation on frontend.
