from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    sender: str = Field(..., examples=["alice-wallet"])
    recipient: str = Field(..., examples=["bob-wallet"])
    amount: float = Field(..., gt=0, examples=[25.5])


class NodeList(BaseModel):
    nodes: list[str] = Field(..., min_length=1, examples=[["127.0.0.1:8001", "127.0.0.1:8002"]])


class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    message: str

