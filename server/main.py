from fastapi import FastAPI

app = FastAPI(title="NetGuard Pro")

@app.get("/")
def root():
    return {"status": "NetGuard Pro API running"}
