"""
visual_manager.py
Orchestrator for the school-focused visual system.

Priorities:
1. Educational Images (Wikimedia Commons)
2. Educational Infographics (HTML/CSS process cards)
3. Comparison Cards (HTML side-by-side comparative cards)
4. Timeline Cards (HTML vertical timeline cards)
5. Graphviz (Simple process flows and classification trees only)

Public API:
    get_smart_visual(topic, explanation, language) -> dict
    render_visual(visual_result)  [call inside Streamlit]
"""

import streamlit as st
import streamlit.components.v1 as components

from visuals.graphviz_generator import generate_graphviz_visual
from visuals.infographic_generator import (
    generate_educational_infographic,
    generate_comparison_cards,
    generate_timeline_cards
)
from visuals.wikimedia_fetcher import fetch_wikimedia_image


def classify_visual_type(topic: str, explanation: str) -> str:
    """
    Classifies the user query/topic based on keywords to select the best visual representation.
    """
    combined = (topic + " " + explanation[:250]).lower()

    # 1. Educational Image (Anatomy, Geography, Astronomy, Biology Objects)
    image_kws = [
        "heart", "brain", "cell", "solar system", "volcano", "skeleton", "map",
        "flower", "digestive", "anatomy", "geography", "astronomy", "biology",
        "lungs", "kidney", "liver", "eye", "ear", "skeleton", "bone", "leaf",
        "root", "seed", "fruit", "planet", "galaxy", "continent", "india"
    ]
    if any(kw in combined for kw in image_kws):
        return "educational_image"

    # 2. Comparison Cards (Difference, Compare, VS)
    compare_kws = ["difference", "compare", "vs", "versus", "antar", "fark", "tulna"]
    if any(kw in combined for kw in compare_kws):
        return "comparison_card"

    # 3. Timeline Cards (History, Timeline, Journey)
    timeline_kws = ["history", "timeline", "journey", "life of", "freedom movement", " struggle", "itihas"]
    if any(kw in combined for kw in timeline_kws):
        return "timeline"

    # 4. Infographic (Process, Cycle, Working, Steps)
    info_kws = ["cycle", "process", "working", "steps", "how does", "water cycle", "photosynthesis", "prakriya", "chakra"]
    if any(kw in combined for kw in info_kws):
        return "infographic"

    # 5. Graphviz (Simple flowcharts and classification trees)
    flow_kws = ["flow", "classification", "tree", "seed to", "food chain", "animal classification", "lifecycle"]
    if any(kw in combined for kw in flow_kws):
        return "graphviz"

    # Default to simple process diagram (Graphviz flowchart)
    return "graphviz"


def get_smart_visual(topic: str, explanation: str, language: str = "Hinglish") -> dict:
    """
    Retrieves the visual asset content based on classified category, cascading if generation fails.
    """
    vtype = classify_visual_type(topic, explanation)

    # ── 1. Educational Image ──────────────────────────────────────────────────
    if vtype == "educational_image":
        img = fetch_wikimedia_image(topic)
        if img:
            return {"type": "educational_image", "content": img, "label": "🖼️ Educational Diagram"}
        # Fallback if image not found
        vtype = "infographic"

    # ── 2. Educational Infographic ────────────────────────────────────────────
    if vtype == "infographic":
        html = generate_educational_infographic(topic, explanation, language)
        if html:
            return {"type": "infographic", "content": html, "label": "💡 Process Infographic"}
        vtype = "graphviz"

    # ── 3. Comparison Card ────────────────────────────────────────────────────
    if vtype == "comparison_card":
        html = generate_comparison_cards(topic, explanation, language)
        if html:
            return {"type": "comparison", "content": html, "label": "⚖️ Comparison Cards"}
        vtype = "graphviz"

    # ── 4. Timeline ───────────────────────────────────────────────────────────
    if vtype == "timeline":
        html = generate_timeline_cards(topic, explanation, language)
        if html:
            return {"type": "timeline", "content": html, "label": "⏳ Timeline Summary"}
        vtype = "graphviz"

    # ── 5. Graphviz (Process Flow / Classification Tree) ──────────────────────
    if vtype == "graphviz":
        svg = generate_graphviz_visual(topic, explanation, language)
        if svg:
            return {"type": "graphviz", "content": svg, "label": "📊 Concept flowchart"}

    # Final Fallback to Wikimedia search
    img = fetch_wikimedia_image(topic)
    if img:
        return {"type": "educational_image", "content": img, "label": "🖼️ Educational Diagram"}

    return {"type": "none", "content": None, "label": ""}


def render_visual(visual_result: dict):
    """
    Renders the visual result in Streamlit.
    """
    vtype   = visual_result.get("type")
    content = visual_result.get("content")
    label   = visual_result.get("label", "🖼️ Visual Learning Aid")

    if vtype == "none" or not content:
        st.info("🔍 No visual aid available for this topic.")
        return

    st.markdown(
        f'<div class="card-title" style="margin-bottom:0.8rem;">{label}</div>',
        unsafe_allow_html=True,
    )

    if vtype in ("infographic", "comparison", "timeline", "graphviz"):
        # HTML/CSS-based components
        height = 420
        if vtype == "comparison":
            height = 480
        elif vtype == "timeline":
            height = 500
        
        components.html(content, height=height, scrolling=True)

    elif vtype == "educational_image":
        img_url = content.get("image_url")
        title   = content.get("title", "")
        desc    = content.get("description", "")
        source  = content.get("source", "Wikimedia Commons")

        if img_url:
            st.image(img_url, use_container_width=True)
        st.markdown(
            f"""<div style="margin-top:0.7rem; padding:0.8rem 1rem;
                            background:rgba(0,200,255,0.05);
                            border-left:3px solid #00c8ff;
                            border-radius:8px;">
                  <div style="font-size:1rem; font-weight:700; color:#80dfff; font-family:system-ui,sans-serif;">{title}</div>
                  <div style="font-size:0.95rem; color:#a2c9dd; margin-top:0.3rem; line-height:1.6; font-family:system-ui,sans-serif;">{desc}</div>
                  <div style="font-size:0.75rem; color:#4a7a94; margin-top:0.4rem; font-family:system-ui,sans-serif;">📌 Source: {source}</div>
                </div>""",
            unsafe_allow_html=True,
        )
