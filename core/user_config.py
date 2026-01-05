"""
User configuration management for AI File Search.

Provides platform-aware configuration storage for packaged app distribution.
Supports Windows, macOS, and Linux with appropriate config directories.

Config Priority (fallback chain):
1. User config dir (AppData/Library/etc.) - for packaged apps
2. .env file in project root - for development
3. Default values
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

# Config file names
SETTINGS_FILE = "settings.yaml"
CREDENTIALS_FILE = "credentials.yaml"
CONFLUENCE_CACHE_FILE = "confluence_cache.yaml"


def get_user_config_dir() -> Path:
    """
    Get platform-appropriate user config directory.

    Returns:
        Path to user config directory (created if doesn't exist)

    Platform paths:
        Windows: %APPDATA%/ai-file-search/
        macOS: ~/Library/Application Support/ai-file-search/
        Linux: ~/.config/ai-file-search/
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    config_dir = base / "ai-file-search"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_project_root() -> Path:
    """Get the project root directory (where run_app.py is)."""
    return Path(__file__).parent.parent


def _load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load YAML file, return empty dict if not exists or error."""
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return {}


def _parse_env_file(env_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Parse .env file and return key-value pairs.

    This is the SINGLE SOURCE OF TRUTH for reading .env files.
    Handles comments, quoted values, and whitespace.

    Args:
        env_file: Path to .env file. If None, uses project root .env.

    Returns:
        Dict of environment variable key-value pairs, empty if file doesn't exist.
    """
    if env_file is None:
        env_file = get_project_root() / ".env"

    if not env_file.exists():
        return {}

    env_vars: Dict[str, str] = {}
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                # Strip quotes from value
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
    except Exception as e:
        logger.debug(f"Failed to parse .env file: {e}")

    return env_vars


def _save_yaml(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save data to YAML file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        logger.error(f"Failed to save {file_path}: {e}")
        return False


# =============================================================================
# Settings (non-sensitive configuration)
# =============================================================================


def get_settings() -> Dict[str, Any]:
    """
    Get user settings with fallback chain.

    Returns settings dict with keys:
        - confluence_url: str
        - confluence_email: str
        - default_space: str (space key)
        - visible_spaces: list[dict] with 'key' and 'name'
        - watch_paths: list[str]
    """
    config_dir = get_user_config_dir()
    settings_file = config_dir / SETTINGS_FILE

    # Load from user config
    settings = _load_yaml(settings_file)

    # If empty, try to migrate from .env
    if not settings:
        settings = _migrate_from_env()
        if settings:
            _save_yaml(settings_file, settings)
            logger.info(f"Migrated settings from .env to {settings_file}")

    return settings


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save user settings to config directory."""
    config_dir = get_user_config_dir()
    settings_file = config_dir / SETTINGS_FILE
    return _save_yaml(settings_file, settings)


def get_setting(key: str, default: Any = None) -> Any:
    """Get a single setting value."""
    settings = get_settings()
    return settings.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """Set a single setting value."""
    settings = get_settings()
    settings[key] = value
    return save_settings(settings)


# =============================================================================
# Credentials (sensitive - stored separately)
# =============================================================================


def get_credentials() -> Dict[str, str]:
    """
    Get credentials with fallback chain.

    Returns dict with keys:
        - confluence_api_token: str
    """
    config_dir = get_user_config_dir()
    creds_file = config_dir / CREDENTIALS_FILE

    # Load from user config
    creds = _load_yaml(creds_file)

    # Fallback to .env if not in user config
    if not creds.get("confluence_api_token"):
        env_vars = _parse_env_file()
        token = env_vars.get("CONFLUENCE_API_TOKEN", "")
        if token:
            creds["confluence_api_token"] = token

    return creds


def save_credentials(credentials: Dict[str, str]) -> bool:
    """Save credentials to config directory."""
    config_dir = get_user_config_dir()
    creds_file = config_dir / CREDENTIALS_FILE

    # Note: In production, consider encrypting the token
    # For now, we rely on OS file permissions
    success = _save_yaml(creds_file, credentials)

    if success:
        # Set restrictive permissions on credentials file (Unix-like systems)
        if sys.platform != "win32":
            try:
                os.chmod(creds_file, 0o600)
            except Exception:
                pass

    return success


def get_credential(key: str, default: str = "") -> str:
    """Get a single credential value."""
    creds = get_credentials()
    return creds.get(key, default)


# =============================================================================
# Migration from .env
# =============================================================================


def _migrate_from_env() -> Dict[str, Any]:
    """
    Migrate settings from .env file to user config format.

    Returns migrated settings dict, or empty dict if no .env.
    """
    env_vars = _parse_env_file()
    if not env_vars:
        return {}

    settings = {}

    # Confluence settings
    confluence_url = env_vars.get("CONFLUENCE_URL", "")
    confluence_email = env_vars.get("CONFLUENCE_EMAIL", "")

    if confluence_url:
        settings["confluence_url"] = confluence_url
    if confluence_email:
        settings["confluence_email"] = confluence_email

    # Default space (if configured)
    default_space = env_vars.get("CONFLUENCE_DEFAULT_SPACE", "")
    if default_space:
        settings["default_space"] = default_space

    # Migrate credentials separately
    token = env_vars.get("CONFLUENCE_API_TOKEN", "")
    if token:
        save_credentials({"confluence_api_token": token})

    return settings


# =============================================================================
# First-run detection
# =============================================================================


def is_first_run() -> bool:
    """
    Check if this is the first run (no config exists).

    Returns True if:
        - No settings.yaml in user config dir
        - No .env file with credentials
    """
    config_dir = get_user_config_dir()
    settings_file = config_dir / SETTINGS_FILE

    # Check user config
    if settings_file.exists():
        return False

    # Check .env fallback using shared parser
    env_vars = _parse_env_file()
    if env_vars.get("CONFLUENCE_URL") and env_vars.get("CONFLUENCE_API_TOKEN"):
        return False

    return True


def is_confluence_configured() -> bool:
    """Check if Confluence credentials are fully configured."""
    settings = get_settings()
    creds = get_credentials()

    has_url = bool(settings.get("confluence_url"))
    has_email = bool(settings.get("confluence_email"))
    has_token = bool(creds.get("confluence_api_token"))

    return has_url and has_email and has_token


# =============================================================================
# Confluence-specific helpers
# =============================================================================


def get_confluence_config() -> Dict[str, Any]:
    """
    Get full Confluence configuration for UI display.

    Returns:
        Dict with url, email, is_configured, default_space, visible_spaces
        Token is NOT included for security.
    """
    settings = get_settings()
    creds = get_credentials()

    return {
        "url": settings.get("confluence_url", ""),
        "email": settings.get("confluence_email", ""),
        "is_configured": is_confluence_configured(),
        "has_token": bool(creds.get("confluence_api_token")),
        "default_space": settings.get("default_space", ""),
        "visible_spaces": settings.get("visible_spaces", []),
    }


def save_confluence_config(
    url: Optional[str] = None,
    email: Optional[str] = None,
    token: Optional[str] = None,
    default_space: Optional[str] = None,
    visible_spaces: Optional[list] = None,
) -> bool:
    """
    Save Confluence configuration.

    Args:
        url: Confluence base URL
        email: User email for API auth
        token: API token (stored separately in credentials)
        default_space: Default space key to pre-select
        visible_spaces: List of spaces to show in dropdown

    Returns:
        True if all saves succeeded
    """
    settings = get_settings()
    success = True

    if url is not None:
        settings["confluence_url"] = url
    if email is not None:
        settings["confluence_email"] = email
    if default_space is not None:
        settings["default_space"] = default_space
    if visible_spaces is not None:
        settings["visible_spaces"] = visible_spaces

    if not save_settings(settings):
        success = False

    # Save token separately
    if token is not None:
        creds = get_credentials()
        creds["confluence_api_token"] = token
        if not save_credentials(creds):
            success = False

    return success
