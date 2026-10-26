"""Low-cost visual selection for Bakra News; no network, no API quota.

Use an illustrated prop only when the spoken line actually supports it.
For other news, use an animated topic card rather than unrelated COD objects.
"""
import re

SCENE_RULES = (
    ("laddoo_hdmi", ("लड्डू", "hdmi")),
    ("bill", ("बिल", "रुपये", "₹", "कीमत", "पैसे")),
    ("showroom", ("टीवी", "फ्रिज", "showroom")),
    ("sweets", ("मिठाई", "लड्डू")),
    ("delivery", ("डिलीवरी", "पार्सल", "cod", "कूरियर")),
)

def select_visual(line, episode, index=0):
    """Return renderer-compatible visual beats and a traceable selection reason."""
    speech = str(line.get("say") or "")
    explicit = str(line.get("scene") or "").strip()
    topic = " ".join(str(episode.get(k) or "") for k in ("title", "breaking", "topic"))
    context = (speech + " " + topic).lower()
    is_delivery_story = any(word in topic.lower() for word in ("cod", "पार्सल", "डिलीवरी", "कूरियर"))
    if is_delivery_story:
        if explicit in {"sweets", "arrival", "showroom", "laddoo_hdmi", "bill", "shop", "delivery"}:
            scene = explicit
        else:
            scene = next((name for name, words in SCENE_RULES if any(w in speech.lower() for w in words)), "delivery")
        return [{"scene": scene}], "illustrated:" + scene
    # Avoid unrelated COD-specific cartoon props for train, exam, weather, etc.
    short_topic = re.sub(r"\s+", " ", topic).strip()
    short_topic = " ".join(short_topic.split()[:5]) or "खबर का नया मोड़"
    return [{"big": short_topic, "color": "#274B83"},
            {"big": short_topic, "color": "#8C3B67"}], "kinetic-topic"

def compare_visual_options(line, episode):
    """Transparent pre-render decision; not an audience engagement score."""
    visuals, reason = select_visual(line, episode)
    return {"chosen": reason, "alternatives": ["verified-news-clip", "illustrated-props", "kinetic-topic"],
            "visuals": visuals, "requires_verified_media": reason != "kinetic-topic"}
