from agents import Orchestrator
from rag import Retriever

CASES = [
    ("Where is my order A123?", "order_status"),
    ("I want a refund for order B456, it arrived damaged.", "return_refund"),
    ("How long does standard shipping take?", "policy_question"),
]

def run():
    retr = Retriever(kb_path="./kb")
    orch = Orchestrator(retr)
    ok = 0
    for q, expected in CASES:
        res = orch.step(q)
        got = res["meta"]["intent"]["category"]
        conf = res["meta"]["confidence"]
        print(f"{q} → {got} (conf={conf:.2f})")
        ok += int(got == expected)
    print(f"Intent accuracy (toy): {ok}/{len(CASES)}")

if __name__ == "__main__":
    run()
