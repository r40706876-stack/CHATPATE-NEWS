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
    topic = " ".join(str(episode.get(k) or "") for k in ("title", "breaking", "topic"))
    # A news topic alone must not force a literal prop. All unverified media
    # follows the same animated stage pipeline, including COD stories.
    # Avoid unrelated COD-specific cartoon props for train, exam, weather, etc.
    short_topic = re.sub(r"\s+", " ", topic).strip()
    short_topic = " ".join(short_topic.split()[:5]) or "खबर का नया मोड़"
    # Caption reflects the current speaker, not an identical headline on every line.
    caption = re.sub(r"\s+", " ", str(line.get("tag_text") or line.get("caption") or speech)).strip()
    caption = " ".join(caption.split()[:7]) or short_topic
    from hybrid_stage import topic_of, concept_of
    # Prefer what the speaker says over incidental keywords in the headline.
    line_kind = topic_of(speech)
    kind = line_kind if line_kind != "news" else topic_of(topic)
    concept = concept_of(speech)
    beats = ["setup", "action", "payoff"] if concept in ("laddoo_hdmi", "receipt") else ["setup", "reaction"]
    return [{"hybrid_stage": True, "topic": kind, "concept": concept,
             "caption": caption, "beats": beats}], "animated-stage:" + (concept or kind)

def compare_visual_options(line, episode):
    """Transparent pre-render decision; not an audience engagement score."""
    visuals, reason = select_visual(line, episode)
    return {"chosen": reason, "alternatives": ["verified-news-clip", "animated-topic-stage", "kinetic-topic"],
            "visuals": visuals, "requires_verified_media": False}
