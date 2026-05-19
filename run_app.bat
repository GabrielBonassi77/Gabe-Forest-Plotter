@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless true
