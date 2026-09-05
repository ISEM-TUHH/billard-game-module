import pandas as pd
import json
from bson.objectid import ObjectId
from bson import json_util

from collections.abc import Mapping, Sequence
from typing import Any


def flatten_document(
    document: dict[str, Any],
    *,
    separator: str = ".",
    list_index_format: str = "[{}]",
) -> dict[str, Any]:

    flattened: dict[str, Any] = {}

    def add_value(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            # Preserve empty dictionaries as values.
            if not value:
                flattened[path] = {}
                return

            for key, nested_value in value.items():
                child_path = (
                    f"{path}{separator}{key}" if path else str(key)
                )
                add_value(nested_value, child_path)

        elif isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            # Preserve empty arrays as values.
            if not value:
                flattened[path] = []
                return

            for index, item in enumerate(value):
                indexed_path = (
                    f"{path}{list_index_format.format(index)}"
                    if path
                    else list_index_format.format(index)
                )
                add_value(item, indexed_path)

        else:
            flattened[path] = value

    for key, value in document.items():
        add_value(value, str(key))

    return flattened


def documents_to_dataframe(
    documents: list[dict[str, Any]],
    *,
    separator: str = ".",
    list_index_format: str = "[{}]",
) -> pd.DataFrame:
    """
    Convert a list of nested MongoDB documents into one-row-per-document
    pandas DataFrame.
    """

    flattened_documents = [
        flatten_document(
            document,
            separator=separator,
            list_index_format=list_index_format,
        )
        for document in documents
    ]

    return pd.DataFrame(flattened_documents)


def documents_to_excel(
    documents: list[dict[str, Any]],
    output_file,
    *,
    sheet_name: str = "data",
) -> pd.DataFrame:
    """
    Flatten MongoDB documents and write them to an Excel file.
    Returns the generated DataFrame.
    """

    dataframe = documents_to_dataframe(documents)
    dataframe.to_excel(output_file, index=False, sheet_name=sheet_name)
    return dataframe
