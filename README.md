# NexaSupport — AI Customer Service Agent

A full-stack AI Customer Service Agent built with **LangGraph**, **LangChain**, **FastAPI**, and a sleek HTML/CSS frontend.

---

## 🗂️ Project Structure

```
customer-service-agent/
├── backend/
│   ├── main.py            # FastAPI server with LangGraph agent
│   └── requirements.txt   # Python dependencies
├── frontend/
│   └── index.html         # Standalone frontend (no build needed)
└── README.md
```

---

## ⚙️ How It Works

The agent processes queries through a **LangGraph state machine**:

1. **Categorize** → Technical / Billing / General
2. **Analyze Sentiment** → Positive / Neutral / Negative
3. **Route**:
   - Math expression → `handle_calculation` (calculator tool)
   - Email request → `handle_email` (email tool)
   - Negative sentiment → `escalate` (human handoff)
   - Technical → `handle_technical`
   - Billing → `handle_billing`
   - General → `handle_general`

---

## 🚀 Steps to Run

### Prerequisites
- Python 3.9+
- An [OpenRouter](https://openrouter.ai) API key (free tier works)

---

### Step 1 — Set up the Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

The backend will be running at: **http://localhost:8000**

You can verify it's working by visiting: http://localhost:8000/health

---

### Step 2 — Open the Frontend

No build step needed! Just open the frontend file directly in your browser:

```bash
# From the project root
open frontend/index.html         # macOS
start frontend/index.html        # Windows
xdg-open frontend/index.html     # Linux
```

Or simply double-click `frontend/index.html` in your file explorer.

---

### Step 3 — Configure & Use

1. Enter your **OpenRouter API key** in the sidebar (starts with `sk-or-v1-...`)
2. Type a query or click a quick example
3. See the AI response with category and sentiment badges

---

## 📝 Example Queries

| Query | Route |
|-------|-------|
| "My internet is not working" | Technical or Escalate |
| "Where can I find my bill?" | Billing |
| "What are your business hours?" | General |
| "Calculate 125 * 8 + 200" | Calculator Tool |
| "Write email for refund request" | Email Tool |
| "I am very angry, my order is wrong!" | Escalate |

---

## 🔑 Getting an OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up for a free account
3. Navigate to **Keys** → **Create Key**
4. Copy the key and paste it into the frontend sidebar

---

## 🛠️ Customization

- **Change the LLM**: Edit `model=` in `backend/main.py` (any OpenRouter model works)
- **Add routing rules**: Edit `route_query()` in `backend/main.py`
- **Change the API base URL**: Swap `https://openrouter.ai/api/v1` for any OpenAI-compatible endpoint
