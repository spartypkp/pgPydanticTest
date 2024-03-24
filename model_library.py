
import pydantic
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

class Account(BaseModel):
    name: str
    age: int
    email: str