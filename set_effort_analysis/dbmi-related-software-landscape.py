# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # DBMI Related Software Landscape Analysis
#
# This notebook explores the existing software landscape of DBMI or DBMI related software projects (including collaborations and general CU Anschutz ecosystem).
#
# ## Setup
#
# Set an environment variable named `LANDSCAPE_ANALYSIS_GH_TOKEN` to a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). E.g.: `export LANDSCAPE_ANALYSIS_GH_TOKEN=token_here`

# %%
import json
import os
import pathlib
import statistics
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Optional

import awkward as ak
import duckdb
import pandas as pd
import pytz
from box import Box
from github import Auth, Github, Repository

# set predefined path for data
data_dir = "../data"

# set github authorization and client
github_client = Github(
    auth=Auth.Token(os.environ.get("LANDSCAPE_ANALYSIS_GH_TOKEN")), per_page=100
)

# %%
# gather org data
org_names = Box.from_yaml(
    filename=f"{data_dir}/software-landscape/github-orgs.yaml"
).organizations

# show how many orgs we need to gather data from
len(org_names)

# %%
