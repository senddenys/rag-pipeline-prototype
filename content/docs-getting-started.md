# Getting Started with the Platform

This guide explains how to get started with our platform. The platform supports **Python 3.10 and above** and **Node.js 18 LTS**. You can install the CLI via pip or npm.

## Installation

- **Python**: `pip install platform-cli`
- **Node**: `npm install -g @company/platform-cli`

After installation, run `platform --version` to verify. The first run will prompt you to log in. Use your company email and SSO.

## Key Concepts

- **Projects**: Each project has a unique ID and contains datasets and pipelines.
- **Datasets**: Structured data (CSV, Parquet) that you upload or sync from a source.
- **Pipelines**: Directed graphs of steps (ingest → transform → export). Steps can be scripts (Python or Node) or built-in connectors.

## Quick Start

1. Create a project: `platform project create --name "My Project"`.
2. Upload a dataset: `platform dataset upload --project <id> --path ./data.csv`.
3. Run a pipeline: `platform pipeline run --project <id> --pipeline <pipeline-id>`.

For more details, see the API reference and the tutorials in the docs.
