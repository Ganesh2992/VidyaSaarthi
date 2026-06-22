import streamlit as st
import os
import json
from speech.stt import speech_to_text
from speech.tts import text_to_speech
from llm import generate_response
from visuals.visual_manager import get_smart_visual, render_visual
from audiorecorder import audiorecorder

os.makedirs("temp", exist_ok=True)

st.set_page_config(
    page_title="AI Teaching Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load Smart Board CSS ──────────────────────────────────────────────────────
css_path = os.path.join("visuals", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🎓 AI Teaching Assistant</h1>
  <p>HARYANA GOVERNMENT SCHOOLS &nbsp;•&nbsp; SMART BOARD EDITION</p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
_DEFAULTS = {
    "query": None,
    "response_parsed": None,
    "audio_file": None,
    "visual_result": None,       # dict from get_smart_visual()
    "show_audio": False,
    # Quiz state
    "quiz_active": False,
    "quiz_data": None,
    "current_q_idx": 0,
    "selected_option": None,
    "quiz_score": 0,
    "quiz_history": [],
    "quiz_feedback_audio": None,
    "quiz_feedback_play_key": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helper: Robust JSON parser ────────────────────────────────────────────────
def parse_llm_response(raw: str) -> dict:
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())
    except Exception as e:
        print("JSON parse error:", e)
        return {
            "type": "explanation",
            "topic_title": "Concept Explanation",
            "explanation_text": raw,
            "analogy_title": "Real-Life Example",
            "analogy_text": "Is concept ko humare aas-paas ki zindagi se samajhte hain.",
            "key_points": [
                "Topic ko dhyan se samjho.",
                "Real-life examples bahut helpful hote hain.",
                "Koi bhi doubt ho toh poochho.",
            ],
            "audio_script": raw,
        }

# ── Helper: Reset all output state ───────────────────────────────────────────
def reset_output_state():
    st.session_state.response_parsed = None
    st.session_state.audio_file = None
    st.session_state.visual_result = None
    st.session_state.show_audio = False
    st.session_state.quiz_active = False
    st.session_state.quiz_data = None
    st.session_state.current_q_idx = 0
    st.session_state.selected_option = None
    st.session_state.quiz_score = 0
    st.session_state.quiz_history = []
    st.session_state.quiz_feedback_audio = None
    st.session_state.quiz_feedback_play_key = None

# ── Helper: Process a query ───────────────────────────────────────────────────
def process(query: str, language: str):
    st.session_state.query = query
    reset_output_state()

    with st.spinner("🤖 Generating response..."):
        raw_resp = generate_response(query, language=language)
        parsed = parse_llm_response(raw_resp)
        st.session_state.response_parsed = parsed

    if parsed.get("type") == "quiz":
        st.session_state.quiz_active = True
        st.session_state.quiz_data = parsed

        intro_text = parsed.get("intro_text", "Chalo bacho, ek quiz khelte hain!")
        questions = parsed.get("questions", [])
        if questions:
            intro_text += " " + questions[0].get("audio_script", "")

        with st.spinner("🔊 Generating quiz announcement..."):
            st.session_state.audio_file = text_to_speech(intro_text, language=language)
        st.session_state.show_audio = True

    else:
        # Generate TTS audio
        audio_text = parsed.get("audio_script", parsed.get("explanation_text", ""))
        with st.spinner("🔊 Generating explanation audio..."):
            st.session_state.audio_file = text_to_speech(audio_text, language=language)
        st.session_state.show_audio = True

        # Generate smart visual (Mermaid / Infographic / Wikimedia)
        topic = parsed.get("topic_title", query)
        explanation = parsed.get("explanation_text", "")
        with st.spinner("🎨 Generating visual learning aid..."):
            st.session_state.visual_result = get_smart_visual(topic, explanation, language)

# ── Language Selector ─────────────────────────────────────────────────────────
col_lang, col_gap = st.columns([1, 3])
with col_lang:
    language = st.selectbox("🌐 Output Language", ["Hinglish", "Hindi", "English"])

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Input Tabs ────────────────────────────────────────────────────────────────
tab_text, tab_voice = st.tabs(["⌨️  Text Input", "🎤  Voice Input"])

with tab_text:
    st.markdown("")
    query_text = st.text_area(
        "Type your teaching command",
        placeholder='e.g. "Photosynthesis samjhao" or "TCP vs UDP explain karo"',
        height=110,
        key="teacher_query_textarea",
    )
    if st.button("🚀  Generate Response", key="btn_text"):
        if query_text.strip():
            process(query_text.strip(), language)
        else:
            st.warning("Please type a command first.")

with tab_voice:
    st.markdown("")
    st.markdown(
        '<p style="color:#80aec4; font-size:1.15rem; font-weight:600;">'
        "Use the recorder below to speak your command:</p>",
        unsafe_allow_html=True,
    )
    audio = audiorecorder("🎤 Start Recording", "⏹ Stop Recording")

    if len(audio) > 0:
        audio_path = "temp/input.wav"
        audio.export(audio_path, format="wav")
        st.audio(audio.export().read())

        with st.spinner("📝 Transcribing..."):
            transcribed = speech_to_text(audio_path)

        if transcribed.startswith("["):
            st.warning(transcribed)
        else:
            st.success(f"📝 Heard: *{transcribed}*")
            process(transcribed, language)

# ── Results & Smart Board ─────────────────────────────────────────────────────
if st.session_state.query:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── CASE 1: Active Interactive Quiz ───────────────────────────────────────
    if st.session_state.quiz_active and st.session_state.quiz_data:
        quiz = st.session_state.quiz_data
        questions = quiz.get("questions", [])
        q_idx = st.session_state.current_q_idx

        # Play intro audio once at q_idx == 0
        if q_idx == 0 and st.session_state.audio_file and st.session_state.show_audio:
            st.audio(st.session_state.audio_file, autoplay=True)
            st.session_state.show_audio = False

        if q_idx < len(questions):
            q = questions[q_idx]

            st.markdown(
                f'<div class="card-title" style="font-size:1.1rem; color:#00c8ff;">'
                f'📝 Interactive Quiz — {quiz.get("quiz_title", "Concept Check")}</div>',
                unsafe_allow_html=True,
            )

            # Score dots
            dots_html = "".join(
                [f'<div class="score-dot {s}"></div>' for s in st.session_state.quiz_history]
                + ['<div class="score-dot"></div>'] * (len(questions) - len(st.session_state.quiz_history))
            )
            st.markdown(
                f'<div class="scoreboard">{dots_html}'
                f'<span style="color:#6a9db8; font-size:0.85rem; margin-left:0.5rem;">'
                f'SCORE: {st.session_state.quiz_score}/{len(questions)}</span></div>',
                unsafe_allow_html=True,
            )

            # Question card
            st.markdown(
                f"""<div class="quiz-question-card">
                    <div class="quiz-question-num">Question {q_idx + 1} of {len(questions)}</div>
                    <div class="quiz-question-text">{q.get("question_text", "")}</div>
                </div>""",
                unsafe_allow_html=True,
            )

            options = q.get("options", {})
            correct_opt = q.get("correct_option", "A")

            if st.session_state.selected_option is None:
                # Selection mode
                cols = st.columns(2)
                for i, (key, val) in enumerate(options.items()):
                    with cols[i % 2]:
                        if st.button(f"{key}: {val}", key=f"opt_btn_{q_idx}_{key}", use_container_width=True):
                            st.session_state.selected_option = key
                            is_correct = key == correct_opt
                            if is_correct:
                                st.session_state.quiz_score += 1
                                st.session_state.quiz_history.append("correct")
                                feedback_text = "Arey waah! Bilkul sahi jawaab!"
                            else:
                                st.session_state.quiz_history.append("incorrect")
                                feedback_text = f"Oh ho! Yeh galat hai. Sahi jawaab hai {correct_opt}."
                            verbal = f"{feedback_text} {q.get('explanation', '')}"
                            fb_audio = text_to_speech(verbal, language=language)
                            st.session_state.quiz_feedback_audio = fb_audio
                            st.session_state.quiz_feedback_play_key = fb_audio
                            st.rerun()
            else:
                # Feedback mode
                sel = st.session_state.selected_option
                cols = st.columns(2)
                for i, (key, val) in enumerate(options.items()):
                    with cols[i % 2]:
                        if key == correct_opt:
                            box_cls = ind_cls = "correct"
                        elif key == sel:
                            box_cls = ind_cls = "incorrect"
                        else:
                            box_cls = ind_cls = "neutral"
                        st.markdown(
                            f"""<div class="option-box {box_cls}">
                                <span class="option-indicator {ind_cls}">{key}</span>
                                <span>{val}</span>
                            </div>""",
                            unsafe_allow_html=True,
                        )

                is_right = sel == correct_opt
                fb_color = "#2ecc71" if is_right else "#e74c3c"
                fb_head = "🎉 Sahi Jawaab!" if is_right else "❌ Galat Jawaab!"
                st.markdown(
                    f"""<div class="card" style="border-color:{fb_color}; background:rgba(255,255,255,0.02);">
                        <div class="card-title" style="color:{fb_color};">{fb_head}</div>
                        <div style="font-size:1.2rem; color:#dff1fa; font-weight:600; margin-bottom:0.5rem;">
                            Sahi Option: {correct_opt}
                        </div>
                        <div style="font-size:1.15rem; color:#a2c9dd; line-height:1.6;">
                            {q.get("explanation", "")}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                fb_audio = st.session_state.quiz_feedback_audio
                play_key = st.session_state.quiz_feedback_play_key
                if fb_audio and play_key:
                    st.audio(fb_audio, autoplay=True)
                    st.session_state.quiz_feedback_play_key = None

                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button("🔊 Replay Feedback Audio", key=f"replay_{q_idx}"):
                        if fb_audio:
                            st.audio(fb_audio, autoplay=True)
                with c2:
                    btn_label = "Next Question ➡️" if q_idx < len(questions) - 1 else "Finish Quiz 🏁"
                    if st.button(btn_label, key=f"next_q_{q_idx}"):
                        st.session_state.selected_option = None
                        st.session_state.quiz_feedback_audio = None
                        st.session_state.quiz_feedback_play_key = None
                        st.session_state.current_q_idx += 1
                        if st.session_state.current_q_idx < len(questions):
                            next_script = questions[st.session_state.current_q_idx].get("audio_script", "")
                            st.session_state.audio_file = text_to_speech(next_script, language=language)
                            st.session_state.show_audio = True
                        else:
                            st.session_state.quiz_active = False
                        st.rerun()

    # ── CASE 2: Quiz Completed ────────────────────────────────────────────────
    elif (
        not st.session_state.quiz_active
        and st.session_state.quiz_data
        and st.session_state.current_q_idx >= len(st.session_state.quiz_data.get("questions", []))
    ):
        quiz = st.session_state.quiz_data
        questions = quiz.get("questions", [])
        total_q = len(questions)
        score = st.session_state.quiz_score

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            f"""<div class="quiz-finished-card">
                <div class="card-title" style="color:#00c8ff; font-size:1.1rem;">🏆 Quiz Completed!</div>
                <div class="quiz-finished-score">{score} / {total_q}</div>
                <div class="quiz-desc">
                    Bacho, aapne <b>{score}</b> out of <b>{total_q}</b> correct answers diye hain!
                    {"Bahut hi shandar performance! Double stars! 🌟🌟" if score == total_q
                     else "Acha try kiya bacho! Agli baar aur badhiya karenge! 👍"}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        celebration = f"Quiz khatam bacho! Aapka score hai {score} out of {total_q}. "
        celebration += (
            "Arey waah, aapne toh saare answers sahi diye! Bahut badhiya."
            if score == total_q
            else "Bahut acha try kiya! Kuch sawaal galat hue par koi baat nahi, hum dobara seekhenge."
        )
        st.audio(text_to_speech(celebration, language=language), autoplay=True)

        if st.button("🔄 Restart Quiz", key="restart_quiz"):
            st.session_state.current_q_idx = 0
            st.session_state.selected_option = None
            st.session_state.quiz_score = 0
            st.session_state.quiz_history = []
            st.session_state.quiz_feedback_audio = None
            st.session_state.quiz_feedback_play_key = None
            st.session_state.quiz_active = True
            first_script = questions[0].get("audio_script", "") if questions else ""
            st.session_state.audio_file = text_to_speech(first_script, language=language)
            st.session_state.show_audio = True
            st.rerun()

    # ── CASE 3: Concept Explanation + Smart Visual ────────────────────────────
    elif st.session_state.response_parsed:
        parsed = st.session_state.response_parsed
        topic = parsed.get("topic_title", "Concept")

        # ── Section A: AI Explanation (full width) ────────────────────────────
        st.markdown(
            f'<div class="card-title">🗣️ Concept Explanation — {topic}</div>',
            unsafe_allow_html=True,
        )

        # Explanation text as Markdown (bold, lists render correctly)
        st.markdown(parsed.get("explanation_text", ""))

        # Analogy card
        analogy_title = parsed.get("analogy_title", "")
        analogy_text = parsed.get("analogy_text", "")
        if analogy_title and analogy_text:
            st.markdown(
                f"""<div class="analogy-card">
                    <div class="analogy-title">💡 Analogy: {analogy_title}</div>
                    <div class="analogy-text">{analogy_text}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Key points
        key_points = parsed.get("key_points", [])
        if key_points:
            items_html = "".join(
                [f'<div class="key-point-item">{pt}</div>' for pt in key_points]
            )
            st.markdown(
                f"""<div class="key-points-card">
                    <div class="key-points-title">📝 Key Takeaways (Yaad Rakhne Wali Baatein)</div>
                    {items_html}
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ── Section B: Visual Learning Aid (full width) ───────────────────────
        visual_result = st.session_state.visual_result
        if visual_result:
            st.markdown(
                '<div style="background:rgba(0,200,255,0.04); border:1px solid rgba(0,200,255,0.2); '
                'border-radius:16px; padding:1.2rem 1.5rem; margin-bottom:1rem;">',
                unsafe_allow_html=True,
            )
            render_visual(visual_result)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ── Section C: Voice Controls ─────────────────────────────────────────
        if st.session_state.audio_file:
            st.markdown(
                '<div class="card-title" style="color:#00c8ff; font-size:0.9rem; '
                'letter-spacing:2px; text-transform:uppercase;">🔊 Voice Controls</div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("▶️ Repeat Explanation Audio", key="play_exp"):
                    st.session_state.show_audio = True
            with c2:
                if st.button("⏹ Stop Audio", key="stop_exp"):
                    st.session_state.show_audio = False

            if st.session_state.show_audio:
                st.audio(st.session_state.audio_file, autoplay=True)