
import pydantic
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

class Account(BaseModel):
    age: float
    email: str
    name: str
    