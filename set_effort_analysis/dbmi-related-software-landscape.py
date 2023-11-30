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
from typing import Dict, Optional, Union

import awkward as ak
import duckdb
import github
import numpy as np
import pandas as pd
import plotly.colors as pc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pytz
import requests
from box import Box
from github import Auth, Github, Repository

# set predefined path for data
data_dir = "../data"

# set github authorization and client
github_client = Github(
    auth=Auth.Token(os.environ.get("LANDSCAPE_ANALYSIS_GH_TOKEN")), per_page=100
)

# set plotly default theme
pio.templates.default = "simple_white"

# define a color sequence to use
color_seq = pc.qualitative.Dark2

# %%
# gather org data
org_names = Box.from_yaml(
    filename=f"{data_dir}/software-landscape/github-orgs.yaml"
).organizations

# show how many orgs we need to gather data from
len(org_names)


# %%
def get_github_org_or_user(
    name: str,
) -> Union[github.NamedUser.NamedUser, github.Organization.Organization]:
    """
    Convenience function to gather pygithub orgs or users similarly
    using only a name as a reference point to simplify data gathering.
    """

    try:
        # attempt to find github org
        return github_client.get_organization(name)
    except github.UnknownObjectException:
        # if we failed to find the org, try as a user instead
        return github_client.get_user(name)


def safe_get_readme(repo: github.Repository.Repository) -> Optional[str]:
    """
    Safely retrieve GitHub repo readme data as a string,
    returning a None where no readme is found.
    """

    try:
        repo.get_readme().content
    except github.UnknownObjectException:
        return None


def safe_detect_license(repo: github.Repository.Repository) -> Optional[str]:
    """
    Safely retrieve detect the license type ID,
    returning a None where no readme is found
    """

    try:
        return repo.get_license().license.spdx_id
    except:
        return None


def get_github_repo_sbom(full_name: str) -> Optional[Dict[str, str]]:
    """
    Gathers GitHub Software Bill of Materials (SBOM) data
    given a full_name (org/repo_name).

    See here for more information:
    https://docs.github.com/en/rest/dependency-graph/sboms
    """

    try:
        response = requests.get(
            f"https://api.github.com/repos/{full_name}/dependency-graph/sbom",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {os.environ.get('LANDSCAPE_ANALYSIS_GH_TOKEN')}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
        response.raise_for_status()  # Raise an exception for HTTP errors

        # return the result json
        return response.json()

    except requests.exceptions.RequestException as err:
        print("Experienced SBOM error: ", err)
        return None


# %%
# gather targeted data from GitHub
github_metrics = [
    {
        "GitHub Org Name": org_name,
        "Repo Name": repo.name,
        "GitHub Repo Full Name": repo.full_name,
        "GitHub Repository ID": repo.id,
        "Repository Size (KB)": repo.size,
        "GitHub Repo Archived": repo.archived,
        "GitHub Repo Created Month": repo.created_at.strftime("%Y-%m-%d"),
        "GitHub Stars": repo.stargazers_count,
        "GitHub Network Count": repo.network_count,
        "GitHub Forks": repo.forks_count,
        "GitHub Subscribers": repo.subscribers_count,
        "GitHub Open Issues": repo.get_issues(state="open").totalCount,
        "GitHub Contributors": repo.get_contributors().totalCount,
        "GitHub License Type": safe_detect_license(repo),
        "GitHub Topics": repo.topics,
        "GitHub Description": repo.description,
        "GitHub Readme": safe_get_readme(repo),
        "GitHub Detected Languages": repo.get_languages(),
        "GitHub Repo SBOM": get_github_repo_sbom(repo.full_name),
    }
    # make a request for github org data with pygithub
    for org_name, repo in [
        (
            org_name,
            repo,
        )
        for org_name in org_names
        for repo in get_github_org_or_user(org_name).get_repos()
    ]
]
ak.Array(github_metrics)

# %%
# gather sbom data from GitHub
github_metrics = [
    dict({})
    # make a request for github org data with pygithub
    for existing_data, repo in [
        (existing_data, github_client.get_repo(repo["GitHub Repo Full Name"]))
        for existing_data in github_metrics
    ]
]
ak.Array(github_metrics)

# %%
df_github_metrics = pd.DataFrame(github_metrics)
df_github_metrics.info()


# %%
# Function to find the top language for each row
def find_top_language(languages):
    if isinstance(languages, dict):
        non_empty_languages = {
            key: value for key, value in languages.items() if value is not None
        }
        if non_empty_languages:
            return max(non_empty_languages, key=non_empty_languages.get)
    return None


# gather the number of lines of code
df_github_metrics["Total lines of GitHub detected code"] = (
    df_github_metrics["GitHub Detected Languages"]
    .dropna()
    .apply(lambda x: sum(value if value is not None else 0 for value in x.values()))
)

# Apply the function to the "GitHub Detected Languages" column and create a new column "Primary programming language"
df_github_metrics["Primary language"] = df_github_metrics[
    "GitHub Detected Languages"
].apply(find_top_language)
df_github_metrics.info()

# %%
# prep for creating an hbar chart for primary languages
grouped_data = (
    df_github_metrics.groupby(["Primary language"]).size().reset_index(name="Count")
)

# Group by "Primary programming language" and calculate the sum of counts for each programming language
programming_language_counts = (
    grouped_data.groupby("Primary language")["Count"].sum().reset_index()
)

# Sort programming languages by the sum of counts in descending order
programming_language_counts = programming_language_counts.sort_values(
    by="Count", ascending=False
)
programming_language_counts

# %%
# Create a horizontal bar chart for primary language counts
fig_languages = px.bar(
    data_frame=grouped_data.sort_values(by="Count"),
    title=f"Repository Primary Language Count",
    y="Primary language",
    x="Count",
    color_discrete_sequence=[color_seq[0]],
    text="Count",
    orientation="h",
    width=1200,
    height=700,
)

# Customize layout to display count labels properly
fig_languages.update_traces(
    texttemplate="%{text}",
    textposition="inside",
)
fig_languages.update_layout(
    # ensure all y axis labels appear
    yaxis=dict(
        tickmode="array",
        tickvals=programming_language_counts["Primary language"].tolist(),
        ticktext=programming_language_counts["Primary language"].tolist(),
    ),
)

fig_languages.write_image("images/software-landscape-primary-language-counts.png")
fig_languages.show()

# %%
# gather total lines of code for all repos by language
total_language_line_counts = [
    {
        "language": language,
        "line_count": ak.sum(
            ak.Array(github_metrics)["GitHub Detected Languages"][language]
        ),
    }
    for language in ak.Array(github_metrics)["GitHub Detected Languages"].fields
]

df_total_language_line_counts = pd.DataFrame.from_records(
    total_language_line_counts
).sort_values(by="line_count")

df_total_language_line_counts

# %%
# Create a horizontal bar chart for language line count totals
fig_languages = px.bar(
    data_frame=df_total_language_line_counts.sort_values(by="line_count"),
    title=f"Repository Language Line Counts Total",
    y="language",
    x="line_count",
    color_discrete_sequence=[color_seq[2]],
    text="line_count",
    orientation="h",
    width=1200,
    height=1200,
)

# Customize layout to display count labels properly
fig_languages.update_traces(
    texttemplate="%{text}",
    textposition="inside",
)
fig_languages.update_layout(
    xaxis_title="Lines of Code (Total)",
    yaxis_title="Language",
    # ensure all y axis labels appear
    yaxis=dict(
        tickmode="array",
        tickvals=df_total_language_line_counts["language"].tolist(),
        ticktext=df_total_language_line_counts["language"].tolist(),
    ),
)

fig_languages.write_image("images/software-landscape-language-line-counts-total.png")
fig_languages.show()

# %%
df_total_language_line_counts["line_count_log"] = np.log(
    df_total_language_line_counts["line_count"]
)

# Create a horizontal bar chart for language line count totals
fig_languages = px.bar(
    data_frame=df_total_language_line_counts.sort_values(by="line_count_log"),
    title=f"Repository Language Line Counts Total",
    y="language",
    x="line_count_log",
    color_discrete_sequence=[color_seq[2]],
    text="line_count_log",
    orientation="h",
    width=1200,
    height=1200,
)

# Customize layout to display count labels properly
fig_languages.update_traces(
    texttemplate="%{text}",
    textposition="inside",
)
fig_languages.update_layout(
    xaxis_title="Lines of Code (Total)(log)",
    yaxis_title="Language",
    # ensure all y axis labels appear
    yaxis=dict(
        tickmode="array",
        tickvals=df_total_language_line_counts["language"].tolist(),
        ticktext=df_total_language_line_counts["language"].tolist(),
    ),
)

fig_languages.write_image(
    "images/software-landscape-language-line-counts-total-log.png"
)
fig_languages.show()

# %%
