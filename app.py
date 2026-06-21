import streamlit as st
import os
from speech.sst import speech_to_text
from speech.tts import text_to_speech
from llm import generate_response
from visuals.visual_manager import get_visual
from streamlit_mic_recorder import mic_recorder

os.makedirs("temp", exist_ok=True)

st.set_page_config(
    page_title="AI Teaching Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Smart Board CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

html, body, * { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }

.stApp {
    background: linear-gradient(150deg, #0a1628 0%, #0d2137 55%, #0a1628 100%);
    min-height: 100vh;
}

/* Header */
.app-header {
    text-align: center;
    padding: 1.8rem 0 1rem;
}
.app-header h1 {
    font-size: 2.8rem;
    font-weight: 900;
    margin: 0;
    background: linear-gradient(90deg, #00c8ff, #80dfff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.app-header p {
    font-size: 1.05rem;
    color: #6a9db8;
    margin: 0.3rem 0 0;
    letter-spacing: 1px;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(0,200,255,0.18);
    border-radius: 16px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.1rem;
}
.card-title {
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #00c8ff;
    margin-bottom: 0.8rem;
}
.query-box {
    font-size: 1.55rem;
    font-weight: 600;
    color: #80dfff;
    background: rgba(0,200,255,0.08);
    border-left: 4px solid #00c8ff;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    line-height: 1.6;
}
.response-box {
    font-size: 1.3rem;
    line-height: 1.95;
    color: #dff1fa;
    white-space: pre-wrap;
}
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,200,255,0.3), transparent);
    margin: 0.8rem 0 1.2rem;
}

/* Language selector */
.stSelectbox label {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #00c8ff !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 2px solid rgba(0,200,255,0.35) !important;
    border-radius: 12px !important;
    font-size: 1.15rem !important;
    color: #dff1fa !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 5px !important;
    border: 1px solid rgba(0,200,255,0.15) !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #6a9db8 !important;
    border-radius: 10px !important;
    padding: 0.65rem 2.5rem !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,200,255,0.18) !important;
    color: #00c8ff !important;
}

/* Text area */
.stTextArea label {
    font-size: 1.15rem !important;
    color: #80aec4 !important;
    font-weight: 600 !important;
}
.stTextArea textarea {
    font-size: 1.3rem !important;
    background: rgba(255,255,255,0.06) !important;
    color: #dff1fa !important;
    border: 2px solid rgba(0,200,255,0.25) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    min-height: 100px !important;
}
.stTextArea textarea:focus {
    border-color: #00c8ff !important;
    box-shadow: 0 0 0 3px rgba(0,200,255,0.15) !important;
}

/* Buttons */
.stButton > button {
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 12px !important;
    border: none !important;
    width: 100% !important;
    letter-spacing: 0.5px !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
}

/* Audio */
audio { width: 100% !important; border-radius: 10px !important; }

/* Image caption */
.stImage > div > img { border-radius: 14px !important; }
.visual-desc {
    font-size: 1.05rem;
    color: #80aec4;
    line-height: 1.7;
    margin-top: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🎓 AI Teaching Assistant</h1>
  <p>HARYANA GOVERNMENT SCHOOLS &nbsp;•&nbsp; SMART BOARD EDITION</p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────────
for k, v in {"query": None, "response": None, "audio_file": None,
              "visual": None, "show_audio": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Language Selector ──────────────────────────────────────────────────────────
col_lang, col_gap = st.columns([1, 3])
with col_lang:
    language = st.selectbox("🌐 Output Language", ["Hinglish", "Hindi", "English"])

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Helper: process query ──────────────────────────────────────────────────────
def process(query: str):
    st.session_state.query = query
    st.session_state.show_audio = False
    with st.spinner("🤖 Generating response..."):
        st.session_state.response = generate_response(query, language=language)
    with st.spinner("🔊 Generating audio..."):
        st.session_state.audio_file = text_to_speech(
            st.session_state.response, language=language
        )
    st.session_state.show_audio = True
    with st.spinner("🖼️ Finding visual aid..."):
        st.session_state.visual = get_visual(query)

# ── Input Tabs ─────────────────────────────────────────────────────────────────
tab_text, tab_voice = st.tabs(["⌨️  Text Input", "🎤  Voice Input"])

with tab_text:
    st.markdown("")
    query_text = st.text_area(
        "Type your teaching command",
        placeholder='e.g. "Photosynthesis samjhao" or "Water cycle quiz banao"',
        height=110
    )
    if st.button("🚀  Generate Response", key="btn_text"):
        if query_text.strip():
            process(query_text.strip())
        else:
            st.warning("Please type a command first.")

with tab_voice:
    st.markdown("")
    st.markdown('<p style="color:#80aec4; font-size:1.1rem;">Click <b>Start Recording</b>, speak your command, then click <b>Stop</b>.</p>', unsafe_allow_html=True)
    audio = mic_recorder(
        start_prompt="🎤  Start Recording",
        stop_prompt="⏹  Stop Recording",
        just_once=True,
        key="mic"
    )
    if audio:
        audio_path = "temp/input.webm"
        with open(audio_path, "wb") as f:
            f.write(audio["bytes"])
        with st.spinner("📝 Transcribing..."):
            transcribed = speech_to_text(audio_path)
        if not transcribed.startswith("["):
            process(transcribed)
        else:
            st.warning(transcribed)

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.query:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Teacher Command
    st.markdown('<div class="card"><div class="card-title">🗣️ Teacher Command</div>'
                f'<div class="query-box">{st.session_state.query}</div></div>',
                unsafe_allow_html=True)

    # AI Response
    if st.session_state.response:
        st.markdown('<div class="card"><div class="card-title">🤖 AI Response</div>'
                    f'<div class="response-box">{st.session_state.response}</div></div>',
                    unsafe_allow_html=True)

    # Audio Controls
    if st.session_state.audio_file:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="color:#00c8ff; font-size:0.9rem; '
                    'letter-spacing:2px; text-transform:uppercase;">🔊 Audio Controls</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️  Play Response", key="play"):
                st.session_state.show_audio = True
        with c2:
            if st.button("⏹  Stop Audio", key="stop"):
                st.session_state.show_audio = False

        if st.session_state.show_audio:
            st.audio(st.session_state.audio_file, autoplay=True)

    # Visual Aid
    visual = st.session_state.visual
    if visual:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title" style="color:#00c8ff; font-size:0.9rem; '
                    f'letter-spacing:2px; text-transform:uppercase;">🖼️ Visual Aid — {visual["title"]}</div>',
                    unsafe_allow_html=True)
        v_col1, v_col2 = st.columns([1, 2])
        with v_col1:
            if visual.get("image_url"):
                st.image(visual["image_url"], use_container_width=True)
        with v_col2:
            st.markdown(f'<div class="visual-desc">{visual["description"]}</div>',
                        unsafe_allow_html=True)