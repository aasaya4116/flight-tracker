@echo off
REM Run this once as Administrator to register the daily Task Scheduler job.
REM It will run tracker.py every day at 8:00 AM.

schtasks /create ^
  /tn "FlightPriceTracker" ^
  /tr "python C:\Users\aasay\Documents\flight_tracker\tracker.py" ^
  /sc daily ^
  /st 08:00 ^
  /f

echo Task registered. Check Task Scheduler to confirm.
pause
