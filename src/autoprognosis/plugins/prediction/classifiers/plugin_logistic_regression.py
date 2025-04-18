# stdlib
from typing import Any, List, Optional

# third party
import pandas as pd
from sklearn.linear_model import LogisticRegression

# autoprognosis absolute
import autoprognosis.plugins.core.params as params
import autoprognosis.plugins.prediction.classifiers.base as base
import autoprognosis.utils.serialization as serialization
from autoprognosis.plugins.prediction.classifiers.helper_calibration import (
    calibrated_model,
)
from autoprognosis.utils.parallel import n_learner_jobs


class LogisticRegressionPlugin(base.ClassifierPlugin):
    """Classification plugin based on the Logistic Regression classifier.

    Method:
        Logistic regression is a linear model for classification rather than regression. In this model, the probabilities describing the possible outcomes of a single trial are modeled using a logistic function.

    Args:
        C: float
            Inverse of regularization strength; must be a positive float.
        solver: int index
            Algorithm to use in the optimization problem: [‘newton-cg’, ‘lbfgs’, ‘liblinear’, ‘sag’, ‘saga’]
        multi_class: int
            If the option chosen is ‘ovr’, then a binary problem is fit for each label. For ‘multinomial’ the loss minimised is the multinomial loss fit across the entire probability distribution, even when the data is binary. ‘multinomial’ is unavailable when solver=’liblinear’. ‘auto’ selects ‘ovr’ if the data is binary, or if solver=’liblinear’, and otherwise selects ‘multinomial’.
        class_weight: int index
            Weights associated with classes in the form {class_label: weight}. If not given, all classes are supposed to have weight one.
        max_iter: int
            Maximum number of iterations taken for the solvers to converge.
        penalty: str
            Specify the norm of the penalty:
        calibration: int
            Enable/disable calibration. 0: disabled, 1 : sigmoid, 2: isotonic.
        random_state: int, default 0
            Random seed


    Example:
        >>> from autoprognosis.plugins.prediction import Predictions
        >>> plugin = Predictions(category="classifiers").get("logistic_regression")
        >>> from sklearn.datasets import load_iris
        >>> X, y = load_iris(return_X_y=True)
        >>> plugin.fit_predict(X, y) # returns the probabilities for each class
    """

    solvers = ["newton-cg", "lbfgs", "sag", "saga"]
    classes = ["auto", "ovr", "multinomial"]
    weights = ["balanced", None]

    def __init__(
        self,
        C: float = 1.0,
        solver: int = 1,
        multi_class: int = 0,
        class_weight: int = 0,
        max_iter: int = 10000,
        penalty: str = "l2",
        calibration: int = 0,
        model: Any = None,
        hyperparam_search_iterations: Optional[int] = None,
        random_state: int = 0,
        n_jobs: int = n_learner_jobs(),
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if model is not None:
            self.model = model
            return

        if hyperparam_search_iterations:
            max_iter = int(hyperparam_search_iterations) * 100

        model = LogisticRegression(
            C=C,
            solver=LogisticRegressionPlugin.solvers[solver],
            multi_class=LogisticRegressionPlugin.classes[multi_class],
            class_weight=LogisticRegressionPlugin.weights[class_weight],
            penalty=penalty,
            max_iter=max_iter,
            random_state=random_state,
            n_jobs=n_jobs,
        )
        self.model = calibrated_model(model, calibration)

    @staticmethod
    def name() -> str:
        return "logistic_regression"

    @staticmethod
    def hyperparameter_space(*args: Any, **kwargs: Any) -> List[params.Params]:
        return [
            params.Float("C", 1e-3, 1e-2),
            params.Integer("solver", 0, len(LogisticRegressionPlugin.solvers) - 1),
            params.Integer("multi_class", 0, len(LogisticRegressionPlugin.classes) - 1),
            params.Integer(
                "class_weight", 0, len(LogisticRegressionPlugin.weights) - 1
            ),
        ]

    def _fit(
        self, X: pd.DataFrame, *args: Any, **kwargs: Any
    ) -> "LogisticRegressionPlugin":
        self.model.fit(X, *args, **kwargs)
        return self

    def _predict(self, X: pd.DataFrame, *args: Any, **kwargs: Any) -> pd.DataFrame:
        return self.model.predict(X, *args, **kwargs)

    def _predict_proba(
        self, X: pd.DataFrame, *args: Any, **kwargs: Any
    ) -> pd.DataFrame:
        return self.model.predict_proba(X, *args, **kwargs)

    def save(self) -> bytes:
        return serialization.save_model(self.model)

    @classmethod
    def load(cls, buff: bytes) -> "LogisticRegressionPlugin":
        model = serialization.load_model(buff)

        return cls(model=model)


plugin = LogisticRegressionPlugin
