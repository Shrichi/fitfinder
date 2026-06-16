"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()
 
    filtered = []
    for item in listings:
        # Price filter
        if max_price is not None and item.get("price", 0) > max_price:
            continue
        # Size filter (case-insensitive, partial match)
        if size is not None:
            item_size = item.get("size", "").lower()
            if size.lower() not in item_size:
                continue
        filtered.append(item)
 
    keywords = set(description.lower().split())
 
    def score(item):
        text = " ".join([
            item.get("title", ""),
            item.get("description", ""),
            item.get("category", ""),
            " ".join(item.get("style_tags", [])),
            item.get("brand", "") or "",
        ]).lower()
        return sum(1 for kw in keywords if kw in text)
 
    scored = [(item, score(item)) for item in filtered]
    scored = [(item, s) for item, s in scored if s > 0]
 
    scored.sort(key=lambda x: x[1], reverse=True)
    return [item for item, _ in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    client = _get_groq_client()
    wardrobe_items = wardrobe.get("items", [])
 
    if not wardrobe_items:
        # Empty wardrobe path: general styling advice
        prompt = f"""You're a thrift fashion stylist. A user just found this secondhand item:
 
            Item: {new_item.get('title')}
            Description: {new_item.get('description')}
            Category: {new_item.get('category')}
            Style tags: {', '.join(new_item.get('style_tags', []))}
            Colors: {', '.join(new_item.get('colors', []))}
            Condition: {new_item.get('condition')}
            
            The user hasn't told you about their wardrobe yet. Give them 1-2 specific outfit ideas 
            for this piece — suggest what types of items would pair well with it (e.g. "wide-leg 
            jeans", "white sneakers"), what vibe or aesthetic it suits, and one concrete styling tip 
            (like tucking, layering, or accessorizing). Keep it conversational and specific."""
 
    else:
        # Wardrobe path: suggest specific combinations
        wardrobe_text = "\n".join(
            f"- {item.get('name')} ({item.get('category')}, {', '.join(item.get('colors', []))})"
            + (f": {item.get('notes')}" if item.get("notes") else "")
            for item in wardrobe_items
        )
 
        prompt = f"""You're a thrift fashion stylist. A user just found this secondhand item:
 
            Item: {new_item.get('title')}
            Description: {new_item.get('description')}
            Category: {new_item.get('category')}
            Style tags: {', '.join(new_item.get('style_tags', []))}
            Colors: {', '.join(new_item.get('colors', []))}
            Condition: {new_item.get('condition')}
            
            Here's what's already in their wardrobe:
            {wardrobe_text}
            
            Suggest 1-2 complete outfit combinations using the new item and specific named pieces 
            from their wardrobe above. For each outfit, mention which exact wardrobe pieces to pair 
            it with, the overall vibe, and one styling tip (tuck, layer, accessorize, etc.). 
            Keep it conversational and specific — like advice from a friend who knows fashion."""
 
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
 
    result = response.choices[0].message.content.strip()
    return result if result else "This piece has great styling potential — try pairing it with basics in neutral tones to let it stand out."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    if not outfit or not outfit.strip():
        return "Error: outfit description is missing — cannot generate a fit card."
 
    client = _get_groq_client()
 
    prompt = f"""Write a 2-4 sentence Instagram caption for a thrift outfit post. 
 
                The thrifted item:
                - Name: {new_item.get('title')}
                - Price: ${new_item.get('price')}
                - Platform: {new_item.get('platform')}
                - Condition: {new_item.get('condition')}
                
                The outfit idea:
                {outfit}
                
                Rules:
                - Sound like a real person posting an OOTD, not a product description
                - Mention the item name, price, and platform naturally (each once)
                - Capture the specific vibe of the outfit in your own words
                - Casual, authentic tone — lowercase is fine, emojis are fine (1-2 max)
                - Do NOT use generic phrases like "loving this look" or "obsessed with this find"
                - Make it feel specific to THIS outfit, not a template"""
                
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,  # Higher temperature for more varied captions
        max_tokens=150,
    )
 
    result = response.choices[0].message.content.strip()
    return result if result else "Error: fit card generation returned an empty response."
