from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CallerState:
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    property_type: Optional[str] = None
    conversation_history: list = field(default_factory=list)
    data_saved: bool = False

    def missing_fields(self) -> list:
        fields = {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "role": self.role,
            "property_type": self.property_type,
        }
        return [k for k, v in fields.items() if v is None]

    def is_complete(self) -> bool:
        return len(self.missing_fields()) == 0


call_sessions: dict[str, CallerState] = {}