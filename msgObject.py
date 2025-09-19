import datetime
from dataclasses import dataclass


@dataclass
class MsgObject:
    """Container for message data including message text, timestamp, and user ID."""
    msg: str
    time: datetime.datetime
    user_id: int
    user_name: str

    @classmethod
    def create(cls, msg: str, user, time) -> 'MsgObject':
        """Create a new MsgObject with the current timestamp."""
        return cls(msg=msg, time=time, user_id=user.id, user_name=user.full_name)

    def to_html(self) -> str:
        return (f"<b>Name: {self.user_name}</b>\n"
                f"<b>Time: {self.time.hour}:{self.time.minute}:{self.time.second}</b>\n\n"
                f"{self.msg}")

    def to_dict(self) -> dict:
        """Convert MsgObject to a dictionary for JSON serialization."""
        return {
            "msg": self.msg,
            "time": self.time.isoformat(),
            "user_id": self.user_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MsgObject':
        """Create a MsgObject from a dictionary (deserialization from JSON)."""
        return cls(
            msg=data["msg"],
            time=datetime.datetime.fromisoformat(data["time"]),
            user_id=data["user_id"]
        )