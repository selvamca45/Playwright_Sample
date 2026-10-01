from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("W1D4_FastAPI:app", port=8001, reload=True)