from pydantic import BaseModel, HttpUrl, Field
from pathlib import Path
from typing import Union
from typing import Literal
from typing import Optional
from typing import Any
from typing import ClassVar
import inspect

from . import rails

class Langsecure(BaseModel):
    """Base class for langsecure implementation."""

    policy_store: Optional[Union[Path, HttpUrl]] = None
    tracking_server: Optional[Union[Path, HttpUrl]] = None
    rails_backend: Optional[Literal['nvidia-nemoguardrails']] = 'nvidia-nemoguardrails'
    langsecure_server: Optional[HttpUrl] = None

    implementors: ClassVar[dict] = {} 

    def __init__(self, **params):
        super().__init__(**params)

        if self.policy_store == None:
            raise ValueError(f"policy_store must be initialized to a local dir or to a remote server.")

        if isinstance(self.policy_store, Path):
            #Load the policies from the path
            pass
        else:
            raise ValueError(f"policy_store with local directory is only supported. Future versions will support remote store as well.")

        # hardcode rails backend to be nvidia nemoguardrails for now.
        self.rails_backend = 'nvidia-nemoguardrails'


    @classmethod
    def implements(cls, fqcn, implclass):
        cls.implementors[fqcn] = implclass

    @classmethod
    def get_implementors(cls):
        return cls.implementors

    def shield(self, runnable: Any):
        try:
            fqcn = f"{runnable.__class__.__module__}.{runnable.__class__.__qualname__}"

            implementors = self.get_implementors()
            if fqcn in implementors:
                implementor = implementors[fqcn]
                return implementor(policy_store=self.policy_store).shield(runnable)
            #if 'llama_index.core.query_pipeline.query' in runnable.__class__.__module__ and 'QueryPipeline' in runnable.__class__.__qualname__:
            #    return LI_QueryPipeline(policy_store=self.policy_store).shield(runnable)
            else:
                return runnable
        except Exception as e:
            print(f"An error of type {type(e).__name__} occurred: {e}")
            raise e

    def _input_enforcer(self, prompt) -> (bool, str):
        results = rails.ParallelRails().trigger(rails=[rails.secure_input_general, rails.secure_input_proprietary_terms, rails.secure_input_disallowed_topics, rails.secure_input_content_security], prompt=prompt)

        for result in results:
            if result.decision == 'deny':
                print(f"Policy {result.policy_id} check failed, message = {result.message}")
                return True, result.message 

        return False, ""
        #print(rails.secure_input_general(prompt))
        #print(rails.secure_input_proprietary_terms(prompt))
        #print(rails.secure_input_disallowed_topics(prompt))
        #print(rails.secure_input_content_security(prompt))

    def _output_enforcer(self, prompt, answer,context=None) -> (bool, str):
        return True, "denied access."

    def server(self):
        # Run this class in server mode.
        pass


def implements(fqcn: str):
    def decorator(cls):
        Langsecure.implements(fqcn, cls)
        return cls

    return decorator
