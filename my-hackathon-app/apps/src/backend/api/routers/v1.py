from backend.main import app 
from fastapi import APIRouter 

router = APIRouter(prefix="/v1", tags=["v1"])

@router.get("/")
def health():
    return {"status": "ok"}
