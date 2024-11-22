"""Arg pack components."""

from typing import Any, Callable, Dict, Optional

from llama_index.core.base.query_pipeline.query import (
    InputKeys,
    OutputKeys,
    QueryComponent,
)
from llama_index.core.bridge.pydantic import Field


class StopComponent(QueryComponent):
    """Stop  component.

    When encountered in a pipeline, the execution stops post this component.

    """

    message: str = "Pipeline execution terminated."

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        raise NotImplementedError

    def validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs."""
        return input

    def _validate_component_outputs(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component outputs."""
        # make sure output value is a list
        if not isinstance(output["output"], str):
            raise ValueError(f"Output is not a string.")
        return output

    def set_callback_manager(self, callback_manager: Any) -> None:
        """Set callback manager."""

    def _run_component(self, **kwargs: Any) -> Any:
        """Run component."""
        msg = kwargs['message']
        return {"output": msg}

    async def _arun_component(self, **kwargs: Any) -> Any:
        """Run component (async)."""
        return self._run_component(**kwargs)

    @property
    def input_keys(self) -> InputKeys:
        """Input keys."""
        return InputKeys.from_keys({"message"})

    @property
    def output_keys(self) -> OutputKeys:
        """Output keys."""
        return OutputKeys.from_keys({"output"})


import inspect
from langsecure.factory import implements
from langsecure import Langsecure

@implements('llama_index.core.query_pipeline.query.QueryPipeline')
class LI_QueryPipeline(Langsecure):
    def shield(self, runnable: Any) -> Any:
        self._parent = runnable
        self._parent_callables = {name: func for name, func in inspect.getmembers(runnable, predicate=inspect.ismethod)}


        self._parent.__class__.get_next_module_keys = self._get_next_module_keys
        return self._parent


    def _get_next_module_keys(self, run_state):
        parent_callable = self._parent_callables["get_next_module_keys"]

        if 'stop_component' in run_state.executed_modules:
            #stop the pipeline execution here
            return []

        next_stages = parent_callable(run_state)
        for stage in next_stages:
            if stage == "input":
                for module_key, module_input in run_state.all_module_inputs.items():
                    if module_key == stage:
                        for value in module_input.values():
                            deny, deny_message = self._input_enforcer(value)
                            if deny == True:
                                stop_component = StopComponent(message=deny_message)
                                #Execute a stop stage and return back to the caller
                                run_state.all_module_inputs['stop_component'] = {"message": deny_message}
                                if "stop_component" not in run_state.module_dict.keys():
                                    self._parent.add("stop_component", stop_component)
                                return ["stop_component"]
            if stage == "stop_component":
                #post stop component, just return empty list
                return []
        return next_stages
