import pytest
from tools import search_listings, suggest_outfit, create_fit_card

# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_item():
    return {
        "id": "lst_006",
        "title": "Graphic Tee — 2003 Tour Bootleg Style",
        "description": "Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.",
        "category": "tops",
        "style_tags": ["graphic tee", "vintage", "grunge", "streetwear", "band tee"],
        "size": "L",
        "condition": "good",
        "price": 24.00,
        "colors": ["black"],
        "brand": None,
        "platform": "depop",
    }


@pytest.fixture
def sample_wardrobe():
    return {
        "items": [
            {
                "id": "w_001",
                "name": "Baggy straight-leg jeans, dark wash",
                "category": "bottoms",
                "colors": ["dark blue", "indigo"],
                "style_tags": ["denim", "streetwear", "baggy"],
                "notes": "High-waisted, sits above the hip",
            },
            {
                "id": "w_007",
                "name": "Chunky white sneakers",
                "category": "shoes",
                "colors": ["white"],
                "style_tags": ["sneakers", "chunky", "streetwear"],
                "notes": None,
            },
        ]
    }


@pytest.fixture
def empty_wardrobe():
    return {"items": []}


@pytest.fixture
def sample_outfit():
    return (
        "Pair the graphic tee with baggy dark-wash jeans and chunky white sneakers "
        "for a classic streetwear look. Tuck the front of the tee for a bit of shape."
    )


# ── search_listings ────────────────────────────────────────────────────────────

def test_search_returns_results():
    """A common keyword returns at least one matching listing."""
    results = search_listings("vintage graphic tee")
    assert len(results) > 0


def test_search_empty_results():
    """An impossible query with no keyword overlap returns an empty list."""
    results = search_listings("unobtanium quantum xyzzy")
    assert results == []


def test_search_price_filter():
    """Every result respects the max_price ceiling."""
    max_price = 25.0
    results = search_listings("vintage", max_price=max_price)
    assert all(item["price"] <= max_price for item in results)


def test_search_size_filter():
    """Every result contains the requested size string (case-insensitive)."""
    results = search_listings("top", size="S/M")
    assert all("s/m" in item["size"].lower() for item in results)


def test_search_no_size_filter():
    """Passing size=None does not raise and returns a list."""
    results = search_listings("jeans", size=None)
    assert isinstance(results, list)


# ── suggest_outfit ─────────────────────────────────────────────────────────────

def test_suggest_with_wardrobe(sample_item, sample_wardrobe):
    """Returns a non-empty string when the wardrobe has items."""
    result = suggest_outfit(sample_item, sample_wardrobe)
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_suggest_empty_wardrobe(sample_item, empty_wardrobe):
    """Returns a non-empty string even when the wardrobe is empty."""
    result = suggest_outfit(sample_item, empty_wardrobe)
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_suggest_never_crashes(sample_item, empty_wardrobe):
    """Does not raise an exception when called with an empty wardrobe."""
    result = suggest_outfit(sample_item, empty_wardrobe)
    assert result is not None


# ── create_fit_card ────────────────────────────────────────────────────────────

def test_fit_card_returns_string(sample_item, sample_outfit):
    """Returns a non-empty string for valid item and outfit inputs."""
    result = create_fit_card(sample_outfit, sample_item)
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_fit_card_empty_outfit(sample_item):
    """Returns an error message string (not an exception) when outfit is empty."""
    result = create_fit_card("", sample_item)
    assert isinstance(result, str)
    assert "error" in result.lower()


def test_fit_card_varies(sample_item, sample_outfit):
    """Two calls with the same input produce different captions (temperature=1.0)."""
    first = create_fit_card(sample_outfit, sample_item)
    second = create_fit_card(sample_outfit, sample_item)
    assert isinstance(first, str) and isinstance(second, str)
    assert first != second
