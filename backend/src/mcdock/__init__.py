import uvicorn

def dev():
    uvicorn.run("src.mcdock.main:app", host="127.0.0.1", port=8000, reload=True)