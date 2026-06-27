"""
VidyaSaarthi — pages/shared.py
Shared utilities: session state, CSS loader, header, bottom nav, processing pipeline.
Imported by every page.
"""

import streamlit as st
import os
import json

# ── Lazy imports ──────────────────────────────────────────────────────────────
def _get_tts():
    from speech.tts import text_to_speech
    return text_to_speech

def _get_llm():
    from llm import generate_and_parse
    return generate_and_parse

def _get_parser():
    from llm import parse_response
    return parse_response

def _get_visuals():
    from visuals.visual_manager import get_smart_visual, render_visual
    return get_smart_visual, render_visual

os.makedirs("temp", exist_ok=True)

# ── Default session state ─────────────────────────────────────────────────────
_DEFAULTS = {
    "query":         None,
    "parsed":        None,
    "audio_path":    None,
    "visual":        None,
    "autoplay":      False,
    "language":      "English",
    "text_language": "English",       # Language for written text (English or Hindi only)
    "audio_language": "English",      # Language for audio (English, Hindi, or Hinglish)
    "class_level":   8,
    "conversation_history": [],
    "input_mode":    "voice",        # "voice" or "text"
    "num_q":         5,
    "difficulty":    "Medium",
    "question_type": "MCQ",
    "quiz_active":   False,
    "quiz_data":     None,
    "q_idx":         0,
    "selected":      None,
    "score":         0,
    "history":       [],
    "fb_audio":      None,
    "fb_play":       False,
    "recent_topics": ["Photosynthesis", "TCP Handshake", "Newton's Laws", "Solar System",
                      "Cell Structure", "Human Heart", "Water Cycle"],
}

def init_state():
    if "lang" in st.query_params:
        st.session_state.language = st.query_params["lang"]
    if "text_lang" in st.query_params:
        val = st.query_params["text_lang"]
        if val in ("English", "Hindi"):
            st.session_state.text_language = val
    if "audio_lang" in st.query_params:
        val = st.query_params["audio_lang"]
        if val in ("English", "Hindi", "Hinglish"):
            st.session_state.audio_language = val
    if "class_lvl" in st.query_params:
        try:
            st.session_state.class_level = int(st.query_params["class_lvl"])
        except ValueError:
            pass
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── CSS loader ────────────────────────────────────────────────────────────────
def load_css():
    p = os.path.join("visuals", "style.css")
    if os.path.exists(p):
        st.markdown(f"<style>{open(p, encoding='utf-8').read()}</style>",
                    unsafe_allow_html=True)

# ── Response parser (delegates to llm module) ─────────────────────────────────
def parse_response(raw: str) -> dict:
    parser = _get_parser()
    return parser(raw, fallback_title=st.session_state.get("query", "Concept Detail"))

# ── Reset state for new query ─────────────────────────────────────────────────
def _reset():
    for k in ("parsed", "audio_path", "visual", "autoplay", "quiz_active",
              "quiz_data", "q_idx", "selected", "score", "history",
              "fb_audio", "fb_play"):
        st.session_state[k] = _DEFAULTS[k]

# ── Processing State Renderer ──────────────────────────────────────────────────
def render_processing_state(step: int, pct: int):
    """HTML renderer for the beautiful Processing State card."""
    step1_icon = "✓" if step > 1 else "⏳"
    step1_class = "completed" if step > 1 else "active"
    
    step2_icon = "✓" if step > 2 else ("⏳" if step == 2 else "○")
    step2_class = "completed" if step > 2 else ("active" if step == 2 else "pending")
    
    step3_icon = "✓" if step > 3 else ("⏳" if step == 3 else "○")
    step3_class = "completed" if step > 3 else ("active" if step == 3 else "pending")
    
    html = f"""<div class="processing-card"><div class="processing-icon-circle"><svg class="hourglass-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h12v6l-4 4 4 4v6H6v-6l4-4-4-4V2zm10 14.5L12 12.5l-4 4V20h8v-3.5zm-8-9l4 4 4-4V4H8v3.5z"/></svg></div><div class="processing-title">Creating explanation</div><div class="processing-steps"><div class="processing-step {step1_class}"><span class="step-icon">{step1_icon}</span><span class="step-label">Understanding your question</span></div><div class="processing-step {step2_class}"><span class="step-icon">{step2_icon}</span><span class="step-label">Generating visuals</span></div><div class="processing-step {step3_class}"><span class="step-icon">{step3_icon}</span><span class="step-label">Preparing voice reply</span></div></div><div class="processing-progress-container"><div class="processing-progress-bar-bg"><div class="processing-progress-bar" style="width: {pct}%;"></div></div><span class="processing-progress-pct">{pct}%</span></div></div>"""
    return html

# ── Process pipeline ──────────────────────────────────────────────────────────
def process(query: str, num_q: int = 5, difficulty: str = "Medium", q_type: str = "MCQ"):
    """Full pipeline: LLM → parse → TTS → Visual generation with dynamic status rendering."""
    st.session_state.query = query
    _reset()

    # Update recent topics
    title = query.strip().title()
    if title and title not in st.session_state.recent_topics:
        st.session_state.recent_topics = [title] + st.session_state.recent_topics[:6]

    text_lang = st.session_state.text_language
    audio_lang = st.session_state.audio_language

    generate_and_parse = _get_llm()
    text_to_speech    = _get_tts()
    get_smart_visual, _ = _get_visuals()

    status_placeholder = st.empty()
    
    # Step 1: Understanding question (30% progress)
    status_placeholder.markdown(render_processing_state(step=1, pct=30), unsafe_allow_html=True)

    audio_req = st.session_state.get("voice_enabled", True)

    if not st.session_state.conversation_history:
        @st.cache_data(show_spinner=False, ttl=3600) # Cache for 1 hour
        def _cached_generate_and_parse_v5(
            q: str, t_lang: str, a_lang: str, n_q: int, diff: str, q_t: str, c_lvl: int, a_req: bool
        ) -> dict:
            return generate_and_parse(
                q, text_language=t_lang, audio_language=a_lang,
                num_questions=n_q, difficulty=diff, question_type=q_t,
                class_level=c_lvl, conversation_history=None, audio_requested=a_req
            )
        data = _cached_generate_and_parse_v5(
            query, text_lang, audio_lang, num_q, difficulty, q_type,
            st.session_state.class_level, audio_req
        )
    else:
        # Don't cache when history is present to avoid cache misses and bloat
        data = generate_and_parse(
            query, text_language=text_lang, audio_language=audio_lang,
            num_questions=num_q, difficulty=difficulty, question_type=q_type,
            class_level=st.session_state.class_level, 
            conversation_history=st.session_state.conversation_history,
            audio_requested=audio_req
        )
    st.session_state.parsed = data
    
    # Append to conversation history (last 3 turns = 6 messages)
    st.session_state.conversation_history.append({"role": "user", "content": query})
    st.session_state.conversation_history.append({"role": "assistant", "content": "Explained topic: " + data.get("topic_title", "Concept Details")})
    if len(st.session_state.conversation_history) > 6:
        st.session_state.conversation_history = st.session_state.conversation_history[-6:]

    # Step 2: Generating visuals (65% progress)
    status_placeholder.markdown(render_processing_state(step=2, pct=65), unsafe_allow_html=True)
    
    if data.get("type") != "quiz":
        st.session_state.visual = get_smart_visual(
            data.get("visual", {}), 
            fallback_topic=data.get("topic_title", query)
        )
    else:
        # Quiz visual generation fallback
        quiz_topic = data.get("quiz_title", query)
        if quiz_topic.lower().startswith("quiz on"):
            quiz_topic = quiz_topic[7:].strip().strip("'\"")
        st.session_state.visual = get_smart_visual(
            None, 
            fallback_topic=quiz_topic
        )

    # Step 3: Preparing voice reply (90% progress)
    status_placeholder.markdown(render_processing_state(step=3, pct=90), unsafe_allow_html=True)

    if audio_req:
        if data.get("type") == "quiz":
            st.session_state.quiz_active = True
            st.session_state.quiz_data   = data
            qs    = data.get("questions", [])
            intro = data.get("intro_text", "Let's start the quiz!")
            if qs:
                intro += " " + qs[0].get("audio_script", "")
            st.session_state.audio_path = text_to_speech(intro, language=audio_lang)
            st.session_state.autoplay = True
        else:
            intro_text = data.get("audio_script") or data.get("notes_intro", "")
            if intro_text:
                st.session_state.audio_path = text_to_speech(intro_text, language=audio_lang)
                st.session_state.autoplay = True
    else:
        if data.get("type") == "quiz":
            st.session_state.quiz_active = True
            st.session_state.quiz_data   = data
        st.session_state.audio_path = None
        st.session_state.autoplay = False

    # Complete (100% progress)
    status_placeholder.markdown(render_processing_state(step=4, pct=100), unsafe_allow_html=True)
    import time
    time.sleep(0.8)
    status_placeholder.empty()

    # Auto-navigate to correct page
    if st.session_state.get("quiz_active"):
        st.switch_page("pages/pg_quiz.py")
    else:
        st.switch_page("pages/pg_notes.py")

# ── Audio helper ──────────────────────────────────────────────────────────────
def play(path, auto=False):
    if path and os.path.exists(path):
        st.audio(path, autoplay=auto)
        if auto:
            st.session_state.autoplay = False

# ══ TOP HEADER ════════════════════════════════════════════════════════════════
def render_header():
    """Render the fixed top header bar with custom logo, subtitle, language option, and floating elements."""
    # Floating background decorations
    floating_decorations_html = """
    <div class="floating-decorations">
        <span class="decor-item d1">📚</span>
        <span class="decor-item d2">🧪</span>
        <span class="decor-item d3">🌍</span>
        <span class="decor-item d4">⚛️</span>
    </div>
    """
    st.markdown(floating_decorations_html, unsafe_allow_html=True)
                                                                                                                                                                                                                                                                                            
    header_html = f"""
    <div class="sa-header">
        <div class="sa-header-left">
            <div class="sa-header-logo">🎓</div>
            <div class="sa-header-brand">
                <div class="sa-header-title">VidyaSaarthi</div>
                <div class="sa-header-sub">Where Knowledge Meets Innovation</div>
            </div>
        </div>
        <div class="sa-header-right">
            <span class="sa-header-icon">🔊</span>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    st.markdown('<div class="header-home-spacer"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 2, 8])
    with col1:
        st.page_link("pages/pg_home.py", label="Home", icon="🏠", use_container_width=True)
            
    with col2:
        with st.popover("⚙️ Settings", use_container_width=True):
            st.selectbox("🎓 Class Level", list(range(5, 11)), index=st.session_state.class_level-5, key="class_level")
            st.selectbox("📝 Text Language", ["English", "Hindi"], index=["English", "Hindi"].index(st.session_state.text_language), key="text_language")
            st.selectbox("🗣️ Audio Language", ["English", "Hindi", "Hinglish"], index=["English", "Hindi", "Hinglish"].index(st.session_state.audio_language), key="audio_language")
            
            # Add a voice toggle switch that we needed for the audio feature
            st.toggle("🔊 Voice Output", value=st.session_state.get("voice_enabled", True), key="voice_enabled")

# ══ SIDEBAR NAV BAR ════════════════════════════════════════════════════════════
_NAV_PAGES = [
    ("pages/pg_home.py",   "🏠", "Home"),
    ("pages/pg_notes.py",  "📚", "Notes"),
    ("pages/pg_quiz.py",   "🧠", "Quiz"),
    ("pages/pg_type.py",   "⌨️",  "Ask by Typing"),
]

def render_sidebar_nav(current_file: str):
    """Custom premium left sidebar navigation."""
    curr = os.path.normpath(current_file)
    
    with st.sidebar:
        # Title/Logo area in the sidebar
        st.markdown("""
        <div class="sidebar-brand">
            <span class="sidebar-logo">🎓</span>
            <div class="sidebar-brand-text">
                <div class="sidebar-title">VidyaSaarthi</div>
                <div class="sidebar-sub">Where Knowledge Meets Innovation</div>
            </div>
        </div>
        <div class="sidebar-divider"></div>
        """, unsafe_allow_html=True)
        
        # Navigation Links
        for page_path, emoji, label in _NAV_PAGES:
            is_active = curr.endswith(os.path.normpath(page_path).replace("/", os.sep))
            if is_active:
                st.markdown('<span class="sidebar-active-marker"></span>', unsafe_allow_html=True)
            st.page_link(page_path, label=label, icon=emoji, use_container_width=True)
        
        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
