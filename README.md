# 🏆 FIFA World Cup 2026 — Smart Accessible Stadium Assistant & Ops Dashboard

A premium, FAANG-grade, context-aware GenAI assistant and operations telemetry system designed to optimize venue navigation during the FIFA World Cup 2026. This system is purpose-built to address critical **accessibility** and **multilingual** wayfinding requirements, ensuring all fans—including those with mobility, vision, hearing, sensory, or cognitive needs—can navigate the stadium seamlessly.

---

## 🌟 Chosen Vertical: Accessibility & Operations

The FIFA World Cup 2026 spans multiple host nations, drawing millions of fans speaking dozens of languages. A generic navigation tool fails to serve fans with accessible wayfinding requirements. 

This solution is designed around the **Fan Persona** (with options for **Staff** and **Volunteers**), using real-time venue telemetry and user-declared context to make dynamic routing decisions.

---

## ⚡ Mind-Blowing Features

### 1. FAANG-Grade Dark Glassmorphism Interface
- A premium, immersive interface designed with modern CSS glassmorphism.
- Powered by a dark theme utilizing vibrant **electric teal** (`#22d3ee`) accents and **deep purple/violet** ambient backdrop glows.
- Smooth CSS transitions and hardware-accelerated animations for a highly responsive, modern look and feel.

### 2. Live SVG Crowd Density Heatmap
- A dynamic, interactive stadium layout that updates in real time.
- Integrated **Heatmap View** that uses dynamic glowing overlay rings inside the SVG map.
- Automatically maps congestion levels (High/Medium/Low) from live telemetry to pulsing color-coded circles (electric cyan, amber, and rose halos) directly on gates, transit lines, and sections.

### 3. Real-Time Predictive Queue Widget
- Calculates and projects queue wait-times for critical stadium resources (accessible restrooms, concessions, and sensory rooms) using live telemetry.
- Renders dynamic color-coded progress bars (green/yellow/red) to alert users before they arrive.

### 4. Dynamic Accessibility Settings Panel
- **Dyslexia Font Mode**: Instantly shifts the interface typography to high-legibility styles with increased letter and word spacing.
- **Large Text Mode**: Globally scales UI text, input forms, and cards, optimizing legibility for low-vision users.
- **High Contrast Mode**: Strips backgrounds to accessibilty standards (solid black, pure white, and yellow borders) to satisfy WCAG AA+ visibility guidelines.

### 5. Dictation Waveform Visualizer
- A voice-enabled assistant that records user query dictation.
- Features a responsive, 5-bar voice equalizer animation next to the microphone icon to indicate active audio recording.

---

## 🛠️ Architecture & Pipeline

The system uses a robust, lightweight pipeline built on FastAPI (backend) and Vanilla JS + CSS (frontend). It functions entirely offline via a fallback system when no cloud LLM credentials are set.

```
+--------------------------------------------------------+
|                  Browser (HTML5/CSS3)                  |
|  (Glassmorphism UI, Accessibility Toggles, Live SVG)   |
+---------------------------+----------------------------+
                            | (HTTP JSON API)
                            v
+--------------------------------------------------------+
|                FastAPI Backend (app.py)                |
|  - Rate Limiter (per-IP)    - Input Pydantic Model     |
+---------------------------+----------------------------+
                            |
                            v
+--------------------------------------------------------+
|              Assistant Pipeline (assistant.py)         |
|  1. Guardrails (guardrails.py) - Sanitization          |
|  2. Context (context.py)       - Intent & Bias Parsing |
|  3. Retrieval (knowledge.py)   - Grounded Facts        |
|  4. System Builder             - System Prompts        |
+---------------------------+----------------------------+
                            |
                            v
+--------------------------------------------------------+
|              LLM Generation Engine (llm.py)            |
|       - Claude Online          - Local Scaffolder      |
+--------------------------------------------------------+
```

### Logical Pipeline Stages:
1. **Guardrails (`guardrails.py`)**: Strips control characters, enforces length limits, and detects prompt-injection attempts without blocking real queries.
2. **Context & Intent (`context.py`)**: Determines user context (role, language, accessibility needs, and location). Infers intent dynamically using a fast, deterministic keyword heuristic (Navigation, Accessibility, Services, Transport, Sustainability, or General). If a user with mobility needs asks for directions, the assistant automatically upgrades the request to an accessibility route to guarantee step-free guidance.
3. **Grounded Retrieval (`knowledge.py`)**: Filters static stadium facts and dynamic telemetry statuses, presenting only relevant information to the prompt to keep context windows small and prevent hallucination.
4. **Decision Router (`assistant.py`)**: Formulates system prompts dynamically, injecting accessibility guidelines corresponding to the fan's declared needs (e.g. step-free paths, tactile maps, hearing loops, simple language, quiet routes).
5. **Generation (`llm.py`)**: Interfaces with Anthropic's Claude API when available, otherwise gracefully degrades to an offline rule-based responder so the system continues operating under poor stadium connectivity conditions.
6. **Output Guardrail**: Sanitizes output text for safety checks and validates response fields.

---

## 📁 Repository Directory Structure

```text
worldcup-assist/
├── src/stadium_assistant/      # Backend Python application package
│   ├── __init__.py
│   ├── app.py                  # FastAPI Application Routes, Middleware & SSE Streams
│   ├── assistant.py            # Orchestrator (decision router, prompt construction)
│   ├── cache.py                # Bounded TTL Response Cache
│   ├── config.py               # Settings (environment reading, dynamic refresh)
│   ├── context.py              # UserContext, Enums & Intent Classifier Heuristics
│   ├── guardrails.py           # Sanitization (length constraints, injection check)
│   ├── i18n.py                 # Multi-language normalization helpers
│   ├── knowledge.py            # Venue Static Facts & Dynamic Telemetry Retrieval
│   └── llm.py                  # LLM engines (Anthropic cloud client vs Offline fallback)
├── web/                        # Frontend Single-Page App
│   ├── index.html              # HTML structure (screen-reader accessible, lang="en")
│   ├── style.css               # Vanilla CSS variables, glassmorphism, responsive styles
│   ├── app.js                  # Frontend UI, DOM updates, SSE listeners, mic animation
│   └── telemetry.js            # Pure side-effect-free telemetry & queue calculations
├── tests/                      # Full Test Suite
│   ├── conftest.py             # Shared fixtures and settings overrides
│   ├── eval_cases.yaml         # 20 golden behavioral evaluation cases
│   ├── test_api.py             # E2E API tests (auth, headers, rate limits, async SSE)
│   ├── test_assistant.py       # Prompt building correctness & RecordingEngine mock
│   ├── test_cache.py           # LRU/TTL cache tests
│   ├── test_config.py          # Dynamic environment setting tests
│   ├── test_context.py         # Intent classification & context bias validation
│   ├── test_evals.py           # Parameterized YAML eval runner (with --live flag)
│   ├── test_guardrails.py      # Control character stripping & injection check
│   ├── test_security.py        # Fail-closed authentication & leftmost proxy IP check
│   └── web/
│       └── telemetry.test.js   # Vitest unit tests for telemetry.js computations
├── pyproject.toml              # Python packaging and test configuration
├── requirements.txt            # Python runtime dependencies
├── package.json                # Frontend test and accessibility tooling
└── run.py                      # Application entry point
```

---

## 📡 API Reference

The server exposes a secure, high-performance API surface:

| Method | Endpoint | Format | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | JSON | Server liveness and Anthropic LLM connection health check |
| `GET` | `/languages` | JSON | Map of supported localized visitor languages |
| `GET` | `/api/stadium/status` | JSON | Fetches active congestion, elevator, and transit telemetry |
| `POST` | `/api/stadium/status` | JSON | Updates stadium telemetry (requires `X-Ops-Key` authentication) |
| `GET` | `/api/stadium/stream` | SSE | Stream of real-time telemetry updates (on change / 25s ping) |
| `POST` | `/api/assist` | JSON | Synchronous chat endpoint (returns reply, facts, and metadata) |
| `POST` | `/api/assist/stream` | SSE | Streaming GenAI assistant chat response (token-by-token) |

---

## 🚀 How to Run locally

### Prerequisites
- Python 3.10 or higher.
- Node.js 18 or higher (for Vitest & ESLint verification).
- (Optional) Anthropic API key.

### Setup and Start
1. Clone the repository to your environment.
2. Setup a virtual environment and install the dependencies:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   pip install -e .
   ```
3. Install Node.js devDependencies:
   ```bash
   npm install
   ```
4. (Optional) Create a `.env` file and add your `ANTHROPIC_API_KEY=your_key_here` to run the online Claude GenAI engine.
5. Run the development server:
   ```bash
   python run.py
   ```
6. Open your browser and navigate to: **`http://127.0.0.1:8000`**

---

## 🧪 Verification & Testing

The code includes a robust, offline-first verification suite covering Python (backend) and Javascript (frontend) code.

### 1. Backend Python Tests & Coverage (pytest)
To execute the backend checks and measure test coverage (minimum 80% required):
```bash
pytest
```
This runs **83 tests** (asserting settings reloading, fail-closed auth, rate-limit 429s, no tracebacks, prompt builder mocks, and context intent classifiers) and generates a code coverage report.

### 2. Frontend JavaScript Tests (Vitest)
To execute frontend pure-compute unit tests:
```bash
npm test
```
This runs **37 unit tests** checking telemetry levels, queue calculations, and the `const tr` string element isolation.

### 3. Golden Behavioral Evals (YAML)
Evaluation cases are located in `tests/eval_cases.yaml`. To run them in offline/CI mode:
```bash
pytest tests/test_evals.py
```
To run the `live_only` cases using the real Anthropic cloud client:
```bash
pytest tests/test_evals.py --live
```
*(Requires `ANTHROPIC_API_KEY` to be set in the environment).*

---

## 💡 Assumptions Made
- **Staging vs. Production Databases**: Static venue information in `knowledge.py` is configured as a list for showcase reasons. In production, this maps to GIS/facility spatial datasets.
- **Single-Worker Demo**: The stadium status is stored in an in-process thread-safe store. In a production environment with multiple uvicorn workers or server scaling, this would be backed by a shared database or Redis cache.
- **Privacy First**: Accessibility data, roles, and current seat locations are kept purely in the local memory context of the transaction. No personal data or query history is stored.
- **Connectivity Fallback**: Offline responders have pre-localized message logs for English, Spanish, and French. The cloud engine supports auto-translation for all languages.

---

## 📄 License

```text
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

