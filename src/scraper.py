from html.parser import HTMLParser
import html
import re
from urllib.request import urlopen

from src.models import CoffeeShop

SOURCE_URLS: dict[str, str] = {
    "Top 100": "https://theworlds100bestcoffeeshops.com/top-100-coffee-shops/",
    "South America": "https://theworlds100bestcoffeeshops.com/top-100-coffee-shops-south/",
}

_ITEM_PATTERN = re.compile(
    r"^\s*(?P<rank>\d{1,3})[\).:-]?\s+(?P<name>[^-]+?)\s+-\s+(?P<city>[^,]+),\s*(?P<country>.+)\s*$"
)
_LOOP_CARD_PATTERN = re.compile(
    r'<p class="elementor-heading-title[^"]*">\s*<a href="(?P<href>[^"]+)">\s*(?P<rank>\d{1,3})\s*</a>\s*</p>'
    r".*?"
    r'<h1 class="elementor-heading-title[^"]*">\s*<a href="[^"]+">\s*(?P<name>[^<]+?)\s*</a>\s*</h1>'
    r".*?"
    r'<p class="elementor-heading-title[^"]*">\s*<a href="[^"]+">\s*(?P<country>[^<]+?)\s*</a>\s*</p>',
    re.DOTALL,
)
_LOCALE_LINK_PATTERN = re.compile(
    r'<a href="(?P<href>https://theworlds100bestcoffeeshops\.com/locales/[^"]+/)">(?P<text>.*?)</a>',
    re.DOTALL,
)
_TAG_STRIPPER = re.compile(r"<[^>]+>")


class _ListItemParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_li = False
        self._buffer: list[str] = []
        self.items: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "li":
            self._inside_li = True
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._inside_li:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "li" and self._inside_li:
            text = " ".join(part.strip() for part in self._buffer if part.strip())
            if text:
                self.items.append(text)
            self._inside_li = False
            self._buffer = []


def fetch_html(url: str, timeout_seconds: int = 30) -> str:
    with urlopen(url, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="ignore")


def parse_coffee_shops(html: str, category: str) -> list[CoffeeShop]:
    shops = _parse_legacy_list_items(html, category)
    if shops:
        return shops
    return _parse_elementor_loop_cards(html, category)


def _parse_legacy_list_items(html: str, category: str) -> list[CoffeeShop]:
    parser = _ListItemParser()
    parser.feed(html)
    shops: list[CoffeeShop] = []
    for item in parser.items:
        match = _ITEM_PATTERN.match(item)
        if not match:
            continue
        shops.append(
            CoffeeShop(
                name=match.group("name").strip(),
                city=match.group("city").strip(),
                country=match.group("country").strip(),
                rank=int(match.group("rank")),
                category=category,
            )
        )
    return shops


def _parse_elementor_loop_cards(html: str, category: str) -> list[CoffeeShop]:
    primary = _parse_elementor_loop_cards_primary(html, category)
    fallback = _parse_elementor_loop_cards_by_href(html, category)
    if len(fallback) > len(primary):
        return fallback
    return primary


def _parse_elementor_loop_cards_primary(html: str, category: str) -> list[CoffeeShop]:
    shops: list[CoffeeShop] = []
    for match in _LOOP_CARD_PATTERN.finditer(html):
        shops.append(
            CoffeeShop(
                name=match.group("name").strip(),
                city="",
                country=match.group("country").strip(),
                rank=int(match.group("rank")),
                category=category,
                source_url=match.group("href").strip(),
            )
        )
    return sorted(shops, key=lambda value: value.rank)


def _parse_elementor_loop_cards_by_href(html_content: str, category: str) -> list[CoffeeShop]:
    links: list[tuple[str, str]] = []
    for match in _LOCALE_LINK_PATTERN.finditer(html_content):
        href = match.group("href").strip()
        raw_text = _TAG_STRIPPER.sub("", match.group("text"))
        text = html.unescape(raw_text).strip()
        if text:
            links.append((href, text))

    grouped: list[tuple[str, list[str]]] = []
    current_href: str | None = None
    current_texts: list[str] = []
    for href, text in links:
        if current_href is None:
            current_href = href
        if href != current_href:
            grouped.append((current_href, current_texts))
            current_href = href
            current_texts = []
        current_texts.append(text)
    if current_href is not None:
        grouped.append((current_href, current_texts))

    shops: list[CoffeeShop] = []
    for href, texts in grouped:
        rank: int | None = None
        name: str | None = None
        country: str | None = None
        non_numeric: list[str] = []
        for text in texts:
            if rank is None and text.isdigit():
                rank = int(text)
            elif not text.isdigit():
                non_numeric.append(text)
        if non_numeric:
            name = non_numeric[0]
        if len(non_numeric) > 1:
            country = non_numeric[1]
        if rank is None or name is None or country is None:
            continue
        shops.append(
            CoffeeShop(
                name=name,
                city="",
                country=country,
                rank=rank,
                category=category,
                source_url=href,
            )
        )
    return sorted(shops, key=lambda value: value.rank)
