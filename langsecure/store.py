from .types import PyPolicy, PyFilter, PySubjects

from pathlib import Path
from pydantic import HttpUrl
from pydantic import BaseModel
from typing import List
from typing import Union

import importlib.util
import os
import json
import yaml

class PyPolicyStore(BaseModel):
    
    policies: List[PyPolicy] = []  
    policy_store: Union[str, Path, HttpUrl] = None
    
    def __init__(self, policy_store=None):
        super().__init__(policy_store=policy_store)

        if self.policy_store == None or self.policy_store == "default":
            #load from the package
            self._load_frompkg("langsecure")

        elif isinstance(self.policy_store, Path):
            #load from the given directory
            self._load_fromdir(self.policy_store)

        elif isinstance(self.policy_store, HttpUrl):
            #load from the given URL
            # URLs can be git or any cloud bucket URLs
            raise NotImplementedError("support for loading policies from a remote store is not implemented.")

    def _load_frompkg(self, package):
        package_spec = importlib.util.find_spec(package)
        pkgdir = os.path.dirname(package_spec.origin)

        self._load_fromdir(os.path.join(pkgdir, "policy_store"))


    def _load_fromdir(self, directory):
        policydocs = []

        #load all json / yaml files from this directory
        for file in os.listdir(directory):
            if file.endswith('.yaml') or file.endswith('.yml'):
                with open(os.path.join(directory, file), 'r') as f:
                    policydocs.append(yaml.safe_load(f))
            elif file.endswith('.json'):
                with open(os.path.join(directory, file), 'r') as f:
                    policydocs.append(json.load(f))

        self.policies = self._load_pydantic(policydocs)


    def _load_pydantic(self, policydocs):
        pypolicies = []
        #prune if there are any non compliant files
        for pdoc in policydocs:
            policies = pdoc.get("policies", [])
            for policy in policies:
                pypolicy = PyPolicy(id=policy['id'], description=policy.get('description', ''))

                filters = policy.get("filters", [])
                for filter in filters:
                    pyfilter = PyFilter(**filter)
                    pypolicy.add_filter(pyfilter)
                subjects = policy.get("subjects", {})
                pypolicy.add_subjects(**subjects)

                pypolicies.append(pypolicy)

        return pypolicies
        
            
