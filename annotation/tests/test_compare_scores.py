import uuid

import pytest

from annotation.schemas.tasks import (AgreementScoreComparingResult,
                                      AgreementScoreServiceResponse,
                                      TaskMetric)
from annotation.tasks.services import compare_agreement_scores

min_match_1 = 0.8
case_1 = [
    AgreementScoreServiceResponse(
        annotator_id=uuid.uuid4(),
        job_id=1,
        task_id=1,
        agreement_score=[
            {"task_id": 2, "agreement_score": 0.99},
            {"task_id": 3, "agreement_score": 0.81},
            {"task_id": 4, "agreement_score": 0.85},
        ],
    ),
    AgreementScoreServiceResponse(
        annotator_id=uuid.uuid4(),
        job_id=1,
        task_id=2,
        agreement_score=[
            {"task_id": 1, "agreement_score": 0.99},
            {"task_id": 4, "agreement_score": 0.89},
            {"task_id": 3, "agreement_score": 0.86},
        ],
    ),
    AgreementScoreServiceResponse(
        annotator_id=uuid.uuid4(),
        job_id=1,
        task_id=3,
        agreement_score=[
            {"task_id": 4, "agreement_score": 0.92},
            {"task_id": 2, "agreement_score": 0.86},
            {"task_id": 1, "agreement_score": 0.81},
        ],
    ),
    AgreementScoreServiceResponse(
        annotator_id=uuid.uuid4(),
        job_id=1,
        task_id=4,
        agreement_score=[
            {"task_id": 1, "agreement_score": 0.85},
            {"task_id": 2, "agreement_score": 0.89},
            {"task_id": 3, "agreement_score": 0.92},
        ],
    ),
]
case_1_result = AgreementScoreComparingResult(
    agreement_score_reached=True,
    task_metrics=[
        TaskMetric(task_from_id=1, task_to_id=2, metric_score=0.99),
        TaskMetric(task_from_id=1, task_to_id=3, metric_score=0.81),
        TaskMetric(task_from_id=1, task_to_id=4, metric_score=0.85),
        TaskMetric(task_from_id=2, task_to_id=3, metric_score=0.86),
        TaskMetric(task_from_id=2, task_to_id=4, metric_score=0.89),
        TaskMetric(task_from_id=3, task_to_id=4, metric_score=0.92),
    ],
)

min_match_2 = 0.99
case_2 = case_1.copy()
case_2_result = AgreementScoreComparingResult(
    agreement_score_reached=False,
    task_metrics=[
        TaskMetric(task_from_id=1, task_to_id=2, metric_score=0.99),
        TaskMetric(task_from_id=1, task_to_id=3, metric_score=0.81),
        TaskMetric(task_from_id=1, task_to_id=4, metric_score=0.85),
        TaskMetric(task_from_id=2, task_to_id=3, metric_score=0.86),
        TaskMetric(task_from_id=2, task_to_id=4, metric_score=0.89),
        TaskMetric(task_from_id=3, task_to_id=4, metric_score=0.92),
    ],
)


min_match_3 = 0.4
case_3 = [
    AgreementScoreServiceResponse(
        annotator_id=uuid.uuid4(),
        job_id=1,
        task_id=1,
        agreement_score=[{"task_id": 2, "agreement_score": 0.39}],
    ),
    AgreementScoreServiceResponse(
        annotator_id=uuid.uuid4(),
        job_id=1,
        task_id=2,
        agreement_score=[{"task_id": 1, "agreement_score": 0.39}],
    ),
]
case_3_result = AgreementScoreComparingResult(
    agreement_score_reached=False,
    task_metrics=[TaskMetric(task_from_id=1, task_to_id=2, metric_score=0.39)],
)


@pytest.mark.unittest
@pytest.mark.parametrize(
    ("agreement_score_response", "score_min_match", "expected_result"),
    (
        (case_1, min_match_1, case_1_result),
        (case_2, min_match_2, case_2_result),
        (case_3, min_match_3, case_3_result),
    ),
)
def test_compare_agreement_scores(
    agreement_score_response, score_min_match, expected_result
):
    assert (
        compare_agreement_scores(agreement_score_response, score_min_match)
        == expected_result
    )
