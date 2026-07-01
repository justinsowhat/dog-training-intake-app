# PawsitiveMind — Frontend (React + Vite + TypeScript)

A React single-page app wired to the FastAPI backend. The browser talks to
FastAPI directly (CORS is enabled on the backend).

Flow: Landing → hybrid intake form → chat intake → generating → training plan
(document / actionable) → post-plan follow-up chat.

## Stack

- React 19 + Vite 5, TypeScript
- A small custom hook (`lib/useConsultationChat.ts`) that consumes the backend's
  NDJSON chat stream with plain `fetch` — no AI SDK / framework lock-in.
- Plain CSS variables for the Sage theme (`src/globals.css`); fonts via a Google
  Fonts `<link>` in `index.html`.

## Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set VITE_API_BASE to your FastAPI URL
npm run dev                         # http://localhost:3000
```

`npm run build` runs `tsc --noEmit` then `vite build`; `npm run preview` serves
the production build.

## How it maps to the backend

| Screen | Backend call | Notes |
|---|---|---|
| Intake form → | `POST /consultation/start` | `lib/api.ts` → `startConsultation`. Sends a full `ComprehensiveIntakeSchema` built in `lib/intake.ts`. |
| Chat intake / follow-up | `POST /consultation/{id}/chat` | `useConsultationChat` reads the NDJSON event stream (see below). |
| Generate plan (manual) | `POST /consultation/{id}/finalize` | `lib/api.ts` → `finalizePlan`. Forces a plan; returns `ComprehensiveTrainingPlanSchema`. |

### The chat wiring (the important part)

`/chat` streams **`application/x-ndjson`** — one JSON event per line. The agent
decides, mid-conversation, when to propose (or revise) a plan via a tool call:

```
{"type":"token","text":"Based on "}      // incremental assistant text
{"type":"plan","plan":{...}}             // a full training plan (0 or 1 per turn)
{"type":"message","text":"I've drafted…"} // canned confirmation after a plan
{"type":"done"}                           // terminator  (or {"type":"error",...})
```

`useConsultationChat` appends `token`/`message` text to the assistant bubble and
hands `plan` events to an `onPlan` callback. The request body is
`{ "user_message": "..." }`; the backend rebuilds history from the DB, so we only
send the latest message.

Because the agent can propose a plan during chat:
- **ChatIntake** surfaces a proposed plan via `onPlanProposed` → the "Generate" CTA
  becomes "View plan" (no `/finalize` round-trip needed). `/finalize` remains as a
  manual "skip the questions" path.
- **PostChat** sends plan revisions via `onPlanRevised`, so asking "make week 1
  lighter" live-updates the displayed plan.

## Notes / future work

- **Intake completeness.** `/start` requires the *full* `ComprehensiveIntakeSchema`,
  but the UX only collects core info before the chat. `buildIntakePayload` seeds one
  `behavior_issue` from the form and leaves the rich fields blank-but-valid. To
  capture what the chat gathers, add a `PATCH /consultation/{id}/intake` later.
- **History hydration.** To resume an in-progress consultation, add
  `GET /consultation/{id}/messages` and pass the result as `initialMessages`.

## Project layout

```
frontend/
  index.html          Vite entry (Google Fonts, #root)
  vite.config.ts      @ -> ./src alias, dev server on :3000
  src/
    main.tsx          React root
    App.tsx           flow state machine
    globals.css       Sage theme
    components/        Landing, IntakeForm, ChatIntake, Generating, TrainingPlan, PostChat, ChatThread, ...
    lib/               types.ts (schema mirrors), api.ts, intake.ts, useConsultationChat.ts
```
