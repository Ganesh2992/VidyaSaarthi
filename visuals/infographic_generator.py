"""
infographic_generator.py
Generates educational infographic components (processes, comparison cards, timelines)
as responsive HTML blocks styled for the smart board dark theme.
Uses JSON-first pattern: LLM outputs structured data, Python builds HTML.
"""

import json
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ──────────────────────────────────────────────────────────────────────────────
# 1. EDUCATIONAL INFOGRAPHICS (Processes / Cycles)
# ──────────────────────────────────────────────────────────────────────────────

_INFOGRAPHIC_SYSTEM_PROMPT = """You are an expert school textbook visual designer.
Create a step-by-step process or cycle breakdown for the given topic in JSON format.

STRICT JSON FORMAT:
{
  "title": "Water Cycle Process (Jal Chakra)",
  "intro": "How water moves from Earth to the sky and back.",
  "steps": [
    {
      "step_num": 1,
      "title": "Evaporation (Vashpikaran)",
      "desc": "The Sun heats up water in lakes, turning it into vapor."
    },
    {
      "step_num": 2,
      "title": "Condensation (Sanganak)",
      "desc": "Water vapor cools down high in the air to form clouds."
    }
  ]
}

RULES:
1. ONLY return a valid JSON object. No conversational text or markdown code blocks.
2. Limit to 3-6 clear, logical steps. Keep explanations simple for Class 5-12.
3. Keep descriptions concise (15-25 words each).
4. Match language requested (Hinglish, Hindi, English).
"""

def generate_educational_infographic(topic: str, explanation: str, language: str = "Hinglish") -> str | None:
    try:
        user_msg = f"Language: {language}\nTopic: {topic}\nContext:\n{explanation[:500]}"
        resp = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _INFOGRAPHIC_SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        data = json.loads(resp.choices[0].message.content.strip())
        
        title = data.get("title", topic)
        intro = data.get("intro", "")
        steps = data.get("steps", [])

        if not steps:
            return None

        # Build clean HTML
        steps_html = ""
        for s in steps:
            num = s.get("step_num", "")
            step_title = s.get("title", "")
            desc = s.get("desc", "")
            steps_html += f"""
            <div style="display:flex; gap:1.2rem; align-items:flex-start; background:#0d2137; 
                        border-radius:12px; padding:1.2rem; border:1px solid rgba(0,200,255,0.15); 
                        margin-bottom:1rem; box-shadow:0 4px 10px rgba(0,0,0,0.15);">
                <div style="background:#00c8ff; color:#0b1d33; font-weight:bold; font-size:1.15rem; 
                            border-radius:50%; width:36px; height:36px; display:flex; 
                            justify-content:center; align-items:center; flex-shrink:0; 
                            box-shadow: 0 0 10px rgba(0,200,255,0.3);">
                    {num}
                </div>
                <div style="flex:1;">
                    <h4 style="color:#80dfff; margin:0 0 0.4rem 0; font-size:1.15rem; font-family:system-ui,sans-serif;">{step_title}</h4>
                    <p style="color:#dff1fa; margin:0; font-size:1rem; line-height:1.6; font-family:system-ui,sans-serif;">{desc}</p>
                </div>
            </div>
            """

        wrapped = f"""
        <div style="background:#0b1d33; padding:1.5rem; border-radius:16px; 
                    border:1px solid rgba(0,200,255,0.25); font-family:system-ui, sans-serif;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
            <h3 style="color:#00c8ff; margin:0 0 0.4rem 0; font-size:1.45rem;">💡 {title}</h3>
            <p style="color:#a2c9dd; margin:0 0 1.5rem 0; font-size:1.05rem; line-height:1.5;">{intro}</p>
            <div>
                {steps_html}
            </div>
        </div>
        """
        return wrapped
    except Exception as e:
        print("[infographic_generator] Infographic error:", e)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# 2. COMPARISON CARDS
# ──────────────────────────────────────────────────────────────────────────────

_COMPARISON_SYSTEM_PROMPT = """You are an expert school textbook designer.
Compare two topics/concepts side-by-side in JSON format.

STRICT JSON FORMAT:
{
  "title": "Herbivores vs Carnivores",
  "cards": [
    {
      "title": "Herbivores (Shakahari)",
      "points": [
        "Eat plants and fruits.",
        "Flat, broad teeth for grinding grass.",
        "Examples: Cow, Deer, Goat."
      ]
    },
    {
      "title": "Carnivores (Mansahari)",
      "points": [
        "Eat other animals and meat.",
        "Sharp, pointed teeth to tear flesh.",
        "Examples: Lion, Tiger, Leopard."
      ]
    }
  ]
}

RULES:
1. ONLY return a valid JSON object. No markdown, no fences.
2. Produce exactly 2 comparative items in the "cards" list.
3. Limit to 3-5 distinct bullet points per card.
4. Keep comparison points aligned and clear for school students.
5. Match language requested (Hinglish, Hindi, English).
"""

def generate_comparison_cards(topic: str, explanation: str, language: str = "Hinglish") -> str | None:
    try:
        user_msg = f"Language: {language}\nTopic: {topic}\nContext:\n{explanation[:500]}"
        resp = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _COMPARISON_SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        data = json.loads(resp.choices[0].message.content.strip())
        
        title = data.get("title", topic)
        cards = data.get("cards", [])

        if len(cards) < 2:
            return None

        # Build two side-by-side cards
        cards_html = ""
        for card in cards:
            c_title = card.get("title", "")
            points = card.get("points", [])
            points_list = "".join([f'<li style="margin-bottom:0.7rem;">{p}</li>' for p in points])
            
            cards_html += f"""
            <div style="flex:1; min-width:280px; background:#0d2137; border-radius:12px; 
                        padding:1.3rem; border:1px solid rgba(0,200,255,0.15); 
                        display:flex; flex-direction:column; box-shadow:0 4px 12px rgba(0,0,0,0.15);">
                <h4 style="color:#00c8ff; font-size:1.3rem; margin:0 0 1.2rem 0; 
                           padding-bottom:0.6rem; border-bottom:2px solid rgba(0,200,255,0.25); 
                           text-align:center; font-family:system-ui,sans-serif;">
                    {c_title}
                </h4>
                <ul style="padding-left:1.2rem; margin:0; color:#dff1fa; font-size:1.05rem; 
                           line-height:1.65; font-family:system-ui,sans-serif;">
                    {points_list}
                </ul>
            </div>
            """

        wrapped = f"""
        <div style="background:#0b1d33; padding:1.5rem; border-radius:16px; 
                    border:1px solid rgba(0,200,255,0.25); font-family:system-ui, sans-serif;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
            <h3 style="color:#00c8ff; margin:0 0 1.5rem 0; font-size:1.45rem; text-align:center;">⚖️ {title}</h3>
            <div style="display:flex; gap:1.5rem; flex-wrap:wrap; justify-content:center;">
                {cards_html}
            </div>
        </div>
        """
        return wrapped
    except Exception as e:
        print("[infographic_generator] Comparison card error:", e)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# 3. TIMELINE CARDS
# ──────────────────────────────────────────────────────────────────────────────

_TIMELINE_SYSTEM_PROMPT = """You are an expert history textbook illustrator.
Create a historical or process timeline in JSON format.

STRICT JSON FORMAT:
{
  "title": "Life of Mahatma Gandhi",
  "events": [
    {
      "time": "1869",
      "event": "Born in Porbandar, Gujarat."
    },
    {
      "time": "1915",
      "event": "Returned to India from South Africa to join the freedom movement."
    },
    {
      "time": "1947",
      "event": "India achieved Independence from British rule."
    }
  ]
}

RULES:
1. ONLY return a valid JSON object. No markdown, no fences.
2. Limit to 3-6 significant chronological events.
3. Keep event summaries simple and educational (10-20 words).
4. Match language requested (Hinglish, Hindi, English).
"""

def generate_timeline_cards(topic: str, explanation: str, language: str = "Hinglish") -> str | None:
    try:
        user_msg = f"Language: {language}\nTopic: {topic}\nContext:\n{explanation[:500]}"
        resp = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _TIMELINE_SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        data = json.loads(resp.choices[0].message.content.strip())
        
        title = data.get("title", topic)
        events = data.get("events", [])

        if not events:
            return None

        # Build vertical timeline
        events_html = ""
        for i, ev in enumerate(events):
            time = ev.get("time", "")
            desc = ev.get("event", "")
            events_html += f"""
            <div style="position:relative; margin-bottom:1.5rem;">
                <!-- Timeline Dot -->
                <div style="position:absolute; left:-29px; top:6px; width:12px; height:12px; 
                            border-radius:50%; background:#00c8ff; border:2px solid #0b1d33;
                            box-shadow: 0 0 8px #00c8ff;"></div>
                <div style="background:#0d2137; border-radius:12px; padding:1.2rem; 
                            border:1px solid rgba(0,200,255,0.15); box-shadow:0 4px 10px rgba(0,0,0,0.15);">
                    <span style="display:inline-block; font-weight:bold; color:#00c8ff; 
                                 font-size:1.15rem; margin-bottom:0.4rem; font-family:system-ui,sans-serif;">
                        📅 {time}
                    </span>
                    <p style="color:#dff1fa; margin:0; font-size:1.05rem; line-height:1.55; font-family:system-ui,sans-serif;">
                        {desc}
                    </p>
                </div>
            </div>
            """

        wrapped = f"""
        <div style="background:#0b1d33; padding:1.5rem; border-radius:16px; 
                    border:1px solid rgba(0,200,255,0.25); font-family:system-ui, sans-serif;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
            <h3 style="color:#00c8ff; margin:0 0 1.8rem 0; font-size:1.45rem;">⏳ {title}</h3>
            <div style="position:relative; padding-left:1.5rem; border-left:3px solid rgba(0,200,255,0.25); 
                        margin-left:1rem; display:flex; flex-direction:column;">
                {events_html}
            </div>
        </div>
        """
        return wrapped
    except Exception as e:
        print("[infographic_generator] Timeline error:", e)
        return None
