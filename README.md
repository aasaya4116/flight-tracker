# Flight Tracker

Daily tracker for non-stop round-trip flights from Washington Dulles (IAD) to Tokyo Haneda (HND). It searches Google Flights through SerpAPI and publishes the lowest fare for each configured date window to ntfy.

## Notifications

Install the ntfy app and subscribe to the same topic configured by `NTFY_TOPIC`. The current default topic is defined in `tracker.py`.

If iPhone notifications stop arriving, remove the topic from ntfy and add it again. This refreshes the iOS push subscription.

## Run locally

1. Copy `.env.example` to `.env`.
2. Add your SerpAPI key and ntfy topic to `.env`.
3. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Run the tracker:

   ```powershell
   python tracker.py
   ```

## Automation

GitHub Actions runs the tracker once per day. You can also start a run manually from the repository's **Actions** page by selecting **Daily Flight Tracker** and choosing **Run workflow**.

The workflow is defined in `.github/workflows/daily_tracker.yml`.
