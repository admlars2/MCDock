import uvicorn

from .main import app

def dev():
    uvicorn.run("mcdock.main:app", host="127.0.0.1", port=8000, reload=True)