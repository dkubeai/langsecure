from .types import PyPolicy, PyFilter, PySubjects

from pathlib import Path
from pydantic import BaseModel
from typing import List, Union, Any

import importlib.util
import os
import json
import yaml
import tempfile
import shutil
import subprocess
from urllib.parse import urlparse

class PyPolicyStore(BaseModel):
    policies: List[PyPolicy] = []
    policy_store: Union[str, Path, Any] = None

    def __init__(self, policy_store=None):
        super().__init__(policy_store=policy_store)

        if self.policy_store is None or self.policy_store == "default":
            # Load from the package
            self._load_frompkg("langsecure")

        elif isinstance(self.policy_store, Path):
            # Load from the given directory
            self._load_fromdir(self.policy_store)

        elif isinstance(self.policy_store, str) and self._is_url(self.policy_store):
            # Load from the given URL
            url = self.policy_store
            if self._is_git_url(url):
                self._load_fromgit(url)
            else:
                # For cloud bucket URLs, raise NotImplementedError for now
                raise NotImplementedError("Support for loading policies from cloud bucket URLs is not implemented.")

        else:
            raise ValueError(f"Unsupported policy store type: {self.policy_store}")

    def _is_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _is_git_url(self, url: str) -> bool:
        return url.endswith('.git') or 'git@' in url

    def _load_frompkg(self, package):
        package_spec = importlib.util.find_spec(package)
        if package_spec is None or package_spec.origin is None:
            raise ImportError(f"Cannot find package '{package}'")
        pkgdir = os.path.dirname(package_spec.origin)

        self._load_fromdir(os.path.join(pkgdir, "policy_store"))

    def _load_fromdir(self, directory):
        policydocs = []

        # Check if the directory exists
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Policy directory '{directory}' does not exist")

        # Load all JSON/YAML files from this directory
        for file in os.listdir(directory):
            filepath = os.path.join(directory, file)
            if os.path.isfile(filepath):
                if file.endswith('.yaml') or file.endswith('.yml'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        doc = yaml.safe_load(f)
                        if doc:
                            policydocs.append(doc)
                elif file.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                        if doc:
                            policydocs.append(doc)

        self.policies = self._load_pydantic(policydocs)

    def _load_pydantic(self, policydocs):
        pypolicies = []
        # Prune if there are any non-compliant files
        for pdoc in policydocs:
            if not pdoc:
                continue
            policies = pdoc.get("policies", [])
            for policy in policies:
                try:
                    pypolicy = PyPolicy(id=policy['id'], description=policy.get('description', ''))

                    filters = policy.get("filters", [])
                    for filter_dict in filters:
                        pyfilter = PyFilter(**filter_dict)
                        pypolicy.add_filter(pyfilter)
                    subjects = policy.get("subjects", {})
                    pypolicy.add_subjects(**subjects)

                    pypolicies.append(pypolicy)
                except Exception as e:
                    # Log or print the error, skip the invalid policy
                    print(f"Skipping invalid policy due to error: {e}")
                    continue

        return pypolicies

    def _load_fromgit(self, git_url: str):
        """
        Clones a Git repository and loads policies from it.
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # Clone the Git repository into the temporary directory
            subprocess.check_call(['git', 'clone', '--depth', '1', git_url, temp_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Load policies from the 'policy_store' directory within the cloned repository
            policy_dir = os.path.join(temp_dir, 'policy_store')
            self._load_fromdir(policy_dir)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone Git repository '{git_url}'. Ensure that the URL is correct and accessible.") from e
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

