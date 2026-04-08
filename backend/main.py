import os
import re
from typing import Dict, TypedDict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Customer Service Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- STATE --------
class State(TypedDict):
    query: str
    category: str
    sentiment: str
    response: str

# -------- REQUEST/RESPONSE --------
class QueryRequest(BaseModel):
    query: str
    openrouter_api_key: str

class QueryResponse(BaseModel):
    query: str
    category: str
    sentiment: str
    response: str

# -------- TOOLS --------
def calculator_tool(expression: str):
    try:
        return str(eval(expression))
    except:
        return "Invalid expression"

def email_tool(content: str):
    return f"[Email drafted and sent]\n\n{content}"

# -------- BUILD GRAPH --------
def build_agent(api_key: str):
    llm = ChatOpenAI(
        model="meta-llama/llama-3-8b-instruct",
        temperature=0,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    def categorize(state: State) -> State:
        prompt = ChatPromptTemplate.from_template(
            "Categorize this customer query into exactly one word: Technical, Billing, or General. "
            "Reply with only that one word.\nQuery: {query}"
        )
        chain = prompt | llm
        return {"category": chain.invoke({"query": state["query"]}).content.strip()}

    def analyze_sentiment(state: State) -> State:
        prompt = ChatPromptTemplate.from_template(
            "Analyze the sentiment of this message and reply with exactly one word: "
            "Positive, Neutral, or Negative.\nMessage: {query}"
        )
        chain = prompt | llm
        return {"sentiment": chain.invoke({"query": state["query"]}).content.strip()}

    def handle_technical(state: State) -> State:
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful technical support agent. Give a clear, concise technical support response: {query}"
        )
        chain = prompt | llm
        return {"response": chain.invoke({"query": state["query"]}).content}

    def handle_billing(state: State) -> State:
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful billing support agent. Give a clear, concise billing support response: {query}"
        )
        chain = prompt | llm
        return {"response": chain.invoke({"query": state["query"]}).content}

    def handle_general(state: State) -> State:
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful customer support agent. Give a clear, concise general support response: {query}"
        )
        chain = prompt | llm
        return {"response": chain.invoke({"query": state["query"]}).content}

    def escalate(state: State) -> State:
        return {"response": "Your concern has been escalated to a human agent who will contact you shortly. We sincerely apologize for any inconvenience caused."}

    def handle_calculation(state: State) -> State:
        query = state["query"]
        expression_parts = re.findall(r"[\d+\-*/().\s]+", query)
        expression = "".join(expression_parts).strip()
        result = calculator_tool(expression)
        return {"response": f"Calculation result: {result}"}

    def handle_email(state: State) -> State:
        prompt = ChatPromptTemplate.from_template(
            "Draft a professional customer support email for this request: {query}"
        )
        chain = prompt | llm
        content = chain.invoke({"query": state["query"]}).content
        return {"response": email_tool(content)}

    def route_query(state: State) -> str:
        query = state["query"].lower()
        if "calculate" in query or re.search(r"\d[\s]*[+\-*/][\s]*\d", query):
            return "handle_calculation"
        if "email" in query or "draft" in query or "write email" in query:
            return "handle_email"
        if "negative" in state["sentiment"].lower():
            return "escalate"
        elif "technical" in state["category"].lower():
            return "handle_technical"
        elif "billing" in state["category"].lower():
            return "handle_billing"
        else:
            return "handle_general"

    workflow = StateGraph(State)
    workflow.add_node("categorize", categorize)
    workflow.add_node("analyze_sentiment", analyze_sentiment)
    workflow.add_node("handle_technical", handle_technical)
    workflow.add_node("handle_billing", handle_billing)
    workflow.add_node("handle_general", handle_general)
    workflow.add_node("escalate", escalate)
    workflow.add_node("handle_calculation", handle_calculation)
    workflow.add_node("handle_email", handle_email)

    workflow.add_edge("categorize", "analyze_sentiment")
    workflow.add_conditional_edges(
        "analyze_sentiment",
        route_query,
        {
            "handle_technical": "handle_technical",
            "handle_billing": "handle_billing",
            "handle_general": "handle_general",
            "escalate": "escalate",
            "handle_calculation": "handle_calculation",
            "handle_email": "handle_email",
        }
    )
    workflow.add_edge("handle_technical", END)
    workflow.add_edge("handle_billing", END)
    workflow.add_edge("handle_general", END)
    workflow.add_edge("escalate", END)
    workflow.add_edge("handle_calculation", END)
    workflow.add_edge("handle_email", END)
    workflow.set_entry_point("categorize")

    return workflow.compile()

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    # Use API key from request if provided, otherwise load from environment
    api_key = request.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not provided in request or .env file")
    
    agent = build_agent(api_key)
    result = agent.invoke({"query": request.query})
    return QueryResponse(
        query=result["query"],
        category=result.get("category", "General"),
        sentiment=result.get("sentiment", "Neutral"),
        response=result.get("response", "No response generated.")
    )

@app.get("/health")
async def health():
    return {"status": "ok"}
