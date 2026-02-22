import requests
import os
import time
from typing import List, Optional
from fastapi import HTTPException
from app.schemas import Project, GitHubProfile

GITHUB_API_BASE = "https://api.github.com"
TIMEOUT = 10  # 10 seconds timeout
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds between retries

def get_github_headers():
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def make_request_with_retry(url: str, retries: int = MAX_RETRIES):
    """Make HTTP request with retry logic"""
    for attempt in range(retries):
        try:
            response = requests.get(
                url, 
                headers=get_github_headers(), 
                timeout=TIMEOUT
            )
            return response
        except requests.exceptions.ConnectionError as e:
            if attempt < retries - 1:
                print(f"Connection error, retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(RETRY_DELAY)
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Cannot connect to GitHub after {retries} attempts. Please check your internet connection."
                )
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                print(f"Timeout, retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(RETRY_DELAY)
            else:
                raise HTTPException(
                    status_code=504,
                    detail="GitHub API timeout. Please try again later."
                )

def check_rate_limit(response: requests.Response):
    """Check rate limit headers and raise appropriate exception"""
    remaining = response.headers.get('X-RateLimit-Remaining')
    reset_time = response.headers.get('X-RateLimit-Reset')
    
    if remaining == '0':
        if reset_time:
            reset_timestamp = int(reset_time)
            reset_in_minutes = (reset_timestamp - time.time()) / 60
            raise HTTPException(
                status_code=429,
                detail=f"GitHub API rate limit exceeded. Try again in {reset_in_minutes:.1f} minutes."
            )
        else:
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Please try again later."
            )

def fetch_repositories(username: str, limit: int = 5) -> List[dict]:
    url = f"{GITHUB_API_BASE}/users/{username}/repos"
    
    try:
        # Use the retry mechanism
        response = make_request_with_retry(url)
        
        # Handle 404 (user not found)
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub user '{username}' not found"
            )
        
        # Handle rate limiting
        if response.status_code == 403:
            check_rate_limit(response)
        
        response.raise_for_status()
        repos = response.json()
        
        if not repos:
            return []

        # Sort by most recently updated
        repos.sort(key=lambda r: r["updated_at"], reverse=True)

        return repos[:limit]
        
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error fetching GitHub data: {str(e)}"
        )

def fetch_languages(languages_url: str) -> List[str]:
    try:
        response = make_request_with_retry(languages_url)
        response.raise_for_status()
        return list(response.json().keys())
    except:
        # Return empty list if languages can't be fetched
        return []

def repo_to_project(repo: dict) -> Project:
    languages = fetch_languages(repo["languages_url"])

    description = repo["description"] or "No description provided."

    return Project(
        name=repo["name"],
        description=description,
        technologies=languages
    )

def get_github_profile(username: str) -> GitHubProfile:
    """
    Fetch GitHub profile and repositories for a given username.
    Returns a GitHubProfile object with projects.
    """
    if not username or username.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="GitHub username cannot be empty"
        )
    
    repos = fetch_repositories(username)

    projects = [repo_to_project(repo) for repo in repos]

    return GitHubProfile(
        username=username,
        projects=projects
    )