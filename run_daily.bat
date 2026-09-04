@echo off
REM ============================================================
REM APIx Daily Pipeline Runner
REM Runs: fetch_serpapi -> clean_data -> calculate_index -> innovation_engine
REM Logs everything (with timestamps) to run_log.txt in this folder.
REM ============================================================

cd /d "%~dp0"

echo. >> run_log.txt
echo ============================================== >> run_log.txt
echo Run started: %DATE% %TIME% >> run_log.txt
echo ============================================== >> run_log.txt

call .venv\Scripts\activate.bat

echo. >> run_log.txt
echo --- fetch_serpapi.py --- >> run_log.txt
python fetch_serpapi.py >> run_log.txt 2>&1

echo. >> run_log.txt
echo --- clean_data.py --- >> run_log.txt
python clean_data.py >> run_log.txt 2>&1

echo. >> run_log.txt
echo --- calculate_index.py --- >> run_log.txt
python calculate_index.py >> run_log.txt 2>&1

echo. >> run_log.txt
echo --- innovation_engine.py --- >> run_log.txt
python innovation_engine.py >> run_log.txt 2>&1

echo. >> run_log.txt
echo Run finished: %DATE% %TIME% >> run_log.txt
echo ============================================== >> run_log.txt
