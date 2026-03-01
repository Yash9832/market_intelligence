# response_formatter.py

import json
import matplotlib.pyplot as plt
import io
import base64

def format_response(result):
    """
    Formats the agent result into a structured dictionary.
    If result contains 'chart' images (as matplotlib figures), it encodes them as base64 strings.
    Otherwise returns the text result.
    """
    # If result is a dict with fig object for charts
    if isinstance(result, dict) and result.get("fig"):
        fig = result["fig"]
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return {
            "text": result.get("text", ""),
            "chart": f"data:image/png;base64,{img_b64}"
        }
    # Plain text or JSON-serializable structure
    try:
        # Attempt to parse JSON strings
        return json.loads(result)
    except (TypeError, ValueError):
        return {"text": str(result)}
