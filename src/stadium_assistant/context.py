"""User context modelling and lightweight intent inference.

The assistant's core value is *context-aware* help: the same question gets a
different, better answer depending on who is asking and what they need. This
module defines the validated context object and a small, transparent rule set
that infers the user's intent from their message. Intent inference is
deliberately rule-based (not an extra LLM call) so it is fast, free,
deterministic and easy to test.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from .i18n import normalize_language


class Role(str, Enum):
    """Who is interacting with the assistant."""

    FAN = "fan"
    STAFF = "staff"
    VOLUNTEER = "volunteer"


class AccessibilityNeed(str, Enum):
    """Self-declared accessibility needs that shape the response."""

    MOBILITY = "mobility"        # wheelchair users, limited walking
    VISION = "vision"            # blind / low vision
    HEARING = "hearing"          # deaf / hard of hearing
    SENSORY = "sensory"          # sensory sensitivity, needs quiet routes
    COGNITIVE = "cognitive"      # prefers simple, step-by-step guidance


class Intent(str, Enum):
    """The kind of help the user is asking for."""

    NAVIGATION = "navigation"
    ACCESSIBILITY = "accessibility"
    SERVICES = "services"
    TRANSPORT = "transport"
    SUSTAINABILITY = "sustainability"
    GENERAL = "general"


# Keyword hints per intent. Kept short and readable; order matters only for
# documentation, not logic (we score all intents and take the strongest).
_INTENT_KEYWORDS: dict[Intent, tuple[str, ...]] = {
    Intent.ACCESSIBILITY: (
        "accessible", "wheelchair", "elevator", "lift", "ramp", "step-free",
        "hearing loop", "captions", "sensory", "quiet", "guide dog", "braille",
    ),
    Intent.NAVIGATION: (
        "where", "how do i get", "find", "gate", "section", "seat", "entrance",
        "exit", "concourse", "map", "directions", "nearest",
    ),
    Intent.SERVICES: (
        "toilet", "restroom", "bathroom", "first aid", "medical", "water",
        "food", "atm", "lost", "charging", "prayer", "family", "baby",
    ),
    Intent.TRANSPORT: (
        "parking", "park", "train", "bus", "metro", "shuttle", "taxi",
        "drop-off", "transit", "rideshare", "uber",
    ),
    Intent.SUSTAINABILITY: (
        "recycle", "recycling", "refill", "reusable", "compost", "waste",
        "sustainab", "green", "bottle",
    ),
}


class UserContext(BaseModel):
    """Validated context accompanying every request.

    All fields are optional except the message so that a first-time user with
    no profile can still be helped; the assistant simply has less to reason
    with and asks clarifying questions when needed.
    """

    message: str = Field(..., min_length=1)
    language: str = Field(default="en")
    role: Role = Field(default=Role.FAN)
    accessibility_needs: list[AccessibilityNeed] = Field(default_factory=list)
    location: str | None = Field(
        default=None, description="Where the user is now, e.g. 'Gate C' or 'Section 114'."
    )

    @field_validator("language")
    @classmethod
    def _normalize_language(cls, value: str) -> str:
        return normalize_language(value)

    @field_validator("accessibility_needs")
    @classmethod
    def _dedupe_needs(cls, value: list[AccessibilityNeed]) -> list[AccessibilityNeed]:
        # Preserve order, drop duplicates so downstream logic is stable.
        seen: set[AccessibilityNeed] = set()
        unique: list[AccessibilityNeed] = []
        for need in value:
            if need not in seen:
                seen.add(need)
                unique.append(need)
        return unique

    @property
    def has_accessibility_needs(self) -> bool:
        return len(self.accessibility_needs) > 0


def infer_intent(message: str, needs: list[AccessibilityNeed] | None = None) -> Intent:
    """Infer the user's intent from their message and declared needs.

    Scores each intent by counting keyword hits, then applies a small bias:
    a user with accessibility needs asking a location question is treated as
    an accessibility request so that step-free routing is prioritised.
    """
    text = message.lower()
    scores: dict[Intent, int] = {intent: 0 for intent in _INTENT_KEYWORDS}
    for intent, keywords in _INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[intent] += 1

    best_intent = max(scores, key=lambda i: scores[i])
    best_score = scores[best_intent]

    if best_score == 0:
        return Intent.GENERAL

    # Context bias: accessibility needs upgrade a plain navigation ask.
    if needs and best_intent == Intent.NAVIGATION and scores[Intent.ACCESSIBILITY] == 0:
        return Intent.ACCESSIBILITY

    return best_intent


class StadiumStatus(BaseModel):
    """Dynamic operational metrics of the stadium."""

    gate_congestion: dict[str, str] = Field(
        default_factory=lambda: {"A": "Low", "B": "Low", "C": "Low", "D": "Low"}
    )
    elevator_status: dict[str, str] = Field(
        default_factory=lambda: {"A": "Online", "B": "Online", "C": "Online", "D": "Online"}
    )
    transit_status: str = Field(default="On Time")  # "On Time", "Minor Delays", "Major Delays"
    concession_times: str = Field(default="Normal")  # "Normal", "Busy", "Very Busy"
    sensory_room_occupancy: str = Field(default="Open")  # "Open", "Near Capacity", "Full"
    active_alert: str | None = Field(default=None)

