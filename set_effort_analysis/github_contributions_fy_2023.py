#!/usr/bin/env python
# coding: utf-8

# # DBMI SET GitHub Contributions - Fiscal Year 2023
# 
# Note: please set environment variables SET_EFFORT_GH_USER with your GitHub username and SET_EFFORT_GH_TOKEN with your GitHub token in order to use this notebook.

# In[1]:


import json
import os
from datetime import datetime

import requests


# In[2]:


# Provide your GitHub username and personal access token for authentication
username = os.environ.get("SET_EFFORT_GH_USER")
token = os.environ.get("SET_EFFORT_GH_TOKEN")

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

# Create a re-usable session object with the user creds in-built
gh_session = requests.Session()
gh_session.auth = (username, token)


# In[3]:


def within_time_range(
    date_to_check: datetime,
    date_start: datetime = date_start,
    date_end: datetime = date_end,
) -> bool:
    """
    Checks whether given date falls within range of date_start and date_end
    """

    return date_start <= date_to_check <= date_end


# In[4]:


org_repos = []

for org in orgs:
    # fetch the list of repositories in the organizations, appending each
    org_repos += json.loads(
        gh_session.get(f"https://api.github.com/orgs/{org}/repos").text
    )


# In[5]:


# set parameters for gathering data
params = {
    # get issues with all states
    "state": "all",
    # get only the first page of 400 results
    "page": "1",
    "per_page": 400,
    # sort order as update datetime descending (most recent first)
    "sort": "updated",
    "direction": "desc",
}
# use GitHub API v3
headers = {"Accept": "application/vnd.github.v3+json"}


# In[ ]:


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
    # Fetch the list of issues (including PRs) in the repository
    issues = json.loads(
        gh_session.get(
            f"https://api.github.com/repos/{repo['full_name']}/issues",
            headers=headers,
            params=params,
        ).text
    )

    # Loop over the issues and count the open and closed PRs
    for issue in issues:
        if within_time_range(
            date_to_check=datetime.strptime(issue["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
        ):
            # pull request block
            if "pull_request" in issue:
                # for pull requests authored by set members
                if issue["user"]["login"] in set_members:
                    if issue["state"] == "open":
                        total_open_prs += 1
                    elif issue["state"] == "closed":
                        total_closed_prs += 1
                    if repo["full_name"] not in touched_repos:
                        touched_repos.append(repo["full_name"])

                # pull request review block
                for review in json.loads(
                    gh_session.get(
                        f"{issue['pull_request']['url']}/reviews",
                        headers=headers,
                        params=params,
                    ).text
                ):
                    if (
                        # if the reviewer is one of the set members
                        review["user"]["login"] in set_members
                        # if the reviewer is not the issue author
                        # (don't count comments on PR submitted by same set member)
                        and issue["user"]["login"] != review["user"]["login"]
                        and within_time_range(
                            date_to_check=datetime.strptime(
                                review["submitted_at"], "%Y-%m-%dT%H:%M:%SZ"
                            )
                        )
                    ):
                        total_reviewed_prs += 1
                        if repo["full_name"] not in touched_repos:
                            touched_repos.append(repo["full_name"])

            # non pull-request issue block
            elif issue["user"]["login"] in set_members:
                if issue["state"] == "open":
                    total_open_issues += 1
                elif issue["state"] == "closed":
                    total_closed_issues += 1

                if repo["full_name"] not in touched_repos:
                    touched_repos.append(repo["full_name"])


# Print the totals
print(f"Repos contributed to count: {len(touched_repos)}")
print(f"Repo opened issues: {total_open_issues}")
print(f"Repo closed issues: {total_closed_issues}")
print(f"Repo opened pull requests: {total_open_prs}")
print(f"Repo closed pull requests: {total_closed_prs}")
print(f"Repo pull request reviews: {total_reviewed_prs}")

