from pydantic import BaseModel, HttpUrl
from pathlib import Path
from typing import Union
from typing import Literal
from typing import Optional
from typing import Any
import os
import mlflow

from . import rails
from . import store
from . import factory
from . import utils
from . import trace


class Langsecure(BaseModel):
    """Base class for langsecure implementation."""

    policy_store: Optional[Union[str, Path, HttpUrl]] = None
    tracking_server: Optional[Union[Path, HttpUrl]] = Path("~/.langsecure/trace.log").expanduser()
    rails_backend: Optional[Literal['nvidia-nemoguardrails']] = 'nvidia-nemoguardrails'
    langsecure_server: Optional[HttpUrl] = None
    llm_engine: Optional[str] = "openai"
    llm_model: Optional[str] = "gpt-3.5-turbo-instruct"
    use_mlflow: bool = False
    mlflow_tracking_uri: Optional[HttpUrl] = None
    custom_logging_func: Optional[Any] = None  # Optional user-defined logging function

    def __init__(self, **params):
        super().__init__(**params)
        os.makedirs(os.path.expanduser("~/.langsecure"), exist_ok=True)
        
        # Hardcode rails backend to be nvidia nemoguardrails for now.
        self.rails_backend = 'nvidia-nemoguardrails'

        if self.langsecure_server is not None:
            self._py_policystore = None
        else:
            self._py_policystore = store.PyPolicyStore(self.policy_store)

        self._trace = trace.LangsecureTracer(self.tracking_server).trace(name="langsecure")
        self._initialize_mlflow()  # Initialize MLflow lazily, only if used

    def _initialize_mlflow(self):
        """Lazy initialization of MLflow if `use_mlflow` is set to True."""
        if self.use_mlflow:
            try:
                global mlflow
                import mlflow
                # Set tracking URI to a default if not provided
                mlflow.set_tracking_uri(str(self.mlflow_tracking_uri) if self.mlflow_tracking_uri else "file:./mlruns")
                mlflow.set_experiment("Langsecure Experiment")
            except ImportError:
                print("MLflow is not installed. Please install it to use MLflow logging.")
                self.use_mlflow = False

    def shield(self, runnable: Any):
        try:
            fqcn = f"{runnable.__class__.__module__}.{runnable.__class__.__qualname__}"
            implementor = factory.get(fqcn)
            if implementor is not None:
                return implementor(**self.__dict__).shield(runnable)
            else:
                return runnable
        except Exception as e:
            print(f"An error of type {type(e).__name__} occurred: {e}")
            raise e

    def _input_enforcer(self, prompt) -> (bool, str):
        return self._enforcer(scope=['user_input'], prompt=prompt)

    def _output_enforcer(self, prompt, answer, context=None, extra_params: Dict[str, Any] = None) -> (bool, str):
        return self._enforcer(scope=['context', 'bot_answer'], prompt=prompt, answer=answer, context=context, extra_params=extra_params)
        
    @utils.execute_remotely_if_needed
    def _enforcer(self, scope=['user_input'], prompt=None, answer=None, context=None, extra_params: Dict[str, Any] = None) -> (bool, str):
        parallel_rails = []
        for policy in self._py_policystore.policies:
            for filter in policy.filters:
                if not all(item in filter.scope for item in scope):
                    continue
                fn = factory.get(filter.id)
                if fn is not None:
                    parallel_rails.append(fn)
        results = rails.ParallelRails().trigger(
            rails=parallel_rails, rules=filter.rules, prompt=prompt, 
            engine=self.llm_engine, trace=self._trace, model=self.llm_model
        )

        for result in results:
            if result.decision == 'deny':
                message = f"Policy {result.policy_id} check failed, message = {result.message}"
                print(message)

                # Call custom or default MLflow logging method
                if self.custom_logging_func:
                    self.custom_logging_func(result, scope, prompt, answer, context, extra_params)
                else:
                    self.log_to_mlflow(result, scope, prompt, answer, context, extra_params)

                return True, result.message

        return False, ""

    def log_to_mlflow(self, result, scope, prompt, answer, context, extra_params):
        """Logs data to MLflow, allowing for custom overrides in subclasses."""
        if self.use_mlflow:
            with mlflow.start_run(nested=True):
                mlflow.log_param("policy_id", result.policy_id)
                mlflow.log_param("decision", result.decision)
                mlflow.log_param("message", result.message)
                mlflow.log_param("scope", scope)
                mlflow.log_param("prompt", prompt)
                
                # Log optional parameters if they exist
                if answer:
                    mlflow.log_param("answer", answer)
                if context:
                    mlflow.log_param("context", context)
                if extra_params:
                    for key, value in extra_params.items():
                        mlflow.log_param(key, value)
    def server(self, app=None):
        if app is not None:
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
