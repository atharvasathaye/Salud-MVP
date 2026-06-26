# Billing Assistant MVP

A patient-facing billing and insurance chatbot prototype built with FastAPI and OpenAI. Designed to help patients understand medical bills, insurance terminology, and portal navigation.

## Background

Patients often struggle to understand medical billing. This prototype demonstrates an LLM-powered assistant that can answer questions about bills, explain insurance concepts (deductible, copay, coinsurance), and guide users through a mock billing portal. All data shown is synthetic. No real patient data is used.

## How It Works

1. The FastAPI backend serves a mock billing portal with sample patient accounts
2. When a patient asks a question, the system routes it through an intent classifier
3. A RAG pipeline retrieves relevant billing/insurance definitions from a local knowledge base
4. The LLM generates a response at a 4th-6th grade reading level using only the mock data
5. PHI protection detects and blocks messages containing account numbers, SSNs, or personal identifiers

## Setup

```bash
git clone https://github.com/atharvasathaye/Salud-MVP.git
cd Salud-MVP
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt

# Add your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# Run
uvicorn main:app --reload --port 8000
```

Requires Python 3.11+ and an OpenAI API key.

## Tech Stack

Python 3.11, FastAPI, OpenAI API (GPT-4o-mini, text-embedding-3-small), Jinja2, Pydantic

## Collaborators

Built as a team project: Nishit Mistry (PM), Atharva Sathaye, Akshay Wagh, Jasmitha Duvvuru, Juhi Khare.

## License

MIT
