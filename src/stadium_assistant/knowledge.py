"""Venue knowledge base.

A small, structured description of a representative World Cup 2026 venue. In a
production system this would be backed by a database or the official venue GIS;
here it is a self-contained, dependency-free dataset so the app runs anywhere.
The retrieval function selects only the facts relevant to the user's intent,
which keeps LLM prompts small (lower cost, lower latency) and grounds answers
in real venue data rather than model guesswork.

Assumption: distances and facility names are illustrative and would be replaced
with per-stadium data ingested before match day.
"""

from __future__ import annotations

from .context import AccessibilityNeed, Intent, StadiumStatus

VENUE_NAME = "World Cup 2026 Stadium (sample venue)"


# Each fact carries the intents it serves and any accessibility needs it is
# especially relevant to, so retrieval can rank by user context.
_FACTS: list[dict] = [
    {
        "id": "gate-accessible",
        "text": "Gate A is the step-free accessible entrance with a level path, "
                "widened lanes and staff trained in disability assistance.",
        "intents": [Intent.NAVIGATION, Intent.ACCESSIBILITY],
        "needs": [AccessibilityNeed.MOBILITY, AccessibilityNeed.VISION],
    },
    {
        "id": "elevators",
        "text": "Elevators to all seating tiers are located behind Gates A and D. "
                "Ramps connect the lower concourse where elevators are busy.",
        "intents": [Intent.NAVIGATION, Intent.ACCESSIBILITY],
        "needs": [AccessibilityNeed.MOBILITY],
    },
    {
        "id": "wheelchair-assist",
        "text": "Complimentary wheelchair assistance can be requested at any gate "
                "or the Guest Services booth near Gate A.",
        "intents": [Intent.ACCESSIBILITY, Intent.SERVICES],
        "needs": [AccessibilityNeed.MOBILITY],
    },
    {
        "id": "hearing-loop",
        "text": "Guest Services booths have hearing loops, and large screens show "
                "captioned announcements. Assistive listening devices are free to borrow.",
        "intents": [Intent.ACCESSIBILITY, Intent.SERVICES],
        "needs": [AccessibilityNeed.HEARING],
    },
    {
        "id": "sensory-room",
        "text": "A quiet sensory room with low lighting is on the main concourse "
                "near Section 112, open throughout the match for anyone needing a calm space.",
        "intents": [Intent.ACCESSIBILITY, Intent.SERVICES],
        "needs": [AccessibilityNeed.SENSORY, AccessibilityNeed.COGNITIVE],
    },
    {
        "id": "guide-audio",
        "text": "For blind and low-vision guests, tactile maps and audio wayfinding "
                "are available at Guest Services, and guide dogs are welcome throughout.",
        "intents": [Intent.ACCESSIBILITY, Intent.NAVIGATION],
        "needs": [AccessibilityNeed.VISION],
    },
    {
        "id": "restrooms",
        "text": "Accessible restrooms are on every concourse level next to the main "
                "elevators; the nearest to the lower bowl is beside Section 108.",
        "intents": [Intent.SERVICES, Intent.ACCESSIBILITY],
        "needs": [AccessibilityNeed.MOBILITY],
    },
    {
        "id": "first-aid",
        "text": "First aid stations are on the lower concourse near Section 104 and "
                "the upper concourse near Section 320. Staff can reach you if you cannot move.",
        "intents": [Intent.SERVICES],
        "needs": [],
    },
    {
        "id": "water",
        "text": "Free water-refill stations are on every concourse; bring a reusable "
                "bottle to skip queues and cut single-use plastic.",
        "intents": [Intent.SERVICES, Intent.SUSTAINABILITY],
        "needs": [],
    },
    {
        "id": "recycling",
        "text": "Recycling and compost bins sit beside every concession stand. "
                "Cups and food packaging at this venue are compostable.",
        "intents": [Intent.SUSTAINABILITY],
        "needs": [],
    },
    {
        "id": "transit",
        "text": "The accessible transit hub is a 6-minute step-free walk from Gate A. "
                "Trains run every 10 minutes; step-free platforms are signposted.",
        "intents": [Intent.TRANSPORT, Intent.ACCESSIBILITY],
        "needs": [AccessibilityNeed.MOBILITY],
    },
    {
        "id": "parking-dropoff",
        "text": "Accessible parking and a passenger drop-off are in Lot 2, closest to "
                "Gate A. Display a valid accessibility permit for Lot 2 access.",
        "intents": [Intent.TRANSPORT, Intent.ACCESSIBILITY],
        "needs": [AccessibilityNeed.MOBILITY],
    },
    {
        "id": "family",
        "text": "A family room with baby-changing and a nursing space is on the main "
                "concourse near Section 118.",
        "intents": [Intent.SERVICES],
        "needs": [],
    },
]


def get_dynamic_facts(status: any) -> list[str]:
    """Convert raw stadium telemetry statuses into user-friendly facts."""
    if not status:
        return []

    # Convert model to dict if it's a Pydantic model
    if hasattr(status, "model_dump"):
        data = status.model_dump()
    elif hasattr(status, "dict"):
        data = status.dict()
    elif isinstance(status, dict):
        data = status
    else:
        return []

    facts = []

    # Gate Congestion
    gate_congestion = data.get("gate_congestion", {})
    for gate, level in gate_congestion.items():
        if level != "Low":
            facts.append(f"Gate {gate} is currently experiencing {level} crowd congestion.")

    # Elevator status
    elevator_status = data.get("elevator_status", {})
    for gate, state in elevator_status.items():
        if state == "Offline":
            facts.append(f"The elevator at Gate {gate} is temporarily offline.")

    # Transit status
    transit_status = data.get("transit_status")
    if transit_status and transit_status != "On Time":
        facts.append(f"Trains at the accessible transit hub are experiencing {transit_status}.")

    # Concession status
    concession_times = data.get("concession_times")
    if concession_times and concession_times != "Normal":
        facts.append(f"Concessions are currently {concession_times}.")

    # Sensory room occupancy
    sensory_room = data.get("sensory_room_occupancy")
    if sensory_room and sensory_room != "Open":
        facts.append(f"The sensory room near Section 112 is {sensory_room}.")

    # Active alert
    active_alert = data.get("active_alert")
    if active_alert:
        facts.append(f"Alert: {active_alert}")

    return facts


def retrieve_facts(
    intent: Intent,
    needs: list[AccessibilityNeed] | None = None,
    limit: int = 4,
    stadium_status: StadiumStatus | None = None,
) -> list[str]:
    """Return the most relevant venue facts for an intent and needs.

    Scoring rewards facts that match the intent and, more strongly, facts that
    match a declared accessibility need. Results are truncated so prompts stay
    compact. Deterministic ordering (score, then original order) keeps output
    stable and testable.
    """
    dynamic_facts = get_dynamic_facts(stadium_status)

    needs = needs or []
    scored: list[tuple[int, int, str]] = []
    for order, fact in enumerate(_FACTS):
        score = 0
        if intent in fact["intents"]:
            score += 2
        for need in needs:
            if need in fact["needs"]:
                score += 3
        if score > 0:
            scored.append((score, -order, fact["text"]))

    if not scored:
        # Nothing matched (e.g. a general greeting): offer a couple of
        # universally useful facts rather than nothing.
        return dynamic_facts + [_FACTS[0]["text"], _FACTS[8]["text"]]

    scored.sort(reverse=True)
    static_results = [text for _, _, text in scored[:limit]]
    return dynamic_facts + static_results

