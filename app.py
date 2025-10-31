import os
import json
import gradio as gr

from rag import Retriever
from agents import Orchestrator

# --- Ensure sample KB exists ---
os.makedirs("kb", exist_ok=True)
if not any(name.endswith((".md", ".txt")) for name in os.listdir("kb")):
    with open("kb/returns_policy.md", "w", encoding="utf-8") as f:
        f.write("# Returns & Refunds Policy\n- Items can be returned within 30 days if unused and in original packaging.\n")
    with open("kb/shipping_policy.md", "w", encoding="utf-8") as f:
        f.write("# Shipping Policy\n- Standard shipping: 3–5 business days. Expedited: 1–2 business days.\n")
    with open("kb/troubleshooting.md", "w", encoding="utf-8") as f:
        f.write("# Troubleshooting\n- Tracking may take up to 24h to refresh. Try power cycle for electronics.\n")

diag = {}
try:
    retriever = Retriever(kb_path="./kb")
    diag["retriever"] = "ok"
except Exception as e:
    retriever = None
    diag["retriever"] = f"error: {e}"

try:
    orchestrator = Orchestrator(retriever) if retriever else None
    diag["orchestrator"] = "ok" if orchestrator else "skipped (retriever init failed)"
except Exception as e:
    orchestrator = None
    diag["orchestrator"] = f"error: {e}"

def respond(message, history):
    if not orchestrator:
        return (
            "Startup error.\nDiagnostics: " + json.dumps(diag) +
            "\nHINT: Is GEMINI_API_KEY set as a Secret and Space restarted?"
        )
    try:
        result = orchestrator.step(message)
        meta = result.get("meta", {})
        meta_str = (
            f"\n\n---\n**Model:** {meta.get('model', os.getenv('MODEL_NAME', 'gemini-2.0-flash'))}"
            f"\n**Intent:** {meta.get('intent')}"
            f"\n**Confidence:** {float(meta.get('confidence', 0.0)):.2f}"
            f"\n**Escalate:** {meta.get('escalate')}"
            f"\n**Citations:** {meta.get('citations')}"
        )
        if meta.get("action_result"):
            meta_str += f"\n**Action Result:** `{json.dumps(meta['action_result'])}`"
        return result["text"] + meta_str
    except Exception as e:
        return f"Unhandled exception in respond(): {e}"

def export_audit():
    if not orchestrator:
        return json.dumps(diag, indent=2)
    return orchestrator.export_audit()

def diagnostics():
    return json.dumps({
        "HAS_GEMINI_KEY": bool(os.getenv("GEMINI_API_KEY")),
        "MODEL_NAME_ENV": os.getenv("MODEL_NAME", None),
        "Notes": "If MODEL_NAME not set, code auto-picks a working flash model (prefers gemini-2.0-flash).",
        **diag
    }, indent=2)

with gr.Blocks(title="Agentic Support Orchestrator") as demo:
    gr.Markdown("# Agentic AI Customer Support Orchestrator\nGemini 2.0 Flash (auto-fallback) + FAISS | CPU-only")
    with gr.Tabs():
        with gr.Tab("Customer Chat"):
            gr.ChatInterface(
                fn=respond,
                title="Support Assistant",
                chatbot=gr.Chatbot(height=420),
                textbox=gr.Textbox(placeholder="Ask about orders, returns, shipping, troubleshooting..."),
            )
        with gr.Tab("Admin / QA"):
            out = gr.Textbox(label="Audit Log (JSON)", lines=22)
            gr.Button("Export Audit").click(export_audit, None, out)
        with gr.Tab("Diagnostics"):
            diag_box = gr.Textbox(label="Startup diagnostics", lines=18, interactive=False)
            gr.Button("Refresh").click(diagnostics, None, diag_box)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", show_api=False)
