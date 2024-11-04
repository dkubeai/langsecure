from pathlib import Path
from langsecure import Langsecure
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
)
from llama_index.core.response_synthesizers import TreeSummarize
from llama_index.core.query_pipeline import InputComponent, QueryPipeline
import os
import mlflow

# Toggle flags for custom logging and extra parameters
use_custom_logging = False
use_extra_params = False

# Load documents for testing
reader = SimpleDirectoryReader("../data")
docs = reader.load_data()

# Initialize index
index = VectorStoreIndex.from_documents(docs)

# Set up components for the query pipeline
retriever = index.as_retriever(similarity_top_k=5)
summarizer = TreeSummarize()

# Build the query pipeline
qp = QueryPipeline(verbose=True)
qp.add_modules(
    {
        "input": InputComponent(),
        "retriever": retriever,
        "summarizer": summarizer,
    }
)
qp.add_link("input", "retriever")
qp.add_link("input", "summarizer", dest_key="query_str")
qp.add_link("retriever", "summarizer", dest_key="nodes")

# Define a custom logging function for MLflow
def custom_logging_func(result, scope, prompt, answer, context, extra_params):
    print("Using custom logging function for MLflow...")
    if langsecure_instance.use_mlflow:
        with mlflow.start_run(nested=True):
            mlflow.log_param("custom_policy_id", result.policy_id)
            mlflow.log_param("custom_decision", result.decision)
            mlflow.log_param("custom_message", result.message)
            mlflow.log_param("custom_scope", scope)
            mlflow.log_param("custom_prompt", prompt)
            # Log optional parameters if they exist
            if answer:
                mlflow.log_param("custom_answer", answer)
            if context:
                mlflow.log_param("custom_context", context)
            if extra_params:
                for key, value in extra_params.items():
                    mlflow.log_param(f"custom_{key}", value)

# Set extra parameters if enabled
extra_params = {
    "custom_metric": 0.98,
    "pipeline_stage": "test_stage",
    "execution_id": "test_run_001"
} if use_extra_params else None

# Initialize Langsecure with MLflow enabled, with optional custom logging
langsecure_instance = Langsecure(
    policy_store="default",
    tracking_server=Path("./langsecure.log"),
    use_mlflow=True,                       # Enable MLflow
    mlflow_tracking_uri="http://127.0.0.1:5000",
    custom_logging_func=custom_logging_func if use_custom_logging else None  # Enable custom logging if flag is True
)

# Apply the shield to the pipeline
qp = langsecure_instance.shield(qp)

# Run the query pipeline and test MLflow logging with or without extra_params
output = qp.run(input="How can I cook an apple pie?", extra_params=extra_params)
print("Pipeline output:", output)

# Conditional instruction message
if not use_custom_logging or not use_extra_params:
    print("\nTo enable custom logging and extra parameters, set `use_custom_logging` and `use_extra_params` to `True`.")
