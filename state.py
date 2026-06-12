# state.py

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CallerState:
    # All the fields we need to collect
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None          # "owner" or "broker/agent"
    property_type: Optional[str] = None # apartment, villa, plot etc
    location: Optional[str] = None
    price_expectation: Optional[str] = None
    
    # Conversation history for the LLM to remember context
    conversation_history: list = field(default_factory=list)
    
    # Flag: have we saved to sheets yet?
    data_saved: bool = False

    def missing_fields(self) -> list:
        """Returns list of fields not yet collected"""
        fields = {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "role": self.role,
            "property_type": self.property_type,
            "location": self.location,
            "price_expectation": self.price_expectation,
        }
        return [k for k, v in fields.items() if v is None]

    def is_complete(self) -> bool:
        """True when all fields collected"""
        return len(self.missing_fields()) == 0


# Global store: call_sid (Twilio's unique call ID) → CallerState
# This lets us track multiple simultaneous calls
call_sessions: dict[str, CallerState] = {}