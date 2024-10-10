from pydantic import BaseModel, HttpUrl, Field
from pathlib import Path
from typing import Union
from typing import Literal
from typing import Optional
from typing import Any
from typing import ClassVar
import inspect

from .decorators import implements

from . import store
from . import factory
from . import utils

class Langsecure(BaseModel):
    """Base class for langsecure implementation."""

    policy_store: Optional[Union[str, Path, HttpUrl]] = None
    tracking_server: Optional[Union[Path, HttpUrl]] = None
    rails_backend: Optional[Literal['nvidia-nemoguardrails']] = 'nvidia-nemoguardrails'
    langsecure_server: Optional[HttpUrl] = None

    def __init__(self, **params):
        super().__init__(**params)

        # hardcode rails backend to be nvidia nemoguardrails for now.
        self.rails_backend = 'nvidia-nemoguardrails'

        if self.langsecure_server != None:
            # no need of loading policies locally
            self._py_policystore = None
        else:
            # Load the policies into the pydantic class.
            self._py_policystore = store.PyPolicyStore(self.policy_store)


    def shield(self, runnable: Any):
        try:
            fqcn = f"{runnable.__class__.__module__}.{runnable.__class__.__qualname__}"
            implementor = factory.get(fqcn)
            if implementor != None:
                return implementor(**self.__dict__).shield(runnable)
            else:
                return runnable
        except Exception as e:
            print(f"An error of type {type(e).__name__} occurred: {e}")
            raise e

    def _input_enforcer(self, prompt) -> (bool, str):
        return self._enforcer(scope=['user_input'], prompt=prompt)

    def _output_enforcer(self, prompt, answer,context=None) -> (bool, str):
        return self._enforcer(scope=['context', 'bot_answer'], prompt=prompt, answer=answer, context=context)
        
    @utils.execute_remotely_if_needed
    def _enforcer(self, scope=['user_input'], prompt=None, answer=None, context=None) -> (bool, str):
        from . import rails
        parallel_rails = []
        for policy in self._py_policystore.policies:
            for filter in policy.filters:
                if all(item in filter.scope for item in scope) == False:
                    continue
                fn = factory.get(filter.id)
                #log if there is no implementor found for a filter
                if fn != None:
                    parallel_rails.append(fn)
                    #raise ValueError(f"No implementor found for filter {filter.id}")
        results = rails.ParallelRails().trigger(rails=parallel_rails, rules=filter.rules, prompt=prompt)

        for result in results:
            if result.decision == 'deny':
                print(f"Policy {result.policy_id} check failed, message = {result.message}")
                return True, result.message 

        return False, ""

        
    def server(self, app=None):
        if app != None:
            utils.apiroute(app, self._enforcer)
        else:
            from flask import Flask, request, jsonify
            app = Flask("langsecure")

            utils.apiroute(app, self._enforcer, instance=self)
            app.run(debug=True, host='0.0.0.0', port=8001)


def implements(fqcn: str):
    def decorator(cls):
        Langsecure.implements(fqcn, cls)
        return cls
    return decorator
