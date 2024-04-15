from pydantic import BaseModel


class StockData(BaseModel):
    name: str
    amount: int
    user_id: int
    purchasePrice: float
    purchaseDate: str