\# Revenue Chatbot (SRP Billing Assistant MVP)



This repository contains a working prototype of a \*\*patient-friendly billing and insurance assistant\*\* for a revenue cycle / billing company.



The chatbot is designed to sit inside a \*\*“Manage My Bills”\*\* portal page and help patients understand:



\- What they (mock) owe

\- Basic insurance concepts (deductible, copay, coinsurance, etc.)

\- What to do next and where to go in the portal  

\- Without ever touching real PHI/PII or live account data



---



\## 🔍 Key Features



\- \*\*Embedded web chatbot\*\* (FastAPI + HTML) that can be dropped into a portal page

\- \*\*Mock bill support\*\* for a demo patient (“Alex Rivera”) with:

&nbsp; - Multiple visits

&nbsp; - Per-bill amounts

&nbsp; - Total “mock” balance

\- \*\*Login-aware behavior\*\*

&nbsp; - Pre-login: general education only

&nbsp; - Post-login: can answer “What is my total?” from mock bills

\- \*\*Safety \& PHI guardrails\*\*

&nbsp; - Regex-based detection of account #, SSN, DOB, policy/member ID

&nbsp; - Blocks unsafe queries \*before\* calling the OpenAI API

&nbsp; - Does not log raw PHI/PII (chat log is lightly redacted)

\- \*\*Intent router (mini “brain” in front of the model)\*\*

&nbsp; - Classifies user messages as:

&nbsp;   - `payment\_help`

&nbsp;   - `portal\_navigation`

&nbsp;   - `cost\_estimate`

&nbsp;   - `sensitive\_info`

&nbsp;   - `other`

&nbsp; - Navigation / payment questions get short, portal-style instructions

&nbsp; - Concept questions go to the main assistant

\- \*\*Knowledge-grounded answers (RAG over notes file)\*\*

&nbsp; - Uses a local knowledge file (`knowledge/billing\_notes.txt`)

&nbsp; - Embeds and retrieves the most relevant chunks per question

&nbsp; - Keeps explanations of insurance terms consistent and factual

\- \*\*Bilingual support (English / Spanish)\*\*

&nbsp; - Language dropdown on the frontend (Auto / English / Español)

&nbsp; - Backend forces English unless Spanish is explicitly chosen

\- \*\*Chat logging\*\*

&nbsp; - Logs are appended to Azure Blob Storage as redacted JSONL

&nbsp; - Easy to analyze intents and usage over time



---



\## 🧱 Tech Stack



\- \*\*Backend:\*\* FastAPI (Python)

\- \*\*Frontend:\*\* Jinja2 HTML template (`templates/manage.html`) + simple JS/CSS chat widget

\- \*\*AI Model:\*\* OpenAI `gpt-4o-mini` (configurable via env variable)

\- \*\*Embeddings:\*\* `text-embedding-3-small`

\- \*\*Storage:\*\*

&nbsp; - Azure Blob Storage (for mock bills + chat logs) – optional

&nbsp; - Local text file for knowledge base (`knowledge/billing\_notes.txt`)



---



\## 📂 Folder Structure



```text

revenue-chatbot/

├── main.py                    # FastAPI app + chatbot logic

├── requirements.txt           # Python dependencies

├── .gitignore

├── knowledge/

│   ├── billing\_notes.txt      # Cleaned billing/insurance guide (used for RAG)

│   └── How Billing and Insurance Work NOTES...txt  # Source notes (optional)

└── templates/

&nbsp;   ├── manage.html            # Main portal + chatbot UI

&nbsp;   ├── salud\_site.html        # Additional HTML mockup

&nbsp;   └── requirements.txt       # (template artifact, not Python deps)



