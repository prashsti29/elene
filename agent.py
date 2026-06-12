from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from state import CallerState, call_sessions
from sheets import save_to_sheets
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama3-8b-8192",
    temperature=0.4
)

SYSTEM_PROMPT = """
You are a professional real estate intake assistant on a phone call.
Your job is to naturally collect the following information from the caller:
- name
- phone
- email  
- role (are they a property owner or a real estate broker/agent)
- property_type (apartment, villa, plot, commercial, etc)
- location (city and area)
- price_expectation

Rules:
- Ask for ONE missing field at a time, naturally in conversation
- Never sound robotic or list out questions
- If the caller gives multiple details at once, acknowledge all of them
- Once you have all details, confirm them and say goodbye professionally
- Always respond in a warm, professional tone

At the END of every response, output a JSON block like this (no matter what):
<extract>
{
  "name": null,
  "phone": null,
  "email": null,
  "role": null,
  "property_type": null,
  "location": null,
  "price_expectation": null
}
</extract>

Only populate fields you extracted from THIS message. Leave others null.
"""

def build_messages(state: CallerState, user_input: str):
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    for turn in state.conversation_history[:-1]:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    
    missing = state.missing_fields()
    context = f"\nStill need to collect: {missing}\nCaller just said: {user_input}"
    messages.append(HumanMessage(content=context))
    
    return messages


def extract_and_update(state: CallerState, llm_response: str):
    try:
        start = llm_response.index("<extract>") + len("<extract>")
        end = llm_response.index("</extract>")
        json_str = llm_response[start:end].strip()
        extracted = json.loads(json_str)
        
        for field, value in extracted.items():
            if value is not None and getattr(state, field) is None:
                setattr(state, field, value)
    except:
        pass


def clean_response(llm_response: str) -> str:
    try:
        end = llm_response.index("<extract>")
        return llm_response[:end].strip()
    except:
        return llm_response.strip()


async def get_agent_response(state: CallerState, user_input: str) -> str:
    messages = build_messages(state, user_input)
    response = llm.invoke(messages)
    raw = response.content
    
    extract_and_update(state, raw)
    
    if state.is_complete() and not state.data_saved:
        await save_to_sheets(state)
        state.data_saved = True
    
    return clean_response(raw)