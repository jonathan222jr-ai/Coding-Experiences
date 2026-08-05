from pydantic import BaseModel
from typing import List, Optional

class EmailModel(BaseModel):
    subject: str
    sender: str
    body: str
    links: Optional[List[str]] = []