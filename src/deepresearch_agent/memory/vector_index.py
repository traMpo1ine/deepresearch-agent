from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np


class NumpyVectorIndex:
    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self.ids: list[str] = []
        self.vectors = np.empty((0, dim), dtype=np.float32)

    def embed_text(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim, dtype=np.float32)
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector

    def add(self, item_id: str, text: str) -> None:
        vector = self.embed_text(text).reshape(1, self.dim)
        if item_id in self.ids:
            index = self.ids.index(item_id)
            self.vectors[index] = vector
            return
        self.ids.append(item_id)
        self.vectors = np.vstack([self.vectors, vector])

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        if not self.ids:
            return []
        query_vector = self.embed_text(query)
        scores = self.vectors @ query_vector
        order = np.argsort(scores)[::-1][:top_k]
        return [(self.ids[i], float(scores[i])) for i in order]

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, ids=np.array(self.ids), vectors=self.vectors, dim=self.dim)

    @classmethod
    def load(cls, path: str | Path) -> "NumpyVectorIndex":
        data = np.load(Path(path), allow_pickle=False)
        index = cls(dim=int(data["dim"]))
        index.ids = [str(item) for item in data["ids"].tolist()]
        index.vectors = data["vectors"].astype(np.float32)
        return index
