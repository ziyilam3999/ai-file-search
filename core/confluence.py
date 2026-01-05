"""CORE: confluence.py
Purpose: Confluence Cloud API client for fetching and indexing pages.
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import yaml
from loguru import logger

# Optional imports - will fail gracefully if not installed
try:
    from atlassian import Confluence

    HAS_ATLASSIAN = True
except ImportError:
    HAS_ATLASSIAN = False
    Confluence = None

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None


CONFIG_PATH = Path("config/confluence.yaml")
ENV_PATH = Path(".env")


@dataclass
class ConfluencePage:
    """Represents a Confluence page with extracted content."""

    page_id: str
    title: str
    space_key: str
    content: str  # Plain text extracted from HTML
    url: str
    version: int
    last_modified: str
    ancestors: List[str] = field(default_factory=list)  # Folder hierarchy
    labels: List[str] = field(default_factory=list)

    @property
    def hierarchy_path(self) -> str:
        """Get the full path including ancestors."""
        if self.ancestors:
            return " / ".join(self.ancestors + [self.title])
        return self.title


class ConfluenceClient:
    """Client for interacting with Confluence Cloud API."""

    def __init__(
        self,
        url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        """
        Initialize Confluence client.

        Args:
            url: Confluence instance URL (e.g., https://company.atlassian.net)
            email: User email for authentication
            api_token: API token from https://id.atlassian.com/manage-profile/security/api-tokens
        """
        if not HAS_ATLASSIAN:
            raise ImportError(
                "atlassian-python-api is not installed. "
                "Install it with: pip install atlassian-python-api"
            )

        if not HAS_BS4:
            raise ImportError(
                "beautifulsoup4 is not installed. "
                "Install it with: pip install beautifulsoup4"
            )

        # Load from parameters, environment, or .env file
        self.url = url or self._get_env("CONFLUENCE_URL")
        self.email = email or self._get_env("CONFLUENCE_EMAIL")
        self.api_token = api_token or self._get_env("CONFLUENCE_API_TOKEN")

        if not all([self.url, self.email, self.api_token]):
            missing = []
            if not self.url:
                missing.append("CONFLUENCE_URL")
            if not self.email:
                missing.append("CONFLUENCE_EMAIL")
            if not self.api_token:
                missing.append("CONFLUENCE_API_TOKEN")
            raise ValueError(
                f"Missing Confluence credentials: {', '.join(missing)}. "
                "Set them in .env file or environment variables."
            )

        # Initialize Confluence API client
        self._client = Confluence(
            url=self.url,
            username=self.email,
            password=self.api_token,
            cloud=True,
        )

        self._config = self._load_config()

    def _get_env(self, key: str) -> Optional[str]:
        """Get environment variable, loading from .env if needed."""
        # First check environment
        value = os.environ.get(key)
        if value:
            return value

        # Try loading from .env file
        if ENV_PATH.exists():
            try:
                with open(ENV_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == key:
                            return v
            except Exception as e:
                logger.warning(f"Failed to read .env file: {e}")

        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load Confluence sync configuration."""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load Confluence config: {e}")
        return {}

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save Confluence sync configuration."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the Confluence connection.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Try to get current user info
            user = self._client.get_current_user()
            if user:
                display_name = user.get(
                    "displayName", user.get("publicName", "Unknown")
                )
                return True, f"Connected as {display_name}"
            return False, "Could not retrieve user info"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_spaces(self) -> List[Dict[str, str]]:
        """
        Get list of accessible spaces.

        Returns:
            List of dicts with 'key', 'name', 'type' keys
        """
        try:
            spaces = self._client.get_all_spaces(start=0, limit=100)
            results = spaces.get("results", [])
            return [
                {
                    "key": s.get("key", ""),
                    "name": s.get("name", ""),
                    "type": s.get("type", ""),
                }
                for s in results
            ]
        except Exception as e:
            logger.error(f"Failed to get spaces: {e}")
            return []

    def get_all_pages(
        self,
        space_key: str,
        limit: int = 500,
    ) -> Generator[ConfluencePage, None, None]:
        """
        Get all pages from a space.

        Args:
            space_key: The Confluence space key
            limit: Maximum pages to fetch

        Yields:
            ConfluencePage objects
        """
        try:
            start = 0
            page_size = 50  # API limit per request
            fetched = 0

            while fetched < limit:
                logger.info(f"Fetching pages {start} to {start + page_size}...")

                pages = self._client.get_all_pages_from_space(
                    space=space_key,
                    start=start,
                    limit=page_size,
                    expand="body.storage,version,ancestors,metadata.labels",
                )

                if not pages:
                    break

                for page_data in pages:
                    try:
                        page = self._parse_page(page_data, space_key)
                        if page:
                            yield page
                            fetched += 1
                            if fetched >= limit:
                                break
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse page {page_data.get('id')}: {e}"
                        )
                        continue

                if len(pages) < page_size:
                    break  # No more pages

                start += page_size

        except Exception as e:
            logger.error(f"Failed to fetch pages from space {space_key}: {e}")

    def get_page(self, page_id: str) -> Optional[ConfluencePage]:
        """
        Get a single page by ID.

        Args:
            page_id: The Confluence page ID

        Returns:
            ConfluencePage or None if not found
        """
        try:
            page_data = self._client.get_page_by_id(
                page_id=page_id,
                expand="body.storage,version,ancestors,metadata.labels,space",
            )
            if page_data:
                space_key = page_data.get("space", {}).get("key", "")
                return self._parse_page(page_data, space_key)
        except Exception as e:
            logger.error(f"Failed to get page {page_id}: {e}")
        return None

    def _parse_page(
        self, page_data: Dict[str, Any], space_key: str
    ) -> Optional[ConfluencePage]:
        """Parse API response into ConfluencePage object."""
        try:
            page_id = str(page_data.get("id", ""))
            title = page_data.get("title", "")

            # Get HTML content
            body = page_data.get("body", {})
            storage = body.get("storage", {})
            html_content = storage.get("value", "")

            # Extract plain text from HTML
            plain_text = self._extract_text_from_html(html_content)

            # Get version info
            version_info = page_data.get("version", {})
            version = version_info.get("number", 1)
            when = version_info.get("when", "")

            # Get ancestors (folder hierarchy)
            ancestors = []
            for ancestor in page_data.get("ancestors", []):
                ancestor_title = ancestor.get("title", "")
                if ancestor_title:
                    ancestors.append(ancestor_title)

            # Get labels
            labels = []
            metadata = page_data.get("metadata", {})
            labels_data = metadata.get("labels", {})
            for label in labels_data.get("results", []):
                label_name = label.get("name", "")
                if label_name:
                    labels.append(label_name)

            # Build URL
            base_url = (self.url or "").rstrip("/")
            url = f"{base_url}/wiki/spaces/{space_key}/pages/{page_id}"

            return ConfluencePage(
                page_id=page_id,
                title=title,
                space_key=space_key,
                content=plain_text,
                url=url,
                version=version,
                last_modified=when,
                ancestors=ancestors,
                labels=labels,
            )

        except Exception as e:
            logger.error(f"Failed to parse page data: {e}")
            return None

    def _extract_text_from_html(self, html: str) -> str:
        """
        Extract plain text from Confluence storage format HTML.

        Handles common Confluence macros and structures.
        """
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        # Handle specific Confluence macros

        # Expand macro - include content
        for expand in soup.find_all("ac:structured-macro", {"ac:name": "expand"}):
            # Keep the content, just unwrap the macro
            expand.unwrap()

        # Code blocks - preserve with markers
        for code in soup.find_all("ac:structured-macro", {"ac:name": "code"}):
            code_body = code.find("ac:plain-text-body")
            if code_body:
                code_text = code_body.get_text()
                code.replace_with(f"\n```\n{code_text}\n```\n")

        # Info/Note/Warning panels - include content
        for panel in soup.find_all(
            "ac:structured-macro", {"ac:name": re.compile(r"info|note|warning|tip")}
        ):
            panel.unwrap()

        # Status macros - extract text
        for status in soup.find_all("ac:structured-macro", {"ac:name": "status"}):
            title_param = status.find("ac:parameter", {"ac:name": "title"})
            if title_param:
                status.replace_with(f"[{title_param.get_text()}]")
            else:
                status.decompose()

        # Tables - convert to simple text format
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                rows.append(" | ".join(cells))
            table.replace_with("\n" + "\n".join(rows) + "\n")

        # Get text with spacing
        text = soup.get_text(separator="\n")

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]  # Remove empty lines
        text = "\n".join(lines)

        # Normalize multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def get_sync_status(self) -> Dict[str, Any]:
        """Get the current sync status."""
        return {
            "last_sync": self._config.get("last_sync"),
            "pages_indexed": self._config.get("pages_indexed", 0),
            "space_key": self._config.get("space_key"),
            "errors": self._config.get("errors", []),
        }

    def update_sync_status(
        self,
        space_key: str,
        pages_indexed: int,
        errors: Optional[List[str]] = None,
    ) -> None:
        """Update the sync status after a sync operation."""
        self._config["last_sync"] = datetime.now().isoformat()
        self._config["pages_indexed"] = pages_indexed
        self._config["space_key"] = space_key
        self._config["errors"] = errors or []
        self._save_config(self._config)

    def get_indexed_versions(self) -> Dict[str, int]:
        """Get the version numbers of previously indexed pages."""
        return self._config.get("indexed_versions", {})

    def update_indexed_version(self, page_id: str, version: int) -> None:
        """Update the indexed version for a page."""
        if "indexed_versions" not in self._config:
            self._config["indexed_versions"] = {}
        self._config["indexed_versions"][page_id] = version
        self._save_config(self._config)


def check_confluence_dependencies() -> Tuple[bool, str]:
    """
    Check if Confluence integration dependencies are installed.

    Returns:
        Tuple of (all_installed, message)
    """
    missing = []

    if not HAS_ATLASSIAN:
        missing.append("atlassian-python-api")

    if not HAS_BS4:
        missing.append("beautifulsoup4")

    if missing:
        return (
            False,
            f"Missing packages: {', '.join(missing)}. Install with: pip install {' '.join(missing)}",
        )

    return True, "All dependencies installed"
