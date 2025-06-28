# Natural Language Cross-Platform Data Query RAG Agent

## Overview

This project is an AI-powered system that allows business users to query multiple data sources using plain English. Built with **ReactJS** (frontend) and **Python FastAPI + LangChain** (backend), it connects to a PostgreSQL database and a MongoDB database to answer questions about client portfolios, relationship managers, client profiles, and more.

### Business Context

The solution is tailored for an asset management firm handling wealth portfolios of film stars and sports personalities with investments of 100+ crores. It supports queries such as:

- "What are the top five portfolios of our wealth members?"
- "Give me the breakup of portfolio values per relationship manager."
- "Which clients have a high risk appetite?"
- "Tell me the top relationship managers in my firm"
- "Which clients are the highest holders of RELIANCE stock?"

## Features

✅ Query PostgreSQL (financial data) and MongoDB (client profile data) in natural language.
✅ Returns results in text, tables, or charts, depending on query.
✅ FastAPI backend with LangChain ReAct Agent for reasoning and tool selection.
✅ ReactJS frontend using TailwindCSS, Recharts (for charts), and lucide-react icons.
✅ Example queries to try out immediately.

## Tech Stack

- **Backend:** Python 3, FastAPI, LangChain, SQLAlchemy, pymongo, PostgreSQL, MongoDB
- **Frontend:** ReactJS, TailwindCSS, Recharts, lucide-react

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL database running (or use Docker)
- MongoDB database running (or use Docker)

### Backend Setup

1. **Clone the repository:**

```bash
git clone https://github.com/rishugkp688/Ai_Agent_Test_Project.git
cd Ai_Agent_Test_Project
```

2. **Create Python virtual environment and activate:**

```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
# OR manually:
pip install "fastapi[all]" "uvicorn[standard]" langchain langchain-community "sqlalchemy" "psycopg2-binary" "pymongo" python-dotenv langchainhub langchain-ollama
```

4. **Create a **\`\`** file in the backend directory with:**

```
POSTGRES_USER=your_pg_user
POSTGRES_PASSWORD=your_pg_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_pg_db

MONGO_URI=mongodb://localhost:27017
```

5. **Run the backend server:**

```bash
uvicorn main:app --reload
```

The backend should start on `http://localhost:8000`.

### Frontend Setup

1. **Install dependencies:**

```bash
cd frontend
npm install
```

2. **Run the frontend:**

```bash
npm run dev
```

This should start the React app on `http://localhost:5173` (or similar port).

## Using the Application

- Navigate to the frontend URL in your browser.
- Try one of the example queries or type your own natural language question.
- The system will respond with a text answer, table, or chart depending on the query.

## Deployment Notes

- **API URL:** In production, update `API_URL` in the frontend to point to your deployed backend.
- **Security:** Restrict CORS origins in `main.py` before deployment.
- **Persistence:** Current setup uses mock data created at backend startup. Connect to your real data sources for production.

## License

MIT License

## Credits

Built with ❤️ using LangChain, FastAPI, ReactJS, and Recharts.
