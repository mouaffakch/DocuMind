import re
from typing import Tuple, Optional, Dict, Any, List
import httpx
from app.core.exceptions import EntityNotFoundError, DocuMindException
from app.schemas.project import GitHubRepoInfoResponse


class GitHubService:
    """Service interacting with the official GitHub REST API (v3)."""

    GITHUB_API_BASE = "https://api.github.com"

    @staticmethod
    def parse_repo_url(url_or_shorthand: str) -> Tuple[str, str]:
        """
        Parse GitHub URL or shorthand into (owner, repo).
        Supports:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        - owner/repo
        """
        cleaned = url_or_shorthand.strip()
        
        # Shorthand: owner/repo
        shorthand_match = re.match(r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$", cleaned)
        if shorthand_match:
            return shorthand_match.group(1), shorthand_match.group(2).removesuffix(".git")

        # Standard HTTPS or SSH URLs
        https_pattern = r"^https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git|/)?$"
        ssh_pattern = r"^git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?$"

        m = re.match(https_pattern, cleaned) or re.match(ssh_pattern, cleaned)
        if m:
            return m.group(1), m.group(2)

        raise DocuMindException(f"Format d'URL de dépôt GitHub invalide: '{url_or_shorthand}'")

    @classmethod
    async def get_repo_metadata(
        cls, 
        owner: str, 
        repo: str, 
        pat: Optional[str] = None
    ) -> GitHubRepoInfoResponse:
        """Fetch repository details from GitHub REST API."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DocuMind-App",
        }
        if pat:
            headers["Authorization"] = f"token {pat}"

        url = f"{cls.GITHUB_API_BASE}/repos/{owner}/{repo}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.RequestError as exc:
                raise DocuMindException(f"Erreur réseau lors de la communication avec GitHub: {str(exc)}")

            if response.status_code == 404:
                raise EntityNotFoundError(f"Le dépôt GitHub '{owner}/{repo}' n'a pas été trouvé (ou est privé et nécessite un token valide).")
            elif response.status_code == 401:
                raise DocuMindException("Token GitHub invalide ou expiré.")
            elif response.status_code == 403:
                raise DocuMindException("Limite de taux d'appels à l'API GitHub atteinte. Veuillez configurer un Personal Access Token.")
            elif response.status_code != 200:
                raise DocuMindException(f"GitHub API a retourné une erreur {response.status_code}: {response.text}")

            data = response.json()

            # Retrieve repository languages
            languages = []
            try:
                lang_res = await client.get(f"{cls.GITHUB_API_BASE}/repos/{owner}/{repo}/languages", headers=headers)
                if lang_res.status_code == 200:
                    languages = list(lang_res.json().keys())
            except Exception:
                pass

            return GitHubRepoInfoResponse(
                owner=data["owner"]["login"],
                repo_name=data["name"],
                full_name=data["full_name"],
                description=data.get("description"),
                default_branch=data.get("default_branch", "main"),
                stars_count=data.get("stargazers_count", 0),
                forks_count=data.get("forks_count", 0),
                open_issues_count=data.get("open_issues_count", 0),
                is_private=data.get("private", False),
                clone_url=data.get("clone_url", f"https://github.com/{owner}/{repo}.git"),
                languages=languages,
            )

    @classmethod
    async def get_latest_commit_sha(
        cls, 
        owner: str, 
        repo: str, 
        branch: str = "main", 
        pat: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve the latest commit SHA for a specific branch."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DocuMind-App",
        }
        if pat:
            headers["Authorization"] = f"token {pat}"

        url = f"{cls.GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{branch}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("sha")
            return None
