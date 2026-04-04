"""Provider adapters for free-first research lookup."""

from .arxiv_provider import resolve_arxiv_record
from .doi_provider import resolve_doi_record
from .github_provider import resolve_github_record
from .optional_provider import resolve_optional_record
from .url_provider import resolve_url_record

__all__ = [
    "resolve_arxiv_record",
    "resolve_doi_record",
    "resolve_github_record",
    "resolve_optional_record",
    "resolve_url_record",
]
