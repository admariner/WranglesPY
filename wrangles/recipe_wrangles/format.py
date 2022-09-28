"""
Functions to re-format data
"""
import pandas as _pd
from .. import format as _format


def price_breaks(df: _pd.DataFrame, input: list, categoryLabel: str, valueLabel: str) -> _pd.DataFrame: # pragma: no cover
    """
    Rearrange price breaks
    """
    df = _pd.concat([df, _format.price_breaks(df[input], categoryLabel, valueLabel)], axis=1)
    return df


def remove_duplicates(df: _pd.DataFrame, input: str, output: str = None) -> _pd.DataFrame:
    """
    type: object
    description: Remove duplicates from a list. Preserves input order.
    additionalProperties: false
    required:
      - input
    properties:
      input:
        type: string
        description: Name of the input column
      output:
        type: string
        description: Name of the output column
    """
    # If user hasn't provided an output, overwrite input
    if output is None: output = input

    output_list = []
    for row in df[input].values.tolist():
        if isinstance(row, list):
            output_list.append(list(dict.fromkeys(row)))
        else:
            output_list.append(row)
    df[output] = output_list
    return df


def trim(df: _pd.DataFrame, input: str, output: str = None) -> _pd.DataFrame:
    """
    type: object
    description: Remove excess whitespace at the start and end of text.
    additionalProperties: false
    required:
      - input
    properties:
      input:
        type:
          - array
          - string
        description: Name of the input column
      output:
        type:
          - array
          - string
        description: Name of the output column
    """
    if output is None: output = input

    # If a string provided, convert to list
    if isinstance(output, str): output = [output]

    # Loop through and create uuid for all requested columns
    for input_column, output_column in zip(input, output):
        df[output_column] = df[input_column].str.strip()

    return df
    

def prefix(df: _pd.DataFrame, input: str, value: str, output: str = None) -> _pd.DataFrame:
  """
  type: object
    description: Add a prefix to a column
    additionalProperties: false
    required:
      - input
      - value
    properties:
      input:
        type:
          - string
        description: Name of the input column
      value:
        type:
          - string
        description: Prefix value to add
      output:
        type:
          - string
        description: (Optional) Name of the output column
  """
  if output is None:
    df[input] = value + df[input].astype(str)
  else:
    df[output] = value + df[input].astype(str)
  
  return df
  
def suffix(df: _pd.DataFrame, input: str, value: str, output: str = None) -> _pd.DataFrame:
  """
  type: object
    description: Add a suffix to a column
    additionalProperties: false
    required:
      - input
      - value
    properties:
      input:
        type:
          - string
        description: Name of the input column
      value:
        type:
          - string
        description: Suffix value to add
      output:
        type:
          - string
        description: (Optional) Name of the output column
  """
  if output is None:
    df[input] = df[input].astype(str) + value
  else:
    df[output] = df[input].astype(str) + value
  
  return df
  
def date_format(df: _pd.DataFrame, input: str, format: str, output: str = None) -> _pd.DataFrame:
    """
    type: object
    description: Format a date
    additionalProperties: false
    required:
      - input
      - format
    properties:
      input:
        type:
          - string
        description: Name of the input column
      output:
        type:
          - string
        description: Name of the output column
      format:
        type:
          - string
        description: String pattern to format date
    """
    # If output is not specified, overwrite input columns in place
    if output is None: output = input
    
    # convert the column to timestamp type and format date
    df[output] = _pd.to_datetime(df[input]).dt.strftime(format)
    
    return df
  
  