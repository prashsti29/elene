from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from state import CallerState, call_sessions
from sheets import save_to_sheets
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.2
)

SYSTEM_PROMPT = """
You are a real estate intake assistant on a phone call. Collect: name, phone, email, whether they are a property owner or broker, and property type (residential or commercial).

Rules:
- Ask for ONE missing field at a time, conversationally
- Never mention field names or say what you are collecting
- Never repeat a question for something already collected
- For phone numbers: read back digits then move on, do not ask for confirmation
- Only extract what the caller explicitly said, never assume or infer
- When all fields collected, say: Thank you, we have all your details. Goodbye!
"""

EXTRACT_PROMPT = """Extract information from the user message. Return ONLY valid JSON, nothing else, no explanation:
{"name": null, "phone": null, "email": null, "role": null, "property_type": null}
- role must be either "owner" or "broker" or null
- property_type must be either "residential" or "commercial" or null
- Only populate what the user explicitly stated. null for everything else."""

def build_messages(state: CallerState, user_input: str):
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
    for turn in state.conversation_history[:-1]:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    
    collected = {k: v for k, v in {
        "name": state.name,
        "phone": state.phone,
        "email": state.email,
        "role": state.role,
        "property_type": state.property_type,
    }.items() if v is not None}
    
    missing = state.missing_fields()
    context = f"\nALREADY COLLECTED (do not ask again): {collected}\nSTILL MISSING: {missing}\nCaller just said: {user_input}"
    messages.append(HumanMessage(content=context))
    
    return messages

async def get_agent_response(state: CallerState, user_input: str) -> str:
    messages = build_messages(state, user_input)
    
    response = llm.invoke(messages)
    agent_reply = response.content.strip()
    
    extract_messages = [
        SystemMessage(content=EXTRACT_PROMPT),
        HumanMessage(content=f"User said: {user_input}")
    ]
    extract_response = llm.invoke(extract_messages)
    
    try:
        cleaned = extract_response.content.strip().replace("```json", "").replace("```", "")
        extracted = json.loads(cleaned)
        for field, value in extracted.items():
            if value is not None and value != "" and hasattr(state, field) and getattr(state, field) is None:
                setattr(state, field, value)
        print(f"State: {state.name} | {state.phone} | {state.email} | {state.role} | {state.property_type}")
    except Exception as e:
        print(f"Extraction error: {e}")
    
    if state.is_complete() and not state.data_saved:
        await save_to_sheets(state)
        state.data_saved = True
    
    return agent_reply