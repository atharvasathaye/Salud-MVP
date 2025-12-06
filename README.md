# Salud-MVP (Billing Assistant Demo)

This repository contains a small working prototype of a patient-friendly billing and insurance assistant for a revenue cycle / billing company.

The chatbot is designed to sit inside a “Manage My Bills” portal page and help patients understand:

- What they (mock) owe
- Basic insurance concepts (deductible, copay, coinsurance, etc.)
- What to do next and where to go in the portal
- Without ever touching real PHI/PII or live account data

## Key features

- Simple FastAPI backend with a chat endpoint
- Jinja2 templates for the pre-login page and the mock “Manage My Bills” page
- LLM-powered assistant using the OpenAI API
- Lightweight retrieval over a local `billing_notes.txt` file for insurance definitions
- Mock bills table wired into the assistant prompt so it can answer questions like  
  “What is my total balance?” or “What is the status of ACC-1002?”

## Tech stack

- Python 3.11
- FastAPI + Uvicorn
- Jinja2 templates
- OpenAI API (chat + embeddings)
- `python-dotenv` for environment variables

## Project structure

```text
.
├── main.py                 # FastAPI app, chat endpoint, mock bills logic, RAG
├── templates/
│   ├── salud_site.html     # Pre-login landing page with chatbot
│   └── manage.html         # Mock Manage My Bills page, bills table, chatbot widget
├── knowledge/
│   └── billing_notes.txt   # Internal billing/insurance notes for retrieval
├── requirements.txt        # Python dependencies
└── .gitignore              # Ignores venv, cache, .env, etc.
