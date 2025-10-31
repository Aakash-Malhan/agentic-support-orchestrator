import os
import glob
from dataclasses import dataclass
from typing import List, Tuple

from sentence_transformers import SentenceTransformer
import faiss

try:
    from pinecone import Pinecone
    _HAS_PINECONE = True
except Exception:
    _HAS_PINECONE = False

@dataclass
class DocChunk:
    text: str
    meta: dict

class Retriever:
    def __init__(self, kb_path: str = "./kb", use_pinecone: bool | None = None,
                 pinecone_index: str | None = None, model_name: str = "all-MiniLM-L6-v2"):
        self.kb_path = kb_path
        self.model = SentenceTransformer(model_name)

        if use_pinecone is None:
            use_pinecone = bool(os.getenv("PINECONE_API_KEY")) and _HAS_PINECONE
        self.use_pinecone = use_pinecone
        self.pinecone_index = pinecone_index or os.getenv("PINECONE_INDEX", "agentic-support-kb")

        self.docs: List[DocChunk] = []
        self.embeddings = None
        self.index = None

        self._load_docs()
        self._build_index()

    def _load_docs(self):
        paths = glob.glob(os.path.join(self.kb_path, "**", "*"), recursive=True)
        for p in paths:
            if os.path.isdir(p):
                continue
            if any(p.endswith(ext) for ext in [".md", ".txt"]):
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                self.docs.append(DocChunk(text=text, meta={"path": p}))
        if not self.docs:
            self.docs.append(DocChunk(text="Default policy: returns allowed within 30 days.", meta={"path": "builtin"}))

    def _build_index(self):
        corpus = [d.text for d in self.docs]
        embs = self.model.encode(corpus, convert_to_numpy=True, show_progress_bar=False)
        dim = embs.shape[1]
        if self.use_pinecone:
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            existing = [i["name"] for i in pc.list_indexes()]
            if self.pinecone_index not in existing:
                pc.create_index(self.pinecone_index, dimension=dim, metric="cosine")
            self.pi = pc.Index(self.pinecone_index)
            vectors = [(f"doc-{i}", embs[i].tolist(), {"path": self.docs[i].meta["path"]}) for i in range(len(self.docs))]
            self.pi.upsert(vectors=vectors)
        else:
            self.index = faiss.IndexFlatIP(dim)
            faiss.normalize_L2(embs)
            self.embeddings = embs
            self.index.add(embs)

    def query(self, q: str, k: int = 4) -> List[Tuple[float, DocChunk]]:
        q_emb = self.model.encode([q], convert_to_numpy=True)
        faiss.normalize_L2(q_emb)
        if self.use_pinecone:
            res = self.pi.query(vector=q_emb[0].tolist(), top_k=k, include_metadata=True)
            out = []
            for m in res["matches"]:
                path = m["metadata"].get("path", "")
                doc = next((d for d in self.docs if d.meta.get("path") == path), None)
                if doc is None:
                    doc = DocChunk(text=f"Document from {path}", meta={"path": path})
                out.append((m["score"], doc))
            return out
        else:
            D, I = self.index.search(q_emb, k)
            out = []
            for score, idx in zip(D[0], I[0]):
                if idx == -1:
                    continue
                out.append((float(score), self.docs[idx]))
            return out
