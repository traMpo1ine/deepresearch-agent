from deepresearch_agent.compression import TextRankCompressor
from deepresearch_agent.schemas import Evidence


def test_compression_preserves_quotes() -> None:
    evidence = [
        Evidence(
            task_id="task",
            source_id="source",
            title="Citation",
            text="Noise sentence. The cited quote must stay available. More background.",
            quote="The cited quote must stay available.",
        )
    ]

    context = TextRankCompressor().compress_evidence("citation quote", evidence, max_sentences=1)

    assert any(sentence.text == "The cited quote must stay available." for sentence in context.sentences)
