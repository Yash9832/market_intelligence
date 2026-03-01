import os
import json
import sqlite3
import re
import io
import base64
import datetime
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import nest_asyncio

import streamlit as st
from PIL import Image
import requests
from urllib.request import urlopen, Request
import certifi
import pandas as pd

# FastAPI imports (if used separately)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import yfinance as yf
from datetime import datetime, timedelta
from dateutil.parser import parse

# Import your existing modules
from newsapi_fetcher import get_top_5_news_json_by_keyword as fetch_articles
from yfinance_extractor import get_clean_data as get_price_history
from reddit_extractor import get_top_5_reddit_discussions_json as fetch_posts
from NER_model import ner_extraction as extract_entities
from sentiment_model import finbert_sentiment_analysis as predict_sentiment
from trend_model import stock_forecast_tool

# Apply nest_asyncio for Streamlit compatibility
nest_asyncio.apply()

# Database setup for conversation memory
class ConversationMemory:
    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """)
        conn.commit()
        conn.close()

    def create_conversation(self, session_id: str, title: str = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        cursor.execute("""
            INSERT INTO conversations (session_id, title)
            VALUES (?, ?)
        """, (session_id, title))
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conversation_id

    def add_message(self, conversation_id: int, role: str, content: str, metadata: Dict = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (conversation_id, role, content, metadata_json))
        conn.commit()
        conn.close()

    def get_conversation_history(self, conversation_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, timestamp, metadata
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """, (conversation_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "role": row[0],
                "content": row[1],
                "timestamp": row[2],
                "metadata": json.loads(row[3]) if row[3] else {}
            }
            for row in rows
        ]

    def get_conversations(self, session_id: str) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, created_at
            FROM conversations
            WHERE session_id = ?
            ORDER BY created_at DESC
        """, (session_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {"id": row[0], "title": row[1], "created_at": row[2]}
            for row in rows
        ]

    def delete_conversation(self, conversation_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        conn.close()


# Enhanced Gemini Wrapper with memory
class GeminiWrapper:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyCMil_XRE20uMZPkT2X5BOKLSUDKgVVXl0"
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-pro")

    def complete_with_memory(self, prompt: str, conversation_history: List[Dict]) -> str:
        context = "".join(
            f"{msg['role'].title()}: {msg['content']}\n"
            for msg in conversation_history[-10:]
        )
        full_prompt = f"Previous conversation context:\n{context}\nCurrent query: {prompt}"
        response = self.model.generate_content(full_prompt)
        if response and response.candidates:
            return response.candidates[0].content.parts[0].text.strip()
        return "No response generated."


# Tool wrappers and mapping
def news_tool_func(query: str) -> str:
    news_json = json.loads(fetch_articles(query))
    articles = news_json.get("top_articles", [])
    return "\n\n".join(
        f"Title: {a.get('title')}\nSource: {a.get('source')}\nDate: {a.get('date')}\nSnippet: {a.get('snippet')}\nURL: {a.get('url')}"
        for a in articles
    )

def reddit_fetcher_wrapper(query: str) -> str:
    return fetch_posts([query])

def stock_forecast_wrapper(ticker: str, periods: int = 7) -> Tuple[str, Optional[str]]:
    try:
        summary, img_b64 = stock_forecast_tool(ticker, periods)
        return summary, img_b64
    except Exception as e:
        return f"Error during forecasting: {e}", None

def fundamental_data_tool(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        keys = [
            "currentPrice","marketCap", "forwardPE", "priceToBook", "beta", "dividendYield",
            "totalRevenue", "grossProfits", "ebitda", "netIncomeToCommon",
            "profitMargins"
        ]
        return "\n".join(f"{k}: {info.get(k, 'N/A')}" for k in keys)
    except Exception as e:
        return f"Error fetching fundamentals: {e}"

from datetime import datetime, timedelta

def stock_price_tool(ticker: str, start_date: str, end_date: str) -> str:
    try:
        stock = yf.Ticker(ticker.upper())
        # yfinance end date is exclusive so add one day to include last day
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        hist = stock.history(start=start_date, end=end_dt.strftime("%Y-%m-%d"))
        if hist.empty:
            return f"No data found for {ticker} between {start_date} and {end_date}."
        df = hist.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
        return df.to_json(orient="records")
    except Exception as e:
        return f"Error fetching historical data: {str(e)}"
    
import plotly.graph_objects as go
import base64
import io

import plotly.graph_objects as go
import json

def plotly_stock_price_figure(input_json: str):
    data = json.loads(input_json)
    dates = [d['date'] for d in data]
    opens = [d['open'] for d in data]
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    closes = [d['close'] for d in data]

    fig = go.Figure(data=[go.Candlestick(
        x=dates,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        increasing_line_color='green',
        decreasing_line_color='red'
    )])
    fig.update_layout(title='NVIDIA (NVDA) Stock Price (1-Year)', xaxis_title='Date', yaxis_title='Price (USD)')
    return fig



TOOLS = {
    "News Fetcher": news_tool_func,
    "Stock Price": stock_price_tool,
    "Reddit Fetcher": reddit_fetcher_wrapper,
    "Entity Extractor": extract_entities,
    "Sentiment Analyzer": predict_sentiment,
    "Stock Forecaster": stock_forecast_wrapper,
    "RAG Responder": lambda q: "RAG response for: " + q,
    "Fundamentals Extractor": fundamental_data_tool,
    "Plotly Plot": plotly_stock_price_figure,
}

REACT_TEMPLATE = """
You are a market intelligence AI assistant using the ReAct framework.
When given a query, reason step-by-step using Thought/Action/Action Input/Observation format.
While answering, ensure to mention tools, function used and their inputs parameters.
Decide inputs for tools based on the user's query.

Available tools:
{tools_list}

Start!

Question: {query}

{history}

Thought:
"""

def parse_action(output: str):
    act = re.search(r"Action:\s*(.*)", output)
    inp = re.search(r"Action Input:\s*(.*)", output)
    return (act.group(1).strip() if act else None,
            inp.group(1).strip() if inp else None)


def get_prompt(query: str, history: str, tools: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"Current date: {today}\n\n" + REACT_TEMPLATE.format(
    tools_list=tools, query=query, history=history
)


def extract_month_year(query: str) -> Optional[str]:
    m = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b", query)
    return f"{m.group(0)}" if m else None


def is_future(month_year: str) -> bool:
    try:
        dt = parse(month_year)
        now = datetime.now()
        return (dt.year, dt.month) > (now.year, now.month)
    except:
        return False


async def react_loop(query: str, convo: List[Dict]) -> Dict[str, Any]:
    # Refuse future-date requests
    month_year = extract_month_year(query)
    if month_year and is_future(month_year):
        return {
            "final_answer": f"Cannot provide data for future date '{month_year}'.",
            "reasoning_trace": "",
            "plot_image": None
        }

    tools_list = "\n".join(TOOLS.keys())
    history_str = "".join(
        f"{'Human' if m['role']=='user' else 'AI'}: {m['content']}\n"
        for m in convo[-5:]
    )
    gem = GeminiWrapper()
    reasoning = ""
    plot_img = None

    while True:
        prompt = get_prompt(query, history_str, tools_list)
        resp = gem.complete_with_memory(prompt, convo)
        if "Final Answer:" in resp:
            return {"final_answer": resp.split("Final Answer:")[-1].strip(),
                    "reasoning_trace": reasoning,
                    "plot_image": plot_img}

        thought = re.search(r"Thought:(.*)", resp, re.DOTALL)
        thought_text = thought.group(1).strip() if thought else resp.strip()
        tool_name, tool_input = parse_action(resp)
        if not tool_name or tool_name not in TOOLS:
            return {"final_answer": resp.strip(),
                    "reasoning_trace": reasoning,
                    "plot_image": plot_img}

        obs = TOOLS[tool_name](tool_input)
        if isinstance(obs, tuple):  # This is new to handle plotly tool output
            observation, plot_img = obs
        else:
            observation = obs

        reasoning += (
            f"Thought:\n{thought_text}\n\n"
            f"Action: {tool_name}\nInput: {tool_input}\n"
            f"Observation:\n{observation}\n\n-----\n\n"
        )
        history_str += f"Thought: {thought_text}\nAction: {tool_name}\nObservation: {observation}\n"
        convo.append({"role": "assistant", "content": observation})

def main():
    st.set_page_config(
        page_title="AI Financial Intelligence Assistant",
        page_icon="💰",
        layout="wide"
    )

    # CSS tweaks
    st.markdown("""
    <style>
    .chat-message { padding:1rem; border-radius:0.5rem; margin-bottom:1rem; }
    .user-message { background-color:#e3f2fd; margin-left:20%; }
    .assistant-message { background-color:#f5f5f5; margin-right:20%; }
    .message-timestamp { font-size:0.8rem; color:#666; margin-top:0.5rem; }
    </style>
    """, unsafe_allow_html=True)

    # Session init
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory()
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(datetime.now().timestamp())
    if "conv_id" not in st.session_state:
        st.session_state.conv_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sidebar
    with st.sidebar:
        st.title("💰 AI Financial Assistant")

        if st.button("🆕 New Chat"):
            st.session_state.conv_id = None
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.subheader("📝 Chat History")
        convs = st.session_state.memory.get_conversations(st.session_state.session_id)
        for conv in convs:
            is_active = st.session_state.conv_id == conv["id"]
            if st.button(conv["title"], key=f"title_{conv['id']}"):
                st.session_state.conv_id = conv["id"]
                st.session_state.messages = st.session_state.memory.get_conversation_history(conv["id"])
                st.rerun()
            if st.button("🗑️", key=f"del_{conv['id']}"):
                st.session_state.memory.delete_conversation(conv["id"])
                if st.session_state.conv_id == conv["id"]:
                    st.session_state.conv_id = None
                    st.session_state.messages = []
                st.rerun()

        if st.session_state.messages and st.button("📤 Export Chat"):
            export = {
                "conversation_id": st.session_state.conv_id,
                "timestamp": datetime.now().isoformat(),
                "messages": st.session_state.messages
            }
            st.download_button(
                "Download Chat History",
                data=json.dumps(export, indent=2),
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    # Main interface
    st.title("🤖 AI Financial Intelligence Assistant")
    st.markdown("Ask me anything about stocks, markets, news, and financial analysis!")

    # Display conversation messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            timestamp = msg.get("timestamp")
            if timestamp:
                st.caption(f"🕒 {timestamp}")
            if msg.get("plot_image"):
                header, b64 = msg["plot_image"].split(",", 1)
                img = Image.open(io.BytesIO(base64.b64decode(b64)))
                st.image(img, use_column_width=True)

    # User text input (no audio)
    prompt = st.chat_input("Ask me about financial markets...", key="input")
    if prompt:
        if st.session_state.conv_id is None:
            title = prompt if len(prompt) <= 50 else prompt[:47] + "..."
            st.session_state.conv_id = st.session_state.memory.create_conversation(
                st.session_state.session_id, title
            )
        # Save user message
        user_msg = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.messages.append(user_msg)
        st.session_state.memory.add_message(st.session_state.conv_id, "user", prompt)

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"🕒 {user_msg['timestamp']}")

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your request..."):
                result = asyncio.run(react_loop(prompt, st.session_state.messages))
                resp = result["final_answer"]
                plot_img = result.get("plot_image")

                st.markdown(resp)

                if plot_img:
                    header, b64 = plot_img.split(",", 1)
                    img = Image.open(io.BytesIO(base64.b64decode(b64)))
                    st.image(img, use_column_width=True)

                ai_msg = {
                    "role": "assistant",
                    "content": resp,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "plot_image": plot_img
                }
                st.session_state.messages.append(ai_msg)
                st.session_state.memory.add_message(
                    st.session_state.conv_id, "assistant", resp,
                    {"plot_image": plot_img} if plot_img else None
                )
                timestamp = ai_msg.get("timestamp")
                if timestamp:
                    st.caption(f"🕒 {timestamp}")

        # No explicit rerun here—Streamlit reruns on interaction automatically


if __name__ == "__main__":
    main()
