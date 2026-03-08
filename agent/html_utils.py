"""HTML cleaning utilities for the browser agent.

Provides `clean_html` and `extract_text` helpers that use BeautifulSoup
to remove scripts, styles, iframes, svgs, comments and common clutter
by id/class selectors while preserving semantic structure.
"""
from typing import List, Optional
import re

from bs4 import BeautifulSoup, Comment


DEFAULT_CLUTTER_KEYWORDS = [
    "advert", "cookie", "consent", "banner", "footer", "header", "nav", "menu", "subscribe", "modal", "popup",
]


def _line_based_fallback(html: str) -> str:
    # Very small fallback to original naive remover if parsing breaks
    clutter_keywords = ['advertisement', 'cookie', 'privacy policy', 'terms of service', 'footer', 'header', 'nav', 'menu']
    lines = html.splitlines()
    cleaned_lines = [line for line in lines if not any(keyword in line.lower() for keyword in clutter_keywords)]
    return "\n".join(cleaned_lines)


def _truncate_to_sentence(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    # Try to end at a sentence boundary within the last 200 chars
    snippet = text[:max_chars]
    last_period = snippet.rfind('.')
    if last_period != -1 and max_chars - last_period < 200:
        return snippet[: last_period + 1]
    return snippet


def extract_text(html: str, max_chars: int = 4000) -> str:
    """Return plain-text extracted from HTML, truncated to `max_chars`.

    This preserves basic sentence structure.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove scripts/styles/comments first for cleaner text
        for node in soup(["script", "style", "noscript"]):
            node.decompose()
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        text = soup.get_text(separator=' ', strip=True)
        # Normalize whitespace
        text = re.sub(r"\s+", ' ', text)
        return _truncate_to_sentence(text, max_chars)
    except Exception:
        return _truncate_to_sentence(_line_based_fallback(html), max_chars)


def clean_html(html: str, max_preview_chars: int = 8000, remove_selectors: Optional[List[str]] = None) -> str:
    """Clean HTML and return a string suitable as an LLM preview.

    - Removes scripts, styles, noscript, iframes, svgs and comments
    - Removes elements whose id/class contain common clutter keywords
    - Removes selectors passed via `remove_selectors`
    - Preserves semantic tags (headings, paragraphs, lists)
    - Normalizes whitespace and truncates to `max_preview_chars` attempting to end at sentence boundary
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted tags
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
            tag.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove elements matching remove_selectors
        if remove_selectors:
            for sel in remove_selectors:
                for node in soup.select(sel):
                    node.decompose()

        # Remove elements by clutter keywords in id/class
        keywords = DEFAULT_CLUTTER_KEYWORDS
        for node in soup.find_all(True):
            did_remove = False
            if node.has_attr('id'):
                nid = str(node['id']).lower()
                if any(k in nid for k in keywords):
                    node.decompose()
                    did_remove = True
            if did_remove:
                continue
            if node.has_attr('class'):
                classes = ' '.join(node.get('class') or []).lower()
                if any(k in classes for k in keywords):
                    node.decompose()

        # Prefer main/article if available
        main_container = soup.find('main') or soup.find('article') or soup.body or soup

        # Build cleaned HTML keeping headings, paragraphs, lists and links
        parts = []
        for tag in main_container.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'blockquote', 'pre', 'a', 'li'], recursive=True):
            # Skip empty tags
            text = tag.get_text(separator=' ', strip=True)
            if not text:
                continue
            # For list items, prefix with dash
            if tag.name == 'li':
                parts.append(f"- {text}")
            elif tag.name in ('ul', 'ol'):
                # lists themselves are handled through li
                continue
            else:
                parts.append(text)

        cleaned = '\n\n'.join(parts).strip()
        cleaned = re.sub(r"\s+", ' ', cleaned)
        cleaned = _truncate_to_sentence(cleaned, max_preview_chars)
        return cleaned
    except Exception:
        # Fallback to line-based
        return _line_based_fallback(html)[:max_preview_chars]
