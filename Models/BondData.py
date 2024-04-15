from pydantic import BaseModel


class BondData(BaseModel):
    name: str
    face_value: int
    user_id: int
    purchasePrice: float
    purchaseDate: str