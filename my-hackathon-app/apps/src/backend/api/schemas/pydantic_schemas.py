from pydantic import BaseModel, Field

class UserInput(BaseModel):
    query: str =Field(min_length=1, description="Main query")
        