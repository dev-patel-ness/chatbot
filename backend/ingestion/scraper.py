"""Web Scraper / Content Extractor (architecture.md §6).

Parses rendered HTML into the structured PageData schema: text, headings,
links, buttons, forms, menus/navigation, and metadata.
"""
from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from .models import ButtonElement, FormElement, FormField, LinkElement, PageData

_NON_CONTENT_TAGS = ("script", "style", "noscript", "svg", "template")


class ContentExtractor:
    """Extracts structured content + UI elements from a page's rendered HTML."""

    def extract(self, url: str, html: str, depth: int = 0, status_code: int | None = None) -> PageData:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.find_all(_NON_CONTENT_TAGS):
            tag.decompose()

        return PageData(
            url=url,
            title=self._extract_title(soup),
            headings=self._extract_headings(soup),
            content=self._extract_text(soup),
            links=self._extract_links(soup, url),
            buttons=self._extract_buttons(soup),
            forms=self._extract_forms(soup, url),
            navigation=self._extract_navigation(soup, url),
            depth=depth,
            status_code=status_code,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return ""

    def _extract_headings(self, soup: BeautifulSoup) -> list[str]:
        headings: list[str] = []
        for level in ("h1", "h2", "h3"):
            for tag in soup.find_all(level):
                text = tag.get_text(strip=True)
                if text:
                    headings.append(text)
        return headings

    def _extract_text(self, soup: BeautifulSoup) -> str:
        body = soup.body or soup
        text = body.get_text(separator=" ", strip=True)
        # Collapse repeated whitespace produced by nested inline tags.
        return " ".join(text.split())

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[LinkElement]:
        links: list[LinkElement] = []
        seen: set[str] = set()
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            absolute = urljoin(base_url, href)
            if absolute in seen:
                continue
            seen.add(absolute)
            links.append(LinkElement(text=tag.get_text(strip=True), href=absolute))
        return links

    def _extract_buttons(self, soup: BeautifulSoup) -> list[ButtonElement]:
        buttons: list[ButtonElement] = []
        for tag in soup.find_all("button"):
            text = tag.get_text(strip=True)
            if text:
                buttons.append(ButtonElement(text=text))
        for tag in soup.find_all("input", attrs={"type": ["button", "submit"]}):
            value = tag.get("value", "").strip()
            if value:
                buttons.append(ButtonElement(text=value))
        for tag in soup.find_all(attrs={"role": "button"}):
            text = tag.get_text(strip=True)
            if text:
                buttons.append(ButtonElement(text=text))
        return buttons

    def _extract_forms(self, soup: BeautifulSoup, base_url: str) -> list[FormElement]:
        forms: list[FormElement] = []
        for form_tag in soup.find_all("form"):
            fields: list[FormField] = []
            for field_tag in form_tag.find_all(("input", "select", "textarea")):
                field_type = field_tag.get("type") if field_tag.name == "input" else field_tag.name
                fields.append(
                    FormField(
                        name=field_tag.get("name"),
                        type=field_type,
                        placeholder=field_tag.get("placeholder"),
                    )
                )
            action = form_tag.get("action")
            forms.append(
                FormElement(
                    action=urljoin(base_url, action) if action else None,
                    method=(form_tag.get("method") or "get").lower(),
                    fields=fields,
                )
            )
        return forms

    def _extract_navigation(self, soup: BeautifulSoup, base_url: str) -> list[LinkElement]:
        nav_links: list[LinkElement] = []
        seen: set[str] = set()
        nav_containers: list[Tag] = soup.find_all("nav")
        nav_containers += soup.find_all(attrs={"role": "navigation"})
        for container in nav_containers:
            for tag in container.find_all("a", href=True):
                href = tag["href"].strip()
                if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                    continue
                absolute = urljoin(base_url, href)
                if absolute in seen:
                    continue
                seen.add(absolute)
                nav_links.append(LinkElement(text=tag.get_text(strip=True), href=absolute))
        return nav_links
