import subprocess
import logging

logger = logging.getLogger(__name__)


def commit_and_push(
    files: list[str],
    message: str = "chore: update run logs [skip ci]",
) -> bool:
    """Stage specific files, commit, and push.

    Returns True on success, False on any failure.
    Safe to call in DRY_RUN – will fail gracefully if git is not configured.
    """
    try:
        # Stage only the specified files (ignore errors for missing files)
        subprocess.run(["git", "add", "--"] + files, check=True, capture_output=True)

        # Check if there is anything staged
        result = subprocess.run(
            ["git", "diff", "--staged", "--quiet"],
            capture_output=True,
        )
        if result.returncode == 0:
            logger.info("Nothing to commit.")
            return True

        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        logger.info("Committed and pushed: %s", files)
        return True
    except subprocess.CalledProcessError as exc:
        logger.warning("git commit/push failed: %s", exc.stderr.decode(errors="replace").strip())
        return False
