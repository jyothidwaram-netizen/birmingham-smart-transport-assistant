from .chat_parser import parse_journey_message
from .journey_engine import search_live_journey


def process_chat_message(message):

    parsed = parse_journey_message(message)

    origin = parsed.get("origin")
    destination = parsed.get("destination")
    route = parsed.get("route")

    if origin and destination:

        result = search_live_journey(
            origin=origin,
            destination=destination,
            route=route,
        )

        if not result.get("success"):
            return {
                "success": False,
                "reply": (
                    "I could not find a verified journey for "
                    f"{origin} to {destination}. "
                    + result.get("message", "")
                ),
                "data": result,
            }

        candidates = result.get("candidates", [])

        if result.get("live_verified") and candidates:

            candidate = candidates[0]

            delay = candidate.get("delay_sec")

            if delay is None:
                status = "Live vehicle position available"
            elif delay > 60:
                status = f"Approximately {delay / 60:.1f} min delayed"
            elif delay < -60:
                status = f"Approximately {abs(delay) / 60:.1f} min early"
            else:
                status = "Approximately on time"

            reply = (
                f"🚌 I found a live Route "
                f"{candidate.get('route', 'unknown')} vehicle.\n\n"
                f"📍 Current live location: "
                f"{candidate.get('current_latitude'):.5f}, "
                f"{candidate.get('current_longitude'):.5f}\n\n"
                f"🚏 Journey: {origin} → {destination}\n\n"
                f"📡 Live status: {status}\n\n"
                f"⚠️ The current production feed verifies the "
                f"vehicle position, but I will not invent an "
                f"exact boarding ETA without a verified "
                f"stop-sequence/ETA match."
            )

        else:

            candidate = candidates[0]

            reply = (
                f"🚌 I found a scheduled service from "
                f"{origin} to {destination}.\n\n"
                f"Route: {candidate.get('route_id', 'unknown')}\n"
                f"Departure: {candidate.get('departure_time', 'unknown')}\n"
                f"Arrival: {candidate.get('arrival_time', 'unknown')}\n\n"
                f"ℹ️ This is scheduled information, not a "
                f"verified live ETA."
            )

        return {
            "success": True,
            "reply": reply,
            "data": result,
        }

    return {
        "success": True,
        "reply": (
            "I can help with public transport journeys. "
            "Try asking:\n\n"
            "“What is my next bus from Coronation Gardens "
            "to Colmore Row?”"
        ),
        "data": parsed,
    }
