# --- Dependencies ---
# pip install "fastapi[all]" "uvicorn[standard]" langchain langchain-community "sqlalchemy" "psycopg2-binary" "pymongo" python-dotenv langchainhub langchain-ollama

import os
import json
import re
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain Imports
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.agents import tool, AgentExecutor
from langchain.agents.react.agent import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain import hub

# --- Environment Setup ---
load_dotenv()

# --- Database Connections ---

# 1. PostgreSQL Connection
def get_postgres_db():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")
    if not all([user, password, host, port, database]):
        raise ValueError("One or more PostgreSQL environment variables are not set.")
    db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    
    return SQLDatabase.from_uri(
        db_uri,
        include_tables=['relationship_managers', 'clients_postgres', 'holdings'],
        sample_rows_in_table_info=3
    )

# 2. MongoDB Connection
from pymongo import MongoClient

def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable is not set.")
    return MongoClient(mongo_uri)

# --- Mock Data Setup ---
def setup_mock_data():
    # PostgreSQL Setup
    try:
        postgres_db = get_postgres_db()
        # Drop tables in reverse order of creation due to foreign key constraints
        postgres_db.run("DROP TABLE IF EXISTS holdings CASCADE;")
        postgres_db.run("DROP TABLE IF EXISTS clients_postgres CASCADE;")
        postgres_db.run("DROP TABLE IF EXISTS relationship_managers CASCADE;")

        postgres_db.run("""
        CREATE TABLE relationship_managers (
            rmId VARCHAR PRIMARY KEY,
            rmName VARCHAR NOT NULL,
            region VARCHAR
        );
        """)
        postgres_db.run("""
        CREATE TABLE clients_postgres (
            clientId VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            rmId VARCHAR,
            FOREIGN KEY (rmId) REFERENCES relationship_managers(rmId)
        );
        """)
        postgres_db.run("""
        CREATE TABLE holdings (
            holdingId SERIAL PRIMARY KEY,
            clientId VARCHAR,
            stockSymbol VARCHAR,
            quantity INT,
            currentValue DECIMAL,
            FOREIGN KEY (clientId) REFERENCES clients_postgres(clientId)
        );
        """)

        postgres_db.run("INSERT INTO relationship_managers (rmId, rmName, region) VALUES ('RM01', 'Anjali Sharma', 'Mumbai'), ('RM02', 'Vikram Singh', 'Delhi');")
        postgres_db.run("INSERT INTO clients_postgres (clientId, name, rmId) VALUES ('C101', 'Shah Rukh Khan', 'RM01'), ('C102', 'Virat Kohli', 'RM02'), ('C103', 'Priyanka Chopra', 'RM01');")
        postgres_db.run("""
        INSERT INTO holdings (clientId, stockSymbol, quantity, currentValue) VALUES
        ('C101', 'RELIANCE', 1000, 2850000.00), ('C101', 'TCS', 500, 1900000.00),
        ('C102', 'HDFCBANK', 2000, 3100000.00), ('C102', 'INFY', 800, 1200000.00),
        ('C103', 'RELIANCE', 1500, 4275000.00), ('C103', 'WIPRO', 3000, 1410000.00);
        """)
        print("PostgreSQL mock data setup complete.")
    except Exception as e:
        print(f"Error setting up PostgreSQL mock data: {e}")

    # MongoDB Setup
    try:
        mongo_client = get_mongo_client()
        db = mongo_client["wealth_management_profiles"]
        collection = db["client_profiles"]
        collection.delete_many({})
        collection.insert_many([
            {"clientId": "C101", "name": "Shah Rukh Khan", "address": "Mannat, Bandra, Mumbai", "riskAppetite": "High", "investmentPreferences": ["Entertainment", "Tech"]},
            {"clientId": "C102", "name": "Virat Kohli", "address": "Gurugram, Haryana", "riskAppetite": "Medium", "investmentPreferences": ["Apparel", "Fintech", "Health"]},
            {"clientId": "C103", "name": "Priyanka Chopra", "address": "Los Angeles, California", "riskAppetite": "High", "investmentPreferences": ["Startups", "Real Estate"]},
        ])
        print("MongoDB mock data setup complete.")
    except Exception as e:
        print(f"Error setting up MongoDB mock data: {e}")


# --- LangChain Tools ---
llm = ChatOllama(model="llama3", temperature=0)
postgres_db = get_postgres_db()
mongo_client = get_mongo_client()
mongo_db = mongo_client["wealth_management_profiles"]
profiles_collection = mongo_db["client_profiles"]

@tool
def query_financial_data(sql_query: str) -> str:
    """
    Use this tool ONLY for questions about financial data, such as stock holdings, portfolio values, transactions, and relationship managers.
    The input MUST be a valid SQL query for a PostgreSQL database.
    You have access to the following tables: 'relationship_managers', 'clients_postgres', 'holdings'.
    Example: To find the highest holders of RELIANCE stock, your Action Input would be:
    "SELECT T2.name, T1.quantity, T1.currentValue FROM holdings AS T1 JOIN clients_postgres AS T2 ON T1.clientId = T2.clientId WHERE T1.stockSymbol = 'RELIANCE' ORDER BY T1.currentValue DESC"
    """
    try:
        return postgres_db.run(sql_query) # type: ignore
    except Exception as e:
        return f"An error occurred while executing the SQL query: {e}"

@tool
def get_client_profile_by_name(client_name: str) -> str:
    """
    Use this tool to get NON-FINANCIAL profile information for a SINGLE, specific client by their full name.
    This includes their address, risk appetite, and investment preferences.
    The input MUST be the client's full name as a string.
    Example Action Input: "Virat Kohli"
    """
    if not client_name:
        return json.dumps({"error": "A client_name string must be provided."})
    # Use a case-insensitive regex to match the name
    profile = profiles_collection.find_one({"name": {"$regex": f"^{client_name}$", "$options": "i"}})
    if profile and '_id' in profile:
        del profile['_id']
        return json.dumps(profile)
    return json.dumps({"error": f"Client profile for '{client_name}' not found."})

@tool
def find_clients_by_risk_appetite(risk_level: str) -> str:
    """
    Use this tool to find a list of clients who match a specific risk appetite.
    The input MUST be one of 'High', 'Medium', or 'Low'.
    Example Action Input: "High"
    """
    if risk_level.title() not in ['High', 'Medium', 'Low']:
        return json.dumps({"error": "risk_level must be one of 'High', 'Medium', or 'Low'."})
    clients = list(profiles_collection.find({"riskAppetite": risk_level.title()}, {"_id": 0, "name": 1, "clientId": 1}))
    return json.dumps(clients)

# --- Master ReAct Agent Setup ---
tools = [query_financial_data, get_client_profile_by_name, find_clients_by_risk_appetite]

# FIX: Escaped all literal curly braces in the template string to prevent formatting errors.
# The original error was caused by LangChain misinterpreting the JSON examples as f-string variables.
# By changing { to {{ and } to }}, we tell the template engine to treat them as literal characters.
prompt_template_str = """
You are an assistant that answers questions by using tools. You have access to the following tools:

{tools}

Your task is to answer the user's question based ONLY on the information returned by the tools.
DO NOT invent any information or use your own knowledge.

**Tool Selection Process:**
1.  Analyze the user's question to determine the type of information needed (financial vs. non-financial profile).
2.  If FINANCIAL data is needed (stocks, values, RMs), you MUST use the `query_financial_data` tool. You will need to generate a valid SQL query for this.
3.  If NON-FINANCIAL profile data is needed (risk appetite, address), you MUST use `get_client_profile_by_name` or `find_clients_by_risk_appetite`.
4.  Choose the tool that most directly answers the question. Check the tool's description to understand its exact purpose and required input format.

Use the following format for your thought process:

Question: The input question you must answer.
Thought: I need to answer the question. I will analyze it to choose the best tool. [Your reasoning for choosing the tool]. The tool's description says it requires [required input]. I will now formulate the correct input.
Action: The action to take, should be one of [{tool_names}].
Action Input: The precise input for the selected tool.
Observation: The result of the action. This is your ONLY source of truth.
Thought: I have received the information from the Observation. I will now analyze the result and construct the final answer based *directly* on the Observation, following all formatting rules.

**CRITICAL INSTRUCTIONS FOR FINAL ANSWER:**
1. Your final answer MUST be a single, valid JSON object wrapped in ```json ... ```. Do not add any text before or after the JSON block.
2. The JSON object must have two keys: "type" and "data".
3. The 'type' must be 'text', 'table', 'chart', or 'error'. Choose the best type to represent the data.
4. The 'data' must ONLY contain information from the 'Observation' step and must follow the format below.

**Data Formatting Rules:**
- **For `type: 'table'`:** The 'data' key must contain an array of JSON objects. The Observation result, if it's a list of tuples from SQL, must be converted into this format.
  Example: `[ {{"clientName": "John Doe", "stock": "AAPL"}}, {{"clientName": "Jane Smith", "stock": "GOOG"}} ]`
- **For `type: 'chart'`:** The 'data' key must contain an array of JSON objects, where each object has a "name" key (for the X-axis label) and a "value" key (for the bar height). This is for aggregations like totals per person/category.
  Example: `[ {{"name": "Manager A", "value": 500000}}, {{"name": "Manager B", "value": 750000}} ]`
- **For `type: 'text'`:** The 'data' key must contain a single user-friendly string with the answer.
- **For `type: 'error'`:** The 'data' key must contain a string explaining the issue.

Final Answer:
```json
{{
  "type": "...",
  "data": "..."
}}
```
Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

prompt = PromptTemplate.from_template(prompt_template_str)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# --- FastAPI App ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.on_event("startup")
async def startup_event():
    print("Setting up mock data on startup...")
    setup_mock_data()
    print("Startup complete.")

@app.get("/")
def read_root():
    return {"Status": "API is running"}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    try:
        response = agent_executor.invoke({"input": request.question})
        output_str = response.get('output', '{}')

        json_str = None
        match = re.search(r"```json\s*(.*?)\s*```", output_str, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            start_index = output_str.find('{')
            end_index = output_str.rfind('}') + 1
            if start_index != -1 and end_index != -1:
                json_str = output_str[start_index:end_index]

        if not json_str:
            print(f"Error: Could not extract JSON from model output.\nOutput:\n{output_str}")
            return {"type": "error", "data": "The model did not return a valid JSON response."}

        return json.loads(json_str)

    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON.\nString was:\n{json_str}") # type: ignore
        return {"type": "error", "data": "Failed to decode the JSON response from the model.", "raw_output": output_str} # type: ignore
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# To run the server: uvicorn main:app --reload
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
