"""
Daily flight price tracker: IAD -> Tokyo (NRT/HND), Nov 19-29
Texts you the cheapest non-stop option found each day via Google Flights (SerpApi).
"""

import os
from datetime import date
from dotenv import load_dotenv
import requests
from serpapi import GoogleSearch

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

ORIGIN       = "IAD"
DESTINATIONS = ["NRT", "HND"]   # Tokyo Narita + Haneda
DEPART_DATE  = "2026-11-19"
RETURN_DATE  = "2026-11-29"
NTFY_TOPIC   = os.getenv("NTFY_TOPIC", "iad-tokyo-flights-adebowale")

# ── Flight search ─────────────────────────────────────────────────────────────

def search_flights(destination: str) -> list[dict]:
    """Return non-stop round-trip offers from Google Flights for one destination."""
    params = {
        "engine":          "google_flights",
        "departure_id":    ORIGIN,
        "arrival_id":      destination,
        "outbound_date":   DEPART_DATE,
        "return_date":     RETURN_DATE,
        "type":            "1",     # round trip
        "stops":           "1",     # non-stop only
        "currency":        "USD",
        "hl":              "en",
        "api_key":         os.getenv("SERPAPI_KEY"),
    }
    results = GoogleSearch(params).get_dict()
    best   = results.get("best_flights", [])
    other  = results.get("other_flights", [])
    print(f"  {destination}: {len(best)} best, {len(other)} other flights found")
    if not best and not other:
        print(f"  Error: {results.get('error', 'unknown')}")
    return best + other


def find_cheapest() -> dict | None:
    """Search both Tokyo airports and return the single cheapest offer."""
    all_offers = []
    for dest in DESTINATIONS:
        all_offers.extend(search_flights(dest))

    if not all_offers:
        return None

    return min(all_offers, key=lambda o: o.get("price", float("inf")))


# ── Format message ────────────────────────────────────────────────────────────

def format_flight_leg(flights: list[dict]) -> str:
    if not flights:
        return "N/A"
    f = flights[0]
    depart_time = f['departure_airport']['time']
    arrive_time = f['arrival_airport']['time']
    airline     = f.get('airline', '')
    flight_num  = f.get('flight_number', '')
    duration_hr = round(f.get('duration', 0) / 60, 1)
    return f"{airline} {flight_num}  |  {depart_time} → {arrive_time}  ({duration_hr} hrs)"


def format_message(offer: dict) -> str:
    price    = offer.get("price", "?")
    legs     = offer.get("flights", [])
    outbound = format_flight_leg(legs)

    return (
        f"✈️ DC → Tokyo  |  Nov 19–29\n"
        f"\n"
        f"💰 ${price} round trip\n"
        f"\n"
        f"🛫 {outbound}\n"
        f"\n"
        f"👉 google.com/flights"
    )


# ── Send notification ─────────────────────────────────────────────────────────

def send_notification(body: str, title: str = "Tokyo Flight Tracker"):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=body.encode("utf-8"),
        headers={"Title": title},
    )
    print("Notification sent.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Searching flights {ORIGIN} -> Tokyo on {date.today()}...")
    offer = find_cheapest()

    if offer is None:
        send_notification(
            "😕 No non-stop flights found today.\nCheck manually at google.com/flights",
            title="Tokyo Flight Tracker - No Results"
        )
        return

    msg = format_message(offer)
    print(msg)
    send_notification(msg)


if __name__ == "__main__":
    main()
