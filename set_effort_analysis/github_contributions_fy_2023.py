# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # DBMI SET GitHub Contributions - Fiscal Year 2023
#
# Note: please set environment variables SET_EFFORT_GH_USER with your GitHub username and SET_EFFORT_GH_TOKEN with your GitHub token in order to use this notebook.

# %%
import json
import os
from datetime import datetime
from typing import Optional

import requests
from github import Auth, Github

# %%
# set github authorization and client
g = Github(auth=Auth.Token(os.environ.get("SET_EFFORT_GH_TOKEN")), per_page=100)

date_start = datetime.strptime("2022-07-01", "%Y-%m-%d")
date_end = datetime.strptime("2023-06-30", "%Y-%m-%d")

# specify set members as github usernames
set_members = ["vincerubinetti", "falquaddoomi", "d33bs"]

# Define github organization names
orgs = [
    "cu-dbmi",
    "cytomining",
    "wayscience",
    "JRaviLab",
    "krishnanlab",
    "greenelab",
    "manubot",
    "CCPM-TIS",
    "monarch-initiative",
    "blekhmanlab",
    "tis-lab",
    "hetio",
    "biothings",
]


# %%
def within_time_range(
    date_to_check: Optional[datetime],
    date_start: datetime = date_start,
    date_end: datetime = date_end,
) -> bool:
    """
    Checks whether given date falls within range of date_start and date_end
    """

    # if date_to_check is None, return false
    if not date_to_check:
        return False

    return date_start <= date_to_check <= date_end


# %%
# gather organization repos
org_repos = [
    repo for org_name in orgs for repo in g.get_organization(org_name).get_repos()
]

print(len(org_repos))

# %%
# Initialize counters
repo_contribution_count = 0
total_open_prs = 0
total_closed_prs = 0
total_reviewed_prs = 0
total_open_issues = 0
total_closed_issues = 0

touched_repos = []

# Loop over the repositories and increment counters
for repo in org_repos:
    # pull request block
    # Loop over list of pulls in the repository
    for pull in repo.get_pulls(state="all"):
        if (
            within_time_range(date_to_check=pull.created_at)
            or within_time_range(date_to_check=pull.closed_at)
            or within_time_range(date_to_check=pull.updated_at)
        ):
            # for pull requests authored by set members
            if pull.user.login in set_members:
                if pull.state == "open":
                    total_open_prs += 1
                elif pull.state == "closed":
                    total_closed_prs += 1
                if repo.full_name not in touched_repos:
                    touched_repos.append(repo.full_name)

            # pull request review block
            for review in pull.get_reviews():
                if (
                    # if the reviewer is one of the set members
                    review.user.login in set_members
                    # if the reviewer is not the issue author
                    # (don't count comments on PR submitted by same set member)
                    and pull.user.login != review.user.login
                    and within_time_range(date_to_check=review.submitted_at)
                ):
                    total_reviewed_prs += 1
                    if repo.full_name not in touched_repos:
                        touched_repos.append(repo.full_name)

    # Loop over list of issues in the repository
    for issue in repo.get_issues():
        if (
            within_time_range(date_to_check=issue.created_at)
            or within_time_range(date_to_check=issue.closed_at)
            or within_time_range(date_to_check=issue.updated_at)
        ):
            # non pull-request issue block
            if issue.user.login in set_members:
                if issue.state == "open":
                    total_open_issues += 1
                elif issue["state"] == "closed":
                    total_closed_issues += 1

                if repo.full_name not in touched_repos:
                    touched_repos.append(repo.full_name)

# %%
# Print the numbers
print(f"Repo opened issues: {total_open_issues}")
print(f"Repo closed issues: {total_closed_issues}")
print(f"Repo opened pull requests: {total_open_prs}")
print(f"Repo closed pull requests: {total_closed_prs}", end="\n\n")

print(f"Repos contributed to count: {len(touched_repos)}")
print(f"Total number of issues authored: {total_open_issues + total_closed_issues}")
print(f"Total pull requests: {total_open_prs + total_closed_prs}")
print(f"Total pull request reviews: {total_reviewed_prs}")
