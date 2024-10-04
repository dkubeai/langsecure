from pydantic import BaseModel
from pydantic import ConfigDict
from typing import Literal
from typing import Any

class Result(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        frozen=True,
        json_encoders={
            Any: lambda v: json.dumps(v) if isinstance(v, (dict, list, tuple)) else v
        },
    )
    
    decision: Literal["allow", "deny", "none"] = None
    message: str = ""
    policy_id: str = ""
