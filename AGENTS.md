# AGENTS.md

## Project Overview

This project is a small AI playground for learning core AI application primitives as a frontend/product engineer.

The goal is not to build a production SaaS, but to understand and implement the building blocks that appear in real AI products:

- streaming chat;
- structured JSON output;
- schema validation;
- tool calling;
- human approval before side effects;
- loading, partial response, error and retry states;
- simple but real frontend UX.

The project should stay focused, small and easy to understand.

---

## Main Goal

Build an AI primitives playground with three practical modules:

1. Brief Parser
2. AI Form Assistant
3. Tool Calling Playground

Each module should demonstrate a specific AI interaction pattern.

The app should prioritize clarity, correctness and learning value over visual complexity.

---

## Preferred Stack

Use the following stack unless the user explicitly changes it:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui if useful, but avoid overengineering
- Zod for schema validation
- Server Actions or API Routes for backend AI calls
- OpenAI SDK or another LLM SDK if already configured

Keep dependencies minimal.

Do not add heavy state-management libraries unless there is a clear reason.

---

## Product Scope

### In Scope

The app should include:

- a simple navigation between playground modules;
- streaming AI response UI;
- structured output generation and validation;
- tool calling simulation or real tool execution;
- visible tool call preview before execution;
- approval flow before any side effect;
- loading states;
- partial response states;
- error states;
- retry action;
- README with learning notes.

### Out of Scope

Do not build:

- authentication;
- payments;
- database-heavy architecture;
- complex admin dashboard;
- multi-user system;
- production analytics;
- complicated design system;
- advanced agent orchestration;
- vector database;
- RAG pipeline;
- background jobs;
- deployment automation unless requested.

This is a learning playground, not a SaaS MVP.

---

## UX Principles

The UI should make AI behavior visible and understandable.

Prioritize:

- clear states;
- transparent model actions;
- user control;
- readable JSON output;
- obvious validation errors;
- simple recovery from failure.

Avoid hiding important AI behavior behind magic.

The user should always understand:

- what was sent to the model;
- what the model returned;
- whether the response is valid;
- what tool the model wants to call;
- what will happen before any side effect is executed.

---

## App Structure

Suggested structure:

```txt
src/
  app/
    page.tsx
    brief-parser/
      page.tsx
    form-assistant/
      page.tsx
    tool-playground/
      page.tsx
    api/
      brief-parser/
        route.ts
      form-assistant/
        route.ts
      tool-playground/
        route.ts

  components/
    ai/
      StreamingMessage.tsx
      JsonPreview.tsx
      ToolCallPreview.tsx
      ApprovalCard.tsx
      RetryButton.tsx
      ErrorState.tsx

    ui/
      ...

  lib/
    ai/
      client.ts
      prompts.ts
      schemas.ts
      tools.ts
      stream.ts

    validators/
      briefSchema.ts
      formSchema.ts
      toolSchema.ts

  types/
    ai.ts
````

This structure can be adjusted if the existing project already has a different convention.

Do not reorganize the whole app unless necessary.

---

## Module 1: Brief Parser

### Goal

The user pastes a product description or business idea.
The model returns a structured JSON object.

### Required Output Schema

The response must include:

```ts
{
  persona: string;
  pain_points: string[];
  risks: string[];
  next_questions: string[];
}
```

Use Zod or another schema validation tool.

### UX Requirements

The Brief Parser page should include:

* textarea for the product brief;
* submit button;
* loading state;
* streamed or progressive response state if possible;
* final structured JSON preview;
* validation success or validation error;
* retry button;
* human-readable summary of the parsed result.

### Important Behavior

The model must not return free-form text as the final result.

The final result should be validated before being shown as successful.

If validation fails, show:

* what failed;
* the raw model output if useful;
* retry action.

---

## Module 2: AI Form Assistant

### Goal

The model helps the user fill a complex form, but does not save anything without confirmation.

### Example Form Fields

Use a simple but realistic product/project form:

```ts
{
  project_name: string;
  target_user: string;
  problem: string;
  proposed_solution: string;
  main_risks: string[];
  success_metric: string;
}
```

### UX Requirements

The page should include:

* empty form;
* user prompt/input field;
* button: “Help me fill this form”;
* AI-generated suggested values;
* diff or preview between current values and suggested values;
* approve button;
* reject button;
* edit manually option;
* save button after approval.

### Approval Rule

The model must never directly save form values.

The flow must be:

1. User asks AI to fill or improve the form.
2. AI suggests values.
3. App shows suggested values.
4. User approves or edits.
5. Only after approval the values can be applied or saved.

### Side Effect Definition

For this project, a side effect means:

* applying AI-generated values to the final form;
* saving data to localStorage;
* sending data to an API;
* overwriting existing user input.

Any side effect requires approval.

---

## Module 3: Tool Calling Playground

### Goal

Demonstrate how the model chooses a tool and how the UI exposes that tool call before execution.

### Required Tools

Implement these tools:

```ts
summarize_text(input: {
  text: string;
}): {
  summary: string;
}
```

```ts
classify_priority(input: {
  text: string;
}): {
  priority: "low" | "medium" | "high";
  reason: string;
}
```

```ts
draft_follow_up_questions(input: {
  context: string;
}): {
  questions: string[];
}
```

### UX Requirements

The page should include:

* user input textarea;
* model response area;
* visible selected tool name;
* visible tool arguments;
* approval card before execution;
* execute button;
* cancel button;
* final tool result;
* error and retry states.

### Tool Approval Rule

The tool call must be visible before execution.

The user should see:

* tool name;
* arguments;
* what the tool will do;
* whether it has side effects.

Even though these tools are harmless, the approval pattern should be implemented as if the project could later support real side-effect tools.

---

## AI Interaction Rules

### Streaming

Where streaming is used:

* show partial response while it is being generated;
* do not block the whole UI unnecessarily;
* show a clear loading indicator;
* handle stream interruption gracefully;
* allow retry after failure.

### Structured Output

All structured outputs must be validated.

Do not trust model output blindly.

Use schemas for:

* Brief Parser response;
* AI Form Assistant suggestions;
* Tool Calling arguments;
* Tool results if applicable.

### Errors

The app should handle:

* network errors;
* invalid model output;
* schema validation errors;
* tool execution errors;
* empty user input;
* timeout or interrupted stream.

Errors should be visible and understandable.

Avoid generic errors like:

```txt
Something went wrong
```

Prefer useful messages:

```txt
The model returned invalid JSON. Please retry or simplify your input.
```

---

## Prompting Rules

Keep prompts explicit and small.

Prompts should explain:

* the user task;
* the expected output format;
* the schema;
* what not to do;
* whether the model may call tools;
* whether approval is required.

Avoid huge universal prompts.

Each module should have its own prompt.

Store prompts in a dedicated file, for example:

```txt
src/lib/ai/prompts.ts
```

---

## State Management

Use simple React state first.

Recommended states:

```ts
type RequestStatus =
  | "idle"
  | "loading"
  | "streaming"
  | "success"
  | "error";
```

For tool calls:

```ts
type ToolCallStatus =
  | "idle"
  | "pending_approval"
  | "approved"
  | "executing"
  | "success"
  | "cancelled"
  | "error";
```

Avoid global state unless it clearly improves the project.

---

## Code Quality Rules

Use TypeScript strictly.

Prefer:

* small components;
* explicit types;
* Zod schemas;
* readable function names;
* clear error handling;
* simple file structure.

Avoid:

* clever abstractions;
* premature architecture;
* large generic AI frameworks;
* hidden side effects;
* silent failures;
* untyped `any`;
* mixing UI logic, prompt logic and tool logic in one huge file.

---

## Security and Safety Rules

Never expose API keys in the client.

AI calls must happen server-side.

Environment variables should be accessed only on the server.

Do not log sensitive user input unnecessarily.

Do not execute arbitrary code from model output.

Do not treat model output as trusted data.

All side effects must go through explicit app logic and user approval.

---

## Local Storage Rules

If localStorage is used, keep it simple.

Allowed use cases:

* saving approved form values;
* saving last successful playground input;
* saving small demo history.

Do not build a full persistence layer unless requested.

When writing to localStorage, treat it as a side effect and require approval if the values came from AI.

---

## README Requirements

The project must include a `README.md` with:

```md
# AI Primitives Playground

## What this project demonstrates

- Streaming chat
- Structured output
- Schema validation
- Tool calling
- Approval before side effects
- Error and retry states

## Modules

### Brief Parser

Explain what it does and what schema it uses.

### AI Form Assistant

Explain the approval flow.

### Tool Calling Playground

Explain the available tools and how approval works.

## What I learned

Write short notes about:

- what streaming changes in UI;
- why structured output needs validation;
- why tool calls should be visible;
- why approval is important before side effects;
- what errors appeared during development.

## How to run

Add project-specific commands here.

## Environment variables

Document required environment variables without exposing real values.
```

The README should be short but useful.

---

## Definition of Done

The project is considered done when:

* Brief Parser returns structured JSON;
* structured JSON is validated by schema;
* AI Form Assistant suggests form values;
* user approval is required before applying AI-generated values;
* Tool Calling Playground shows selected tool before execution;
* user can approve or cancel tool execution;
* streaming or partial response is visible in UI;
* loading states are implemented;
* error states are implemented;
* retry is available after errors;
* README explains what was learned;
* API keys are not exposed to the client;
* the project can be run locally.

---

## Development Order

Recommended implementation order:

1. Create base app layout and navigation.
2. Add shared UI components for loading, error and retry.
3. Implement Brief Parser without streaming first.
4. Add schema validation.
5. Add streaming or progressive response display.
6. Implement AI Form Assistant.
7. Add approval before applying AI suggestions.
8. Implement Tool Calling Playground.
9. Add tool call preview and approval.
10. Improve error handling.
11. Write README learning notes.
12. Refactor only after the flows work.

Do not start with abstractions.

First make the flows work clearly.

---

## Agent Behavior Instructions

When modifying this project, the coding agent should:

* preserve the learning-focused scope;
* avoid adding unnecessary production features;
* explain major architectural choices in comments or README if helpful;
* keep AI logic separated from UI components;
* keep schemas close to the AI outputs they validate;
* avoid large rewrites unless clearly needed;
* prefer simple, readable implementation;
* make every AI side effect explicit and user-approved.

Before adding a new dependency, check whether the feature can be implemented with existing tools.

Before changing the folder structure, check whether the current structure already supports the task.

Before introducing a new abstraction, implement the feature directly first.

---

## Non-Goals

This project is not meant to become:

* a full chatbot product;
* a CRM;
* a production agent platform;
* a complex LangChain/LangGraph demo;
* a database-heavy SaaS;
* an authentication demo;
* a design portfolio landing page.

The main value of the project is understanding AI primitives through working UI examples.

---

## Future Improvements

Only after the core project is finished, consider:

* adding conversation history;
* adding persistent playground sessions;
* adding more tools;
* adding real side-effect tools;
* adding evals for structured output quality;
* adding tests for schemas and tools;
* adding deployment;
* adding a small visual trace of AI steps;
* adding model/provider switcher.

Do not implement these in the first version unless explicitly requested.
