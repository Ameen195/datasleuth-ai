# DataSleuth AI — Autonomous Data Incident Investigation

DataSleuth AI is an AI-powered data quality investigation platform that compares dataset snapshots, detects data anomalies, gathers supporting evidence, and generates investigation summaries with recommended next steps.

The project combines deterministic data-quality checks with an AI agent to help data engineers investigate changes and potential data pipeline issues.

## Live Demo

- **Frontend:** https://datasleuth-ai.vercel.app/
- **Backend API:** https://datasleuth-ai-api.onrender.com/
- **API Documentation:** https://datasleuth-ai-api.onrender.com/docs

## Features

- **Dataset comparison:** Compare baseline and current CSV snapshots.
- **Data-quality detection:** Identify missing values, duplicate keys, invalid numeric values, and schema changes.
- **Evidence collection:** Gather supporting evidence for detected anomalies using investigation tools.
- **AI-assisted diagnosis:** Use an AI agent to analyze findings and suggest possible explanations.
- **Evidence-based reporting:** Separate confirmed findings from unverified hypotheses and recommended next steps.
- **Interactive dashboard:** View findings, severity distribution, dataset statistics, AI diagnosis, and evidence summaries.
- **JSON export:** Export investigation findings from the dashboard.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI orchestration | LangGraph, LangChain |
| Hosted inference | Groq API, ChatGroq |
| Local inference | Ollama, Qwen 3.5 4B |
| Data processing | Pandas |
| Testing | Pytest |
| Frontend hosting | Vercel |
| Backend hosting | Render |

## Architecture

```text
                  User
                   |
                   v
          React Dashboard
             (Vercel)
                   |
          Upload baseline CSV
          and current CSV
                   |
                   v
            FastAPI Backend
              (Render)
                   |
                   v
        Deterministic Data Checks
                   |
                   v
       LangGraph Investigation Agent
                   |
          +--------+--------+
          |                 |
          v                 v
      Groq API          Local Ollama
   Hosted inference     Qwen 3.5 4B
          |                 |
          +--------+--------+
                   |
                   v
       Diagnosis and Evidence Summary
                   |
                   v
           React Dashboard
```

The hosted backend uses Groq when `GROQ_API_KEY` is configured. Otherwise, the application falls back to the locally configured Ollama model. The local Ollama fallback requires Ollama and the configured model to be available in the environment running the backend.

## Example Investigation

The included sample datasets demonstrate how DataSleuth AI identifies issues such as:

- A removed `payment_method` column.
- Duplicate `transaction_id` keys.
- Missing values in `transaction_date`.
- Invalid numeric values in `amount`.
- An unexpected `payment_type` column.

The application reports evidence for these findings and provides possible explanations and recommended investigation steps. Suggested explanations are hypotheses and should be verified against source data and business rules.

## Run Locally

### Prerequisites

- Python 3.11 or a compatible Python version.
- Node.js and npm.
- Git.
- A Groq API key for hosted inference, or Ollama with the configured model for local inference.

### 1. Clone the repository

```bash
git clone https://github.com/Ameen195/datasleuth-ai.git
cd datasleuth-ai
```

### 2. Set up the Python environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3. Configure AI inference

For hosted inference, set your Groq API key in the environment before starting the backend:

```powershell
$env:GROQ_API_KEY = "YOUR_GROQ_API_KEY"
```

Optionally configure the model:

```powershell
$env:GROQ_MODEL = "openai/gpt-oss-20b"
```

Replace the placeholder with your own key. Never commit API keys to GitHub.

For local inference, install and start Ollama, ensure the model configured in `app/agent/investigation.py` is available, and run the backend without `GROQ_API_KEY`.

### 4. Start the backend

From the project root:

```powershell
python -m uvicorn backend.main:app --reload
```

The API should be available at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

### 5. Start the frontend

Open a second terminal:

```powershell
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory containing:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

Then start the development server:

```powershell
npm run dev
```

Open the local URL printed by Vite in your terminal.

## Run Tests

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The project had 16 passing tests in the development environment at the time of deployment.

## Deployment

The frontend is deployed on Vercel, and the FastAPI backend is deployed on Render.

Configure the frontend's `VITE_API_URL` environment variable to point to the deployed backend. Configure `GROQ_API_KEY` as a private environment variable in Render when using hosted inference.

The backend must also allow requests from the deployed frontend origin through its CORS configuration.

## Project Design Principles

- Deterministic checks provide the confirmed data-quality findings.
- AI-generated explanations are not treated as proven root causes.
- Investigation tools gather evidence to support the diagnosis.
- The agent is intended to investigate and report; it does not automatically modify the source datasets.

## Future Improvements

- Improve diagnosis formatting and response completeness.
- Add support for additional dataset formats and configurable validation rules.
- Expand automated integration tests for hosted inference.
- Add investigation history, richer filtering, and downloadable reports.
- Improve production monitoring, upload validation, and error handling.

## Author

**Mohammed Ameen Naimuddin**

GitHub: https://github.com/Ameen195

