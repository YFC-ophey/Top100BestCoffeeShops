from src.models import CoffeeShop
from src.scraper import enrich_shops_with_details, extract_city_address, parse_coffee_shops


def test_parse_coffee_shops_extracts_rank_name_and_location() -> None:
    html = """
    <html><body>
      <ol>
        <li>1. Coffee Collective - Copenhagen, Denmark</li>
        <li>2. Proud Mary - Melbourne, Australia</li>
      </ol>
    </body></html>
    """

    shops = parse_coffee_shops(html, category="Top 100")

    assert len(shops) == 2
    assert shops[0].rank == 1
    assert shops[0].name == "Coffee Collective"
    assert shops[0].city == "Copenhagen"
    assert shops[0].country == "Denmark"
    assert shops[0].category == "Top 100"


def test_parse_coffee_shops_skips_unparseable_entries() -> None:
    html = """
    <html><body>
      <ol>
        <li>Not a ranked item</li>
        <li>3. Tim Wendelboe - Oslo, Norway</li>
      </ol>
    </body></html>
    """

    shops = parse_coffee_shops(html, category="Top 100")

    assert len(shops) == 1
    assert shops[0].name == "Tim Wendelboe"


def test_parse_coffee_shops_extracts_from_elementor_loop_cards() -> None:
    html = """
    <div data-elementor-type="loop-item" class="e-loop-item">
      <p class="elementor-heading-title"><a href="https://theworlds100bestcoffeeshops.com/locales/onyx-coffee-lab/">1</a></p>
      <h1 class="elementor-heading-title"><a href="https://theworlds100bestcoffeeshops.com/locales/onyx-coffee-lab/">Onyx Coffee LAB</a></h1>
      <p class="elementor-heading-title"><a href="https://theworlds100bestcoffeeshops.com/locales/onyx-coffee-lab/">USA</a></p>
    </div>
    <div data-elementor-type="loop-item" class="e-loop-item">
      <p class="elementor-heading-title"><a href="https://theworlds100bestcoffeeshops.com/locales/tim-wendelboe/">2</a></p>
      <h1 class="elementor-heading-title"><a href="https://theworlds100bestcoffeeshops.com/locales/tim-wendelboe/">Tim Wendelboe</a></h1>
      <p class="elementor-heading-title"><a href="https://theworlds100bestcoffeeshops.com/locales/tim-wendelboe/">Norway</a></p>
    </div>
    """

    shops = parse_coffee_shops(html, category="Top 100")

    assert len(shops) == 2
    assert shops[0].rank == 1
    assert shops[0].name == "Onyx Coffee LAB"
    assert shops[0].country == "USA"
    assert shops[0].source_url == "https://theworlds100bestcoffeeshops.com/locales/onyx-coffee-lab/"


def test_extract_city_address_from_detail_page() -> None:
    detail_html = """
    <p class="elementor-heading-title elementor-size-default">Rogers, Arkansas</p>
    <p class="elementor-heading-title elementor-size-default">USA</p>
    <p class="elementor-heading-title elementor-size-default">101 E Walnut Ave Rogers, AR 72756, USA</p>
    """
    city, address = extract_city_address(detail_html, fallback_country="USA")
    assert city == "Rogers, Arkansas"
    assert address == "101 E Walnut Ave Rogers, AR 72756, USA"


def test_enrich_shops_with_details_sets_city_and_address() -> None:
    shop = CoffeeShop(
        name="Onyx Coffee LAB",
        city="",
        country="USA",
        rank=1,
        category="Top 100",
        source_url="https://example.com/onyx",
    )
    detail_html = """
    <p class="elementor-heading-title">Rogers, Arkansas</p>
    <p class="elementor-heading-title">USA</p>
    <p class="elementor-heading-title">101 E Walnut Ave Rogers, AR 72756, USA</p>
    """

    def fake_fetcher(url: str) -> str:
        assert url == "https://example.com/onyx"
        return detail_html

    result = enrich_shops_with_details([shop], fetcher=fake_fetcher, sleep_seconds=0.0)
    assert result[0].city == "Rogers, Arkansas"
    assert result[0].address == "101 E Walnut Ave Rogers, AR 72756, USA"
