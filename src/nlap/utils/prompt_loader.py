"""Utility for loading prompts from files."""

from pathlib import Path

from nlap.utils.logger import get_logger

logger = get_logger(__name__)

# Get the project root directory (assuming prompts/ is at the root)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_PROMPTS_DIR = _PROJECT_ROOT / "prompts"

# Cache for loaded prompts
_PROMPT_CACHE: dict[str, str] = {}


def load_prompt(filename: str) -> str:
    """Load a prompt from a file in the prompts directory.

    Prompts are cached after first load to avoid repeated file reads.

    Args:
        filename: Name of the prompt file (e.g., "nlp_parser_system.txt")

    Returns:
        Contents of the prompt file as a string

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        IOError: If there's an error reading the file
    """
    # Check cache first
    if filename in _PROMPT_CACHE:
        logger.debug("Prompt loaded from cache", filename=filename)
        return _PROMPT_CACHE[filename]

    prompt_path = _PROMPTS_DIR / filename

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            # Cache the loaded prompt
            _PROMPT_CACHE[filename] = content
            logger.debug("Prompt loaded from file and cached", filename=filename, length=len(content))
            return content
    except IOError as e:
        logger.error(
            "Failed to load prompt file",
            filename=filename,
            path=str(prompt_path),
            error=str(e),
        )
        raise


def get_prompt_path(filename: str) -> Path:
    """Get the full path to a prompt file.

    Args:
        filename: Name of the prompt file

    Returns:
        Path object to the prompt file
    """
    return _PROMPTS_DIR / filename


def clear_cache() -> None:
    """Clear the prompt cache.

    Useful for testing or when prompts need to be reloaded from disk.
    """
    _PROMPT_CACHE.clear()
    logger.debug("Prompt cache cleared")

