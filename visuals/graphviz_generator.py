"""
graphviz_generator.py
Generates process flows and classification trees using Python's Graphviz bindings.
Converts LLM JSON output to dynamic styled SVG diagrams.
"""

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

# Ensure Graphviz binary path is in environment PATH
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

load_dotenv()
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

_SYSTEM_PROMPT = """You are a smart school board visual designer.
Create a simple step-by-step process flowchart or classification tree for the given topic.

STRICTLY return a JSON object with this format (no markdown fences, no formatting outside of JSON):
{
  "title": "Descriptive title of the flow (e.g., Seed to Plant Growth)",
  "nodes": ["Step 1", "Step 2", "Step 3"],
  "edges": [
    ["Step 1", "Step 2"],
    ["Step 2", "Step 3"]
  ]
}

RULES:
1. Keep the number of nodes between 3 and 7.
2. Keep node labels short (2 to 4 words).
3. The nodes must represent sequential steps (processes) or categories (classification).
4. Edge pairs MUST exactly match node names defined in the "nodes" list.
5. All text must match the requested language/Hinglish instructions.
"""


def generate_graphviz_visual(topic: str, explanation: str, language: str = "Hinglish") -> str | None:
    """
    Calls LLM to generate diagram structure JSON and renders it via Graphviz to an SVG string.
    """
    try:
        user_msg = (
            f"Language: {language}\n"
            f"Topic: {topic}\n\n"
            f"Explanation context:\n{explanation[:500]}\n\n"
            f"Generate a simplified flowchart/classification JSON."
        )

        resp = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=600,
            temperature=0.2,
        )

        raw_json = resp.choices[0].message.content.strip()
        data = json.loads(raw_json)

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        title = data.get("title", topic)

        if not nodes:
            return None

        # Render graph using graphviz
        import graphviz
        
        dot = graphviz.Digraph(comment=title)
        
        # Configure layout variables for a clean school board aesthetic
        dot.attr(bgcolor='#0b1d33')
        dot.attr(rankdir='LR')  # Left-to-right flow
        dot.attr(splines='true')
        
        # Default node/edge styles
        dot.attr('node', shape='box', style='rounded,filled',
                 fillcolor='#0d2137', color='#00c8ff',
                 fontcolor='#ffffff', fontname='Helvetica,Arial,sans-serif',
                 penwidth='2.0', fontsize='12')
        
        dot.attr('edge', color='#00c8ff', arrowhead='normal',
                 penwidth='1.8', fontname='Helvetica,Arial,sans-serif',
                 fontsize='10', fontcolor='#80dfff')

        # Add nodes
        for node in nodes:
            dot.node(node, node)

        # Add edges (validating existence)
        for edge in edges:
            if len(edge) == 2 and edge[0] in nodes and edge[1] in nodes:
                dot.edge(edge[0], edge[1])

        # Render to SVG string
        svg_data = dot.pipe(format='svg').decode('utf-8')
        
        # Make the SVG responsive by scaling to 100% width and auto height
        svg_data = re.sub(r'width="[^"]+"', 'width="100%"', svg_data, count=1)
        svg_data = re.sub(r'height="[^"]+"', 'height="auto"', svg_data, count=1)

        # Wrap it in a styled dark container
        wrapped_html = f"""
        <div style="background:#0b1d33; padding:1.5rem; border-radius:16px; 
                    border:1px solid rgba(0,200,255,0.25); display:flex; 
                    flex-direction:column; align-items:center; justify-content:center;">
            <div style="color:#80dfff; font-size:1.15rem; font-weight:700; margin-bottom:1rem; text-align:center; font-family:system-ui,sans-serif;">
                {title}
            </div>
            <div style="width:100%; max-width:800px; display:flex; justify-content:center;">
                {svg_data}
            </div>
        </div>
        """
        return wrapped_html

    except Exception as e:
        print("[graphviz_generator] Error:", e)
        return None
