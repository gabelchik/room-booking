from pydantic import BaseModel

class DummyLoginSchema(BaseModel):
    role: str