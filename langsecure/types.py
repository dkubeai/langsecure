from pydantic import BaseModel
from pydantic import ConfigDict
from typing import Literal
from typing import Any
from typing import List
from typing import Optional
from typing import Union
from typing import TypeVar
from typing import Dict

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


ACTIONS = Literal["log", "deny", "mask", "redact", "filter", "remove", "review", "notify"]
FILTERS = Literal["general_orgcompliance", "proprietary_terms", "content_security", "topics_control", "pii_protection", "hallucination_moderation", "context_security", "compliance_check"]

#TF = TypeVar('T', *_FILTERS)
#TA = TypeVar('T', *_ACTIONS)


class PyFilter(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        frozen=True,
        json_encoders={
            Any: lambda v: json.dumps(v) if isinstance(v, (dict, list, tuple)) else v
        },
    )

    id : Union[FILTERS] 
    rules: Union[str, Dict, List] = "default"
    action: ACTIONS = "log"
    scope: List[Literal["user_input", "context", "bot_response", 'all']] = ['all']

class PySubjects(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        frozen=False,
        json_encoders={
            Any: lambda v: json.dumps(v) if isinstance(v, (dict, list, tuple)) else v
        },
    )

    users: Union[str, List[str]] = '*'
    groups: Union[str, List[str]] = '*'
    roles: Union[str, List[str]] = '*'

    def update(self, **params):
        self.users = params.get('users', self.users)
        self.groups = params.get('groups', self.groups)
        self.roles = params.get('roles', self.roles)

class PyPolicy(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        frozen=True,
        json_encoders={
            Any: lambda v: json.dumps(v) if isinstance(v, (dict, list, tuple)) else v
        },
    )

    id: str
    description: str = ""
    subjects: PySubjects = PySubjects()
    filters: List[PyFilter] = []

    def add_filter(self, filter: PyFilter):
        self.filters.append(filter)
        
    def add_subjects(self, **subjects):
        self.subjects.update(**subjects)
