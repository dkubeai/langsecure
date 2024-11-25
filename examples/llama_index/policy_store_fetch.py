import os
import requests
from pathlib import Path
from pydantic import HttpUrl

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.response_synthesizers import TreeSummarize
from llama_index.core.query_pipeline import InputComponent, QueryPipeline
from langsecure import Langsecure

# Define the GitHub URL for the policy file
policy_url = "https://raw.githubusercontent.com/dkubeai/langsecure/main/policy_store/policy.yaml"
policy_dir = Path("./policy_store")
policy_file = policy_dir / "policy.yaml"

# Ensure the policy directory exists
policy_dir.mkdir(exist_ok=True)

# Download the policy file if it doesn't already exist locally
if not policy_file.exists():
    print(f"Downloading policy file from {policy_url}...")
    response = requests.get(policy_url)
    response.raise_for_status()  # Raise an error if the request failed

    with open(policy_file, "wb") as f:
        f.write(response.content)
    print(f"Policy file downloaded to {policy_file}")
else:
    print(f"Using existing policy file at {policy_file}")

# Load documents for the pipeline
reader = SimpleDirectoryReader("../data")
docs = reader.load_data()
index = VectorStoreIndex.from_documents(docs)

# Set up components for the query pipeline
retriever = index.as_retriever(similarity_top_k=5)
summarizer = TreeSummarize()

# Initialize QueryPipeline and add components
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

# Use Langsecure with the downloaded policy directory
tracking_server = Path("./langsecure.log")
qp = Langsecure(policy_store=policy_dir, tracking_server=tracking_server).shield(qp)

# Run the pipeline
output = qp.run(input="How can I cook an apple pie?")
print(str(output))
