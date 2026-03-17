"""
Daily flight price tracker
Routes : IAD -> Tokyo (non-stop, UA 803) | RDU -> Tokyo (1-stop)
Windows: Nov 17-27 / Nov 18-28 / Nov 19-29
"""

import os
from datetime import date
from dotenv import load_dotenv
import requests
from serpapi import GoogleSearch

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "iad-tokyo-flights-adebowale")

ROUTES = [
    {
        "origin":        "IAD",
        "destinations":  ["HND"],   # UA 803 flies IAD → HND
        "label":         "DC (IAD)",
        "flight_number": None,      # any non-stop
        "stops":         "1",       # non-stop only
    },
    {
        "origin":        "RDU",
        "destinations":  ["NRT", "HND"],
        "label":         "Raleigh (RDU)",
        "flight_number": None,      # any airline
        "stops":         "2",       # 1 stop or fewer
    },
]

DATE_WINDOWS = [
    ("2026-11-17", "2026-11-27"),
    ("2026-11-18", "2026-11-28"),
    ("2026-11-19", "2026-11-29"),
]

# ── Flight search ─────────────────────────────────────────────────────────────

def search_flights(origin, destination, depart, ret, stops):
    params = {
        "engine":        "google_flights",
        "departure_id":  origin,
        "arrival_id":    destination,
        "outbound_date": depart,
        "return_date":   ret,
        "type":          "1",
        "stops":         stops,
        "currency":      "USD",
        "hl":            "en",
        "api_key":       os.getenv("SERPAPI_KEY"),
    }
    results = GoogleSearch(params).get_dict()
    if "error" in results:
        print(f"  Error: {results['error']}")
        return []
    return results.get("best_flights", []) + results.get("other_flights", [])


def find_best_for_window(route, depart, ret):
    all_offers = []
    for dest in route["destinations"]:
        all_offers.extend(search_flights(route["origin"], dest, depart, ret, route["stops"]))

    if not all_offers:
        return None

    if route["flight_number"]:
        filtered = [
            o for o in all_offers
            if any(f.get("flight_number") == route["flight_number"] for f in o.get("flights", []))
        ]
        pool = filtered if filtered else all_offers
    else:
        pool = all_offers

    return min(pool, key=lambda o: o.get("price", float("inf")))


# ── Format ────────────────────────────────────────────────────────────────────

def format_leg(flights):
    if not flights:
        return "N/A"
    f    = flights[0]
    dep  = f['departure_airport']['time']
    arr  = f['arrival_airport']['time']
    hrs  = round(f.get('duration', 0) / 60, 1)
    code = f.get('flight_number', '')
    return f"  {code}  {dep} -> {arr}  ({hrs} hrs)"


def format_route_message(route, results):
    origin = route["origin"]
    lines  = [f"Tokyo Flights from {origin} | {date.today()}", ""]

    any_found = False
    for (depart, ret), offer in results:
        d_day = depart[8:10]
        r_day = ret[8:10]
        window_label = f"Nov {d_day}-{r_day}"
        if offer is None:
            lines.append(f"{window_label}: No results")
        else:
            any_found = True
            price = offer.get("price", "?")
            leg   = format_leg(offer.get("flights", []))
            lines.append(f"{window_label}: ${price} round trip")
            lines.append(leg)
        lines.append("")

    if not any_found:
        lines.append("No flights found - check google.com/flights")
    else:
        lines.append("Book: google.com/flights")

    return "\n".join(lines)


# ── Notify ────────────────────────────────────────────────────────────────────

def send_notification(body, title):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=body.encode("utf-8"),
        headers={"Title": title},
    )
    print(f"Notification sent: {title}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Running flight check on {date.today()}...\n")

    for route in ROUTES:
        print(f"Checking {route['origin']} -> Tokyo...")
        results = []
        for (depart, ret) in DATE_WINDOWS:
            offer = find_best_for_window(route, depart, ret)
            results.append(((depart, ret), offer))
            status = f"${offer['price']}" if offer else "none"
            print(f"  {depart} -> {ret}: {status}")

        msg   = format_route_message(route, results)
        title = f"Tokyo Flights | {route['origin']}"
        print(msg)
        send_notification(msg, title)


if __name__ == "__main__":
    main()
