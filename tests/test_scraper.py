from src.scraper import parse_coffee_shops


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
