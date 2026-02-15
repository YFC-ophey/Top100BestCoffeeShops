"""Shared fixtures for scraper tests."""

import pytest
from bs4 import BeautifulSoup


def make_soup(html):
    """Helper to create a BeautifulSoup object from HTML string."""
    return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Mock HTML: List pages
# ---------------------------------------------------------------------------

MOCK_LIST_HTML = """
<html><body>
<div class="elementor-section">
  <a href="/locales/tobbys-estate/">
    <img src="/img/toby.jpg" alt="Toby's Estate"/>
  </a>
  <a href="/locales/tobbys-estate/">
    <h3>1</h3>
  </a>
  <a href="/locales/tobbys-estate/">
    <h2>Toby's Estate Coffee Roasters</h2>
  </a>
  <a href="/locales/tobbys-estate/">
    <p>Australia</p>
  </a>

  <a href="/locales/onyx-coffee-lab/">
    <img src="/img/onyx.jpg" alt="Onyx"/>
  </a>
  <a href="/locales/onyx-coffee-lab/">
    <h3>2</h3>
  </a>
  <a href="/locales/onyx-coffee-lab/">
    <h2>Onyx Coffee LAB</h2>
  </a>
  <a href="/locales/onyx-coffee-lab/">
    <p>USA</p>
  </a>

  <a href="https://theworlds100bestcoffeeshops.com/locales/gota-coffee-experts/">
    <img src="/img/gota.jpg" alt="Gota"/>
  </a>
  <a href="https://theworlds100bestcoffeeshops.com/locales/gota-coffee-experts/">
    <h3>3</h3>
  </a>
  <a href="https://theworlds100bestcoffeeshops.com/locales/gota-coffee-experts/">
    <h2>Gota Coffee Experts</h2>
  </a>
  <a href="https://theworlds100bestcoffeeshops.com/locales/gota-coffee-experts/">
    <p>Austria</p>
  </a>

  <a href="/about/">About Us</a>
  <a href="/">Home</a>
</div>
</body></html>
"""

MOCK_SOUTH_LIST_HTML = """
<html><body>
<div class="elementor-section">
  <a href="/locales-south/tropicalia-coffee/">
    <img src="/img/trop.jpg" alt="Tropicalia"/>
  </a>
  <a href="/locales-south/tropicalia-coffee/">
    <h3>1</h3>
  </a>
  <a href="/locales-south/tropicalia-coffee/">
    <h2>Tropicalia Coffee</h2>
  </a>
  <a href="/locales-south/tropicalia-coffee/">
    <p>Colombia</p>
  </a>
</div>
</body></html>
"""

# ---------------------------------------------------------------------------
# Mock HTML: Detail pages
# ---------------------------------------------------------------------------

MOCK_DETAIL_HTML = """
<html><body>
<div class="detail-page">
  <h1>Toby's Estate Coffee Roasters</h1>
  <p>Sydney</p>
  <p>Australia</p>
  <p>Some description about the shop that is longer than a city name
     and talks about how great the coffee is.</p>
  <h2>Contact</h2>
  <p>32-36 City Rd, Chippendale NSW 2008, Australia</p>
  <a href="https://www.tobysestate.com.au/">
    https://www.tobysestate.com.au/
  </a>
  <a href="https://www.instagram.com/tobysestatecoffee/">
    https://www.instagram.com/tobysestatecoffee/
  </a>
</div>
</body></html>
"""

MOCK_DETAIL_CONTACTO_HTML = """
<html><body>
<div class="detail-page">
  <h2>Tropicalia Coffee</h2>
  <p>Bogota</p>
  <p>Colombia</p>
  <h2>Contacto</h2>
  <p>Cl. 81a #8-23, Bogota, Colombia</p>
  <a href="https://tropicalia.co/">https://tropicalia.co/</a>
</div>
</body></html>
"""

MOCK_DETAIL_NO_CONTACT_HTML = """
<html><body>
<div class="detail-page">
  <h1>Mystery Coffee Shop</h1>
  <p>Berlin</p>
  <p>Germany</p>
  <p>No contact section on this page at all.</p>
</div>
</body></html>
"""

MOCK_DETAIL_URL_IN_TEXT = """
<html><body>
<div class="detail-page">
  <h1>Link Coffee</h1>
  <p>Tokyo</p>
  <p>Japan</p>
  <h2>Contact</h2>
  <p>1-2-3 Shibuya, Tokyo, Japan</p>
  <p>http://linkcoffee.jp</p>
</div>
</body></html>
"""

MOCK_DETAIL_ONYX = """
<html><body>
<h1>Onyx Coffee LAB</h1>
<p>Rogers</p><p>USA</p>
<h2>Contact</h2>
<p>101 E Walnut Ave, Rogers, AR 72756, USA</p>
<a href="https://onyxcoffeelab.com/">x</a>
</body></html>
"""

MOCK_DETAIL_GOTA = """
<html><body>
<h1>Gota Coffee Experts</h1>
<p>Vienna</p><p>Austria</p>
<h2>Contact</h2>
<p>Zollergasse 6, 1070 Wien, Austria</p>
<a href="https://gota.at/">x</a>
</body></html>
"""
