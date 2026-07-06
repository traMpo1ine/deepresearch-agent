from deepresearch_agent.memory.vector_index import NumpyVectorIndex


def test_vector_index_returns_most_similar_item() -> None:
    index = NumpyVectorIndex(dim=32)
    index.add("citation", "claim citation evidence verification")
    index.add("cooking", "recipe salt soup kitchen")

    results = index.search("evidence citation", top_k=1)

    assert results[0][0] == "citation"


def test_vector_index_save_load(tmp_path) -> None:
    path = tmp_path / "index.npz"
    index = NumpyVectorIndex(dim=16)
    index.add("a", "agent memory citation")

    index.save(path)
    loaded = NumpyVectorIndex.load(path)

    assert loaded.search("citation", top_k=1)[0][0] == "a"
