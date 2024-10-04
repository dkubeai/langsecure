![Langsecure](images/title.png)

> **LATEST RELEASE / DEVELOPMENT VERSION**: The [main](https://github.com/dkubeai/langsecure/tree/main) branch tracks the latest version: [0.1](https://github.com/dkubeai/langsecure/tree/v0.9.1.1). For the latest development version, checkout the [dev](https://github.com/dkubeai/langsecure/tree/dev) branch.

> **DISCLAIMER**: The project is currently under active development. During this time, you may encounter breaking changes in the API or implementation that could lead to unexpected behavior. We do not currently recommend using this project in production until the stable release is available.

We are working diligently toward releasing a stable version as soon as possible. Your feedback and contributions are greatly valued as we build a reliable LLM execution toolkit. Please note that the examples provided in the documentation are intended for educational purposes and initial exploration, not for production use.

## Overview

### Secure Your GenAI Workflows with Langsecure

Users build their GenAI applications and workflows using popular open-source libraries like **LlamaIndex**, **LangChain**, and **Autogen**. These applications often access sensitive enterprise data, user information, and secrets, necessitating robust security guardrails.

### Key Challenges

#### Developer Focus
Developers frequently lack the domain-specific security expertise or bandwidth to implement comprehensive security measures, resulting in critical vulnerabilities.

#### Contextual Security
Traditional security solutions often miss the mark on implementing fine-grained, role-based, and context-aware access controls required in enterprise environments.

#### Diverse Security Policies
Security requirements vary widely across enterprises, applications, and user roles, necessitating adaptable security measures. Additionally, LLM responses must often be dynamically tailored based on specific policies, further complicating the security landscape.

### Langsecure Solution

Langsecure introduces a policy-based security overlay that integrates with workflows like **Retrieval-Augmented Generation (RAG)**, data ingestion, and fine-tuning, all managed through configuration files. This allows for easy customization and enforcement of security policies, ensuring applications remain secure and portable across various environments.

#### Features

- **Protect Access to Indexes**
  - Policies to allow access at the index level or even at the document level.
  - Record access of users to index records.
  - Track the lineage of which user fetched which records in the context of which query.

- **Role-Based Access Control (RBAC)**
  - Control who can delete/update the indices or records in them.
  - Define policies for which user/application/agent can access which index.

- **LLM Key Vault**
  - Guard Personally Identifiable Information (PII) & personal data.
  - Implement usage limits or fallback mechanisms in case of overutilization.
  - Record all access to the LLM.
  - Control which data can be used for fine-tuning an LLM.

Langsecure provides the necessary tools to safeguard your GenAI workflows, addressing the critical security challenges faced by developers and enterprises alike. By implementing robust, policy-based security measures, Langsecure ensures that your GenAI applications remain secure, compliant, and efficient.

## How to setup for development

### 1. Create a Conda Environment

To start, create and activate a new Conda environment:

```bash
conda create -n lgrenv python=3.10.14 -y
conda activate lgrenv
```

### 2. Install Core Langsecure Dependencies

Navigate to the langsecure directory and install the core dependencies:

```bash
pip install .
```

## Examples

please see `examples/llama_index/`
