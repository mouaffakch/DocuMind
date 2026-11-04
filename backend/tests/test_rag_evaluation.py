import pytest
from scripts.evaluate_rag import RAGEvaluator, EvaluationSample, run_comparative_experiment


def test_rag_evaluator_metrics():
    retrieved = ["src/auth.py", "src/user.py", "src/main.py"]
    ground_truth = {"src/auth.py"}

    p_at_1 = RAGEvaluator.compute_precision_at_k(retrieved, ground_truth, k=1)
    assert p_at_1 == 1.0

    p_at_3 = RAGEvaluator.compute_precision_at_k(retrieved, ground_truth, k=3)
    assert round(p_at_3, 2) == 0.33

    recall = RAGEvaluator.compute_recall_at_k(retrieved, ground_truth, k=1)
    assert recall == 1.0

    mrr = RAGEvaluator.compute_mrr(retrieved, ground_truth)
    assert mrr == 1.0

    # Test when ground truth is at rank 2
    retrieved_offset = ["src/other.py", "src/auth.py"]
    mrr_offset = RAGEvaluator.compute_mrr(retrieved_offset, ground_truth)
    assert mrr_offset == 0.5


def test_faithfulness_and_citation_accuracy():
    context = ["def authenticate(token): return verify(token)"]
    grounded_answer = "La fonction authenticate vérifie le token."
    hallucinated_answer = "Cette fonction supprime tous les disques durs et configure le cluster Kubernetes extraterrestre."

    faith_high = RAGEvaluator.compute_faithfulness(grounded_answer, context)
    faith_low = RAGEvaluator.compute_faithfulness(hallucinated_answer, context)

    assert faith_high >= faith_low

    citations = [
        {"file_path": "src/auth.py", "start_line": 10, "end_line": 20},
        {"file_path": "non_existent.py", "start_line": 5, "end_line": 2},  # Invalid
    ]
    acc = RAGEvaluator.compute_citation_accuracy(citations, {"src/auth.py"})
    assert acc == 0.5


def test_run_comparative_experiment():
    results = run_comparative_experiment()
    assert "bm25" in results
    assert "dense" in results
    assert "hybrid" in results
    assert results["hybrid"].precision_at_k >= 0.5
    assert results["hybrid"].recall_at_k >= 0.5
