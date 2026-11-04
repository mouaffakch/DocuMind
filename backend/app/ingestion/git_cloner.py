import os
import shutil
import tempfile
from typing import Optional
import git
from app.core.exceptions import IngestionError


class GitCloner:
    """Safely handles shallow cloning of GitHub repositories."""

    @staticmethod
    def clone_repository(
        repo_url: str,
        target_dir: str,
        branch: Optional[str] = None,
        pat: Optional[str] = None,
    ) -> str:
        """
        Perform a shallow clone (depth=1) of the specified repository.
        Returns the cloned directory path.
        """
        # Inject authentication token into HTTPS clone URL if PAT provided
        clone_url = repo_url
        if pat and "github.com" in repo_url:
            cleaned = repo_url.replace("https://", "").replace("http://", "")
            clone_url = f"https://x-access-token:{pat}@{cleaned}"

        os.makedirs(target_dir, exist_ok=True)

        clone_kwargs = {
            "depth": 1,
            "single_branch": True,
        }
        if branch:
            clone_kwargs["branch"] = branch

        try:
            git.Repo.clone_from(clone_url, target_dir, **clone_kwargs)
            return target_dir
        except git.GitCommandError as exc:
            # Clean up on failure
            shutil.rmtree(target_dir, ignore_errors=True)
            raise IngestionError(f"Échec du clonage Git: {exc.stderr or str(exc)}")

    @staticmethod
    def cleanup_directory(target_dir: str) -> None:
        """Safely removes cloned directory."""
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
