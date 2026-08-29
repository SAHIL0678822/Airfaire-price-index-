@echo off
REM Runs the scraper, then the cleaner, and logs output with a timestamp.
REM This is what Windows Task Scheduler will trigger daily.

cd /d C:\Users\sahil\Desktop\API

echo ===== Run started: %DATE% %TIME% ===== >> run_log.txt

call .venv\Scripts\activate.bat

python fetch_serpapi.py >> run_log.txt 2>&1
python clean_data.py >> run_log.txt 2>&1

echo ===== Run finished: %DATE% %TIME% ===== >> run_log.txt
echo. >> run_log.txt
