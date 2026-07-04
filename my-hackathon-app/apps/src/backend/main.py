from fastapi import FastAPI
from backend.api.schemas.pydantic_schemas import UserInput

def create_app() -> FastAPI:
    app = FastAPI()
    return app

app = create_app()

@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/query")
def post_query(user_input: UserInput):
    return user_input