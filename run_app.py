# run_app.py
import multiprocessing
import subprocess

def run_streamlit():
    subprocess.run(["streamlit", "run", "app.py"])

def run_fastapi():
    subprocess.run(["uvicorn", "webhook_server:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    multiprocessing.Process(target=run_streamlit).start()
    multiprocessing.Process(target=run_fastapi).start()
