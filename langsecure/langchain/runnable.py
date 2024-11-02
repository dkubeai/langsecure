from __future__ import annotations
from typing import Any, Optional
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langsecure import Langsecure

class RunnableLangsecure(Runnable[Input, Output]):
    def __init__(self, langsecure: Langsecure) -> None:
        self.langsecure = langsecure

    @property
    def InputType(self) -> Input:
        return Any

    @property
    def OutputType(self) -> Input:
        """The type of the output of this runnable as a type annotation."""
        return Any

    def invoke( self, input: Input, config: Optional[RunnableConfig] = None,) -> Output:
        deny, deny_message = self.langsecure._input_enforcer(input)
        if deny is True:
            raise ValueError(deny_message)
        return input