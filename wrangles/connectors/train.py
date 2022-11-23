import logging as _logging
import pandas as _pd
from ..train import train as _train


class classify():
    def write(df: _pd.DataFrame, columns: list = None, name: str = None, model_id: str = None) -> None:
        """
        Train a new or existing classify wrangle

        :param df: Dataframe to be written to a file
        :param model_id: Model to be updated
        """
        _logging.info(": Training Classify Wrangle")

        # Select only specific columns if user requests them
        if columns is not None: df = df[columns]

        _train.classify(df.values.tolist(), name, model_id)


class extract():
    def write(df: _pd.DataFrame, columns: list = None, name: str = None, model_id: str = None) -> None:
        """
        Train a new or existing extract wrangle

        :param df: Dataframe to be written to a file
        :param model_id: Model to be updated
        """
        _logging.info(f": Training Extract Wrangle")

        # Select only specific columns if user requests them
        if columns is not None: df = df[columns]

        _train.extract(df.values.tolist(), name, model_id)


class standardize():
    def write(df: _pd.DataFrame, columns: list = None, name: str = None, model_id: str = None) -> None:
        """
        Train a new or existing standardize wrangle

        :param df: Dataframe to be written to a file
        :param model_id: Model to be updated
        """
        _logging.info(f": Training Standardize Wrangle")

        # Select only specific columns if user requests them
        if columns is not None: df = df[columns]

        _train.standardize(df.values.tolist(), name, model_id)
