# AI Primitives Playground

## What this project demonstrates

- Streaming chat responses
- Structured JSON output
- Schema validation with Zod
- Tool calling and tool selection
- Approval before side effects
- Error and retry states
- Loading and partial response states

## Modules

### Brief Parser

Paste a product description or business idea. The model returns structured JSON with:

- `persona`: target user description
- `pain_points`: array of pain points
- `risks`: array of risks
- `next_questions`: array of follow-up questions

The output is streamed in real-time and validated against a Zod schema before being shown as successful.

### AI Form Assistant

Describe your project and let AI suggest values for a structured form. The flow is:

1. User describes the project
2. AI suggests form values
3. App shows suggested values in a preview
4. User approves or rejects
5. Only after approval values are applied to the form
6. User can save approved values to localStorage

### Tool Calling Playground

See how the model chooses a tool based on user input. Available tools:

- `summarize_text`: Summarize a piece of text
- `classify_priority`: Classify priority as low, medium, or high
- `draft_follow_up_questions`: Generate follow-up questions from context

The tool call is visible before execution. User must approve before the tool runs.

## What I learned

- Streaming changes UI significantly — users see progress immediately, but you need to handle partial/invalid data gracefully.
- Structured output needs validation because models can return malformed JSON or miss required fields.
- Tool calls should be visible to the user so they understand what the model is trying to do.
- Approval is important before side effects because model output is not trusted data.
- Common errors during development: invalid JSON from model, schema mismatches, missing environment variables, and stream interruption.

## How to run

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local and add your Timeweb Cloud AI API key

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the playground.

## Environment variables

| Variable | Description |
|----------|-------------|
| `AI_API_KEY` | Your Timeweb Cloud AI API key (server-side only) |
