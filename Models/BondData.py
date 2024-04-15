from pydantic import BaseModel


class BondData(BaseModel):
    name: str
    amount: int
    user_id: int
    purchasePrice: float
    purchaseDate: str