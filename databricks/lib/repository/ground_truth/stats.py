from typing import Any, Dict, List, Optional, Sequence, Tuple

import lib.spark_helper.predictions as predictions_helper
from lib.spark_helper.ground_truth import GroundTruthFileStorage
from lib.spark_helper.predictions import Prediction
from sklearn.metrics import accuracy_score, precision_score, recall_score
from tabulate import tabulate


def replace_values(
    input_list: List[Any], replacements: Dict[Any, Any]
) -> List[Any]:
    return [replacements.get(item, item) for item in input_list]


def convert_classes_to_binary(
    ground_truth: List[str], predicted: List[str]
) -> Tuple[List[int], List[int]]:
    replacements = {"Compliant": 0, "Minor Issues": 1, "Red Flag": 1}
    return replace_values(ground_truth, replacements), replace_values(
        predicted, replacements
    )


def get_annotation_from_revision_by_category(
    revision: Dict[str, List[Dict[str, List[Dict[str, str]]]]], category: str
) -> Optional[str]:

    for annotation in revision["pages"][0]["objs"]:
        if annotation.get("category") == category:
            return annotation.get("text")
    return None


class StatsCalculator:
    def __init__(
        self,
        temporary_storage: predictions_helper.TemporaryStorage,
        ground_truth_storage: GroundTruthFileStorage,
    ) -> None:
        self.temporary_storage = temporary_storage
        self.ground_truth_storage = ground_truth_storage
        self.predictions: List[Prediction] = []

    def get_predictions(self, job_ids: Sequence[int]) -> None:

        self.predictions = []
        for job_id in job_ids:
            self.predictions.extend(
                self.temporary_storage.load_predictions(job_id=job_id)
            )

    def get_predictions_by_job_id(self, job_id: int) -> List[Prediction]:
        return [
            prediction
            for prediction in self.predictions
            if prediction.job_id == job_id
        ]

    def calculate_accuracy_from_predictions(
        self, predictions: List[Prediction]
    ) -> Any:

        ground_truth, predicted = self.generate_prediction_and_truth_lists(
            predictions
        )
        if not ground_truth or not predicted:
            return None

        ground_truth_binary, predicted_binary = convert_classes_to_binary(
            ground_truth, predicted
        )

        return accuracy_score(ground_truth_binary, predicted_binary)

    def calculate_precision_from_predictions(
        self, predictions: List[Prediction]
    ) -> Any:

        ground_truth, predicted = self.generate_prediction_and_truth_lists(
            predictions
        )
        if not ground_truth or not predicted:
            return None

        ground_truth_binary, predicted_binary = convert_classes_to_binary(
            ground_truth, predicted
        )

        return precision_score(
            ground_truth_binary, predicted_binary, zero_division=0
        )

    def calculate_recall_from_predictions(
        self, predictions: List[Prediction]
    ) -> Any:

        ground_truth, predicted = self.generate_prediction_and_truth_lists(
            predictions
        )
        if not ground_truth or not predicted:
            return None

        ground_truth_binary, predicted_binary = convert_classes_to_binary(
            ground_truth, predicted
        )

        return recall_score(
            ground_truth_binary, predicted_binary, zero_division=0
        )

    def generate_prediction_and_truth_lists(
        self, predictions: List[Prediction]
    ) -> Tuple[List[str], List[str]]:

        predicted: List[str] = []
        ground_truth: List[str] = []
        for prediction in predictions:
            try:
                revision = self.ground_truth_storage.read_revision_file(
                    file_id=prediction.file_id,
                    revision_id=(
                        prediction.ground_truth_revision_id
                        if prediction.ground_truth_revision_id
                        else ""
                    ),
                )
            except Exception:
                continue
            for category in prediction.prediction_result:
                annotation = get_annotation_from_revision_by_category(
                    revision, category
                )
                if not annotation:
                    continue
                predicted.append(prediction.prediction_result[category])
                ground_truth.append(annotation)

        return ground_truth, predicted

    def calculate_jobs_accuracy(self, job_ids: List[int]) -> Dict[int, Any]:

        accuracy = {}
        for job_id in job_ids:
            job_predictions = self.get_predictions_by_job_id(job_id)
            accuracy[job_id] = self.calculate_accuracy_from_predictions(
                job_predictions
            )

        return accuracy

    def calculate_files_accuracy(
        self, job_ids: List[int]
    ) -> Dict[int, Dict[int, Dict[str, Any]]]:

        files_accuracy: Dict[int, Dict[int, Dict[str, Any]]] = {}
        for job_id in job_ids:
            job_predictions = self.get_predictions_by_job_id(job_id)
            for prediction in job_predictions:
                file_accuracy = self.calculate_accuracy_from_predictions(
                    [prediction]
                )
                if not file_accuracy:
                    continue

                if prediction.file_id not in files_accuracy:
                    files_accuracy[prediction.file_id] = {}
                files_accuracy[prediction.file_id][prediction.job_id] = {}
                files_accuracy[prediction.file_id][prediction.job_id][
                    "accuracy"
                ] = file_accuracy
                files_accuracy[prediction.file_id][prediction.job_id][
                    "categories"
                ] = {}
                try:
                    revision = self.ground_truth_storage.read_revision_file(
                        file_id=prediction.file_id,
                        revision_id=(
                            prediction.ground_truth_revision_id
                            if prediction.ground_truth_revision_id
                            else ""
                        ),
                    )
                except Exception:
                    continue
                for category in prediction.prediction_result:
                    annotation = get_annotation_from_revision_by_category(
                        revision, category
                    )
                    if not annotation:
                        continue
                    predicted = prediction.prediction_result[category]
                    files_accuracy[prediction.file_id][prediction.job_id][
                        "categories"
                    ][category] = int(predicted == annotation)

        return files_accuracy

    def get_accuracy_rows(
        self, job_ids: List[int], include_files: bool, include_categories: bool
    ) -> List[List[Any]]:

        jobs_accuracy = self.calculate_jobs_accuracy(job_ids)

        rows: List[List[Any]] = []
        rows.append(
            ["accuracy"] + [jobs_accuracy[job_id] for job_id in job_ids]
        )

        if not include_files:
            return rows

        files_accuracy = self.calculate_files_accuracy(job_ids)
        for file_id in files_accuracy:
            row = ["- " + str(file_id)]
            for job_id in job_ids:
                row.append(files_accuracy[file_id][job_id]["accuracy"])
            rows.append(row)

            if include_categories:
                for category in files_accuracy[file_id][job_id]["categories"]:
                    row = ["-- " + category]
                    for job_id in job_ids:
                        row.append(
                            files_accuracy[file_id][job_id]["categories"][
                                category
                            ]
                        )
                    rows.append(row)

        return rows

    def calculate_jobs_precision(self, job_ids: List[int]) -> Dict[int, Any]:

        precision = {}
        for job_id in job_ids:
            job_predictions = self.get_predictions_by_job_id(job_id)
            precision[job_id] = self.calculate_precision_from_predictions(
                job_predictions
            )

        return precision

    def calculate_jobs_recall(self, job_ids: List[int]) -> Dict[int, Any]:

        recall = {}
        for job_id in job_ids:
            job_predictions = self.get_predictions_by_job_id(job_id)
            recall[job_id] = self.calculate_recall_from_predictions(
                job_predictions
            )

        return recall

    def calculate_files_precision(
        self, job_ids: List[int]
    ) -> Dict[int, Dict[int, Any]]:

        files_precision: Dict[int, Dict[int, Optional[float]]] = {}
        for job_id in job_ids:
            job_predictions = self.get_predictions_by_job_id(job_id)

            for prediction in job_predictions:
                precision = self.calculate_precision_from_predictions(
                    [prediction]
                )
                if not precision:
                    continue

                if prediction.file_id not in files_precision:
                    files_precision[prediction.file_id] = {}

                files_precision[prediction.file_id][
                    prediction.job_id
                ] = precision

        return files_precision

    def calculate_files_recall(
        self, job_ids: List[int]
    ) -> Dict[int, Dict[int, Any]]:

        files_recall: Dict[int, Dict[int, Optional[float]]] = {}
        for job_id in job_ids:
            job_predictions = self.get_predictions_by_job_id(job_id)

            for prediction in job_predictions:
                recall = self.calculate_recall_from_predictions([prediction])
                if not recall:
                    continue

                if prediction.file_id not in files_recall:
                    files_recall[prediction.file_id] = {}

                files_recall[prediction.file_id][prediction.job_id] = recall

        return files_recall

    def get_precision_rows(
        self, job_ids: List[int], include_files: bool
    ) -> List[List[Any]]:

        jobs_precision = self.calculate_jobs_precision(job_ids)
        files_precision = self.calculate_files_precision(job_ids)

        rows: List[List[Any]] = []
        rows.append(
            ["precision"] + [jobs_precision[job_id] for job_id in job_ids]
        )

        if not include_files:
            return rows

        for file_id in files_precision:
            row = ["- " + str(file_id)]
            for job_id in job_ids:
                row.append(files_precision[file_id][job_id])
            rows.append(row)

        return rows

    def get_recall_rows(
        self, job_ids: List[int], include_files: bool
    ) -> List[List[Any]]:

        jobs_recall = self.calculate_jobs_recall(job_ids)
        files_recall = self.calculate_files_recall(job_ids)

        rows: List[List[Any]] = []
        rows.append(["recall"] + [jobs_recall[job_id] for job_id in job_ids])

        if not include_files:
            return rows

        for file_id in files_recall:
            row = ["- " + str(file_id)]
            for job_id in job_ids:
                row.append(files_recall[file_id][job_id])
            rows.append(row)

        return rows

    def get_precision_recall_rows(
        self, job_ids: List[int], include_files: bool
    ) -> List[List[Any]]:

        rows: List[List[Any]] = []
        rows.extend(self.get_precision_rows(job_ids, include_files))
        rows.extend(self.get_recall_rows(job_ids, include_files))

        return rows

    def calculate_stats_by_category(
        self, job_ids: List[int]
    ) -> Dict[str, Dict[int, Dict[str, Any]]]:

        stats: Dict[str, Dict[int, Dict[str, Any]]] = {}
        for job_id in job_ids:
            job_predictions = self.get_predictions_by_job_id(job_id)

            for prediction in job_predictions:
                try:
                    revision = self.ground_truth_storage.read_revision_file(
                        file_id=prediction.file_id,
                        revision_id=(
                            prediction.ground_truth_revision_id
                            if prediction.ground_truth_revision_id
                            else ""
                        ),
                    )
                except Exception:
                    continue
                for category in prediction.prediction_result:
                    if category not in stats:
                        stats[category] = {}
                    if job_id not in stats[category]:
                        stats[category][job_id] = {
                            "ground_truth": [],
                            "predicted": [],
                        }

                    annotation = get_annotation_from_revision_by_category(
                        revision, category
                    )
                    if not annotation:
                        continue

                    stats[category][job_id]["ground_truth"].append(annotation)
                    stats[category][job_id]["predicted"].append(
                        prediction.prediction_result[category]
                    )

        for category in stats:
            for job_id in stats[category]:
                ground_truth = stats[category][job_id]["ground_truth"]
                predicted = stats[category][job_id]["predicted"]

                ground_truth, predicted = convert_classes_to_binary(
                    ground_truth, predicted
                )

                stats[category][job_id]["precision"] = precision_score(
                    ground_truth, predicted, zero_division=0
                )

                stats[category][job_id]["recall"] = recall_score(
                    ground_truth, predicted, zero_division=0
                )

                stats[category][job_id]["accuracy"] = accuracy_score(
                    ground_truth, predicted
                )

        return stats

    def get_category_rows(self, job_ids: List[int]) -> List[List[Any]]:

        stats = self.calculate_stats_by_category(job_ids)
        rows = []

        rows.extend(self.get_precision_rows(job_ids, include_files=False))
        for category in stats:
            row = ["- " + category]
            for job_id in job_ids:
                row.append(stats[category][job_id]["precision"])

            rows.append(row)

        rows.extend(self.get_recall_rows(job_ids, include_files=False))
        for category in stats:
            row = ["- " + category]
            for job_id in job_ids:
                row.append(stats[category][job_id]["recall"])

            rows.append(row)

        rows.extend(
            self.get_accuracy_rows(
                job_ids, include_files=False, include_categories=False
            )
        )
        for category in stats:
            row = ["- " + category]
            for job_id in job_ids:
                row.append(stats[category][job_id]["accuracy"])

            rows.append(row)

        return rows

    def avg_summary_by_jobs(self, job_ids: List[int]) -> None:

        self.get_predictions(job_ids)

        table_rows: List[List[Any]] = []
        table_rows.append(
            ["job_id"] + [str(job_id) for job_id in job_ids]
        )  # header row
        table_rows.extend(
            self.get_precision_recall_rows(
                job_ids,
                include_files=False,
            )
        )
        table_rows.extend(
            self.get_accuracy_rows(
                job_ids, include_files=False, include_categories=False
            )
        )

        print(
            tabulate(
                table_rows,
                headers="firstrow",
                tablefmt="simple_grid",
                floatfmt=".2f",
            )
        )

    def avg_category_by_jobs(self, job_ids: List[int]) -> None:

        self.get_predictions(job_ids)

        table_rows: List[List[Any]] = []
        table_rows.append(
            ["job_id"] + [str(job_id) for job_id in job_ids]
        )  # header row
        table_rows.extend(self.get_category_rows(job_ids))

        print(
            tabulate(
                table_rows,
                headers="firstrow",
                tablefmt="simple_grid",
                floatfmt=".2f",
            )
        )

    def avg_file_by_jobs(self, job_ids: List[int]) -> None:

        self.get_predictions(job_ids)

        table_rows: List[List[Any]] = []
        table_rows.append(
            ["job_id"] + [str(job_id) for job_id in job_ids]
        )  # header row
        table_rows.extend(
            self.get_precision_recall_rows(
                job_ids,
                include_files=True,
            )
        )
        table_rows.extend(
            self.get_accuracy_rows(
                job_ids, include_files=True, include_categories=False
            )
        )

        print(
            tabulate(
                table_rows,
                headers="firstrow",
                tablefmt="simple_grid",
                floatfmt=".2f",
            )
        )

    def avg_file_and_category_by_jobs(self, job_ids: List[int]) -> None:

        self.get_predictions(job_ids)

        table_rows: List[List[Any]] = []
        table_rows.append(
            ["job_id"] + [str(job_id) for job_id in job_ids]
        )  # header row
        table_rows.extend(
            self.get_precision_recall_rows(job_ids, include_files=True)
        )
        table_rows.extend(
            self.get_accuracy_rows(
                job_ids, include_files=True, include_categories=True
            )
        )

        print(
            tabulate(
                table_rows,
                headers="firstrow",
                tablefmt="simple_grid",
                floatfmt=".2f",
            )
        )
