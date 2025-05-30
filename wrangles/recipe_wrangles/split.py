"""
Split a single column to multiple columns
"""
# Rename List to _list to be able to use function name list without clashing
from typing import Union as _Union, List as _list
import pandas as _pd
from .. import format as _format
import json as _json
import itertools as _itertools
from ..utils import (
    wildcard_expansion_dict as _wildcard_expansion_dict,
    get_nested_function as _get_nested_function
)

def dictionary(
    df: _pd.DataFrame,
    input: _Union[str, int, _list],
    output: _Union[str, _list] = None,
    default: dict = {}
) -> _pd.DataFrame:
    """
    type: object
    description: |-
      Split one or more dictionaries into columns.
      The dictionary keys will be returned as the new column headers.
      If the dictionaries contain overlapping values, the last value will be returned.
    additionalProperties: false
    required:
      - input
    properties:
      input:
        type: 
          - string
          - integer
          - array
        description: |-
          Name or lists of the column(s) containing dictionaries to be split.
          If providing multiple dictionaries and the dictionaries
          contain overlapping values, the last value will be returned.
      output:
        type: 
          - string
          - array
        description: |-
          (Optional) Subset of keys to extract from the dictionary.
          If not provided, all keys will be returned.
          Columns can be renamed with the following syntax:
          output:
            - key1: new_column_name1
            - key2: new_column_name2
      default:
        type: object
        description: >-
          Provide a set of default headings and values
          if they are not found within the input
    """ 
    # Ensure input is passed as a list
    if not isinstance(input, _list):
        input = [input]

    def _parse_dict_or_json(val):
        if isinstance(val, dict):
            return val.items()
        elif isinstance(val, str) and val.startswith('{') and val.endswith('}'):
            try:
                return _json.loads(val).items()
            except:
                pass
        raise ValueError(f'{val} is not a valid Dictionary') from None
        

    # Generate new columns for each key in the dictionary
    df_temp = _pd.DataFrame([
        dict(_itertools.chain.from_iterable(_parse_dict_or_json(d) for d in ([default] + row.tolist())))
        for row in df[input].values
    ])

    # If user has defined how they'd like the output columns
    if output is not None:
        # Ensure output is a list
        if not isinstance(output, _list):
            output = [output]

        # Convert output to a dict of
        # {"in_col": "out_col", "unchanged": "unchanged"}
        # and rename as required
        output = dict(
            _itertools.chain.from_iterable(
                [
                    x.items() if isinstance(x, dict)
                    else {x: x}.items()
                    for x in output
                ]
            )
        )
        # Expand wildcard and regex defined columns to match the actual columns
        output = _wildcard_expansion_dict(df_temp.columns, output)
        df_temp = df_temp.rename(columns=output)

        # Return only the named output columns
        df_temp = df_temp[output.values()]

    df[df_temp.columns] = df_temp.values

    return df

    
def list(df: _pd.DataFrame, input: _Union[str, int], output: _Union[str, _list]) -> _pd.DataFrame:
    """
    type: object
    description: Split a list in a single column to multiple columns.
    additionalProperties: false
    required:
      - input
      - output
    properties:
      input:
        type:
          - string
          - int
        description: Name of the column to be split
      output:
        type:
          - string
          - array
        description: >-
          Name of column(s) for the results.
          If providing a single column, use a wildcard (*)
          to indicate a incrementing integer
    """
    # Ensure rows are lists even if they are JSON strings
    results = [
        row if isinstance(row, _list) else _json.loads(row)
        for row in df[input].values
    ]
    # If column is empty, return early
    if len(results) == 0:
        return df
    # Generate results and pad to a consistent length
    # as long as the max length
    max_len = max([len(x) for x in results])
    results = [
        x + [''] * (max_len - len(x))
        for x in results
    ]

    # Handle wildcard cases and column assignment
    if (isinstance(output, str) and '*' in output) or (isinstance(output, _list) and len(output) == 1 and '*' in output[0]):
        # Use the wildcard pattern for generating output headers
        wildcard_template = output if isinstance(output, str) else output[0]
        output_headers = [wildcard_template.replace('*', str(i)) for i in range(1, len(results[0]) + 1)]
        df[output_headers] = results
    else:
        # Direct assignment for single column
        df[output] = results

    return df


def text(
    df: _pd.DataFrame,
    input: str,
    output: _Union[str, _list] = None,
    char: str = ',',
    pad: bool = None,
    element: _Union[int, str] = None,
    inclusive: bool = False
) -> _pd.DataFrame:
    """
    type: object
    description: Split a string to multiple columns or a list.
    additionalProperties: false
    required:
      - input
    properties:
      input:
        type: string
        description: Name of the column to be split
      output:
        type:
          - string
          - array
        description: |-
          Name of the output column(s)
          If a single column is provided,
          the results will be returned as a list
          If multiple columns are listed,
          the results will be separated into the columns.
          If omitted, will overwrite the input.
      char:
        type: string
        description: |-
          Set the character(s) to split on.
          Default comma (,)
          Can also prefix with "regex:" to split on a pattern.
      pad:
        type: boolean
        description: >-
          Choose whether to pad to ensure a consistent length.
          Default true if outputting to columns, false for lists.
      element:
        type: 
          - integer
          - string
        description: >-
          Select a specific element or range after splitting
          using slicing syntax. e.g. 0, ":5", "5:", "2:8:2"
      inclusive:
        type: boolean
        description: >-
          If true, include the split character in the output.
          Default False
    """
    # Ensure only a single input column is specified
    if isinstance(input, _list):
        if len(input) != 1:
            raise ValueError("Only a single column is allowed for input.")
        else:
            input = input[0]

    # If user didn't provide an output, overwrite the input
    if output is None:
        output = input

    if pad is None:
        # If user has specified output columns either named
        # or using a wildcard, set pad = True
        if (
            (isinstance(output, str) and '*' in output)
            or isinstance(output, _list)
        ):
            pad = True
        else:
            pad = False

    # Determine the output_length based on the type and length of output
    # output_length = len(output) if isinstance(output, _list) and len(output) > 1 else None

    # Perform the split operation
    results = _format.split(
        df[input].astype(str).values,
        output_length=len(output) if isinstance(output, _list) and len(output) > 1 else None,
        split_char=char,
        pad=pad,
        inclusive=inclusive,
        element=element
    )

    # Handle wildcard cases and column assignment
    if (isinstance(output, str) and '*' in output) or (isinstance(output, _list) and len(output) == 1 and '*' in output[0]):
        # Use the wildcard pattern for generating output headers
        wildcard_template = output if isinstance(output, str) else output[0]
        output_headers = [wildcard_template.replace('*', str(i)) for i in range(1, len(results[0]) + 1)]
        df[output_headers] = results
    else:
        # Direct assignment for single column
        df[output] = results
        
    return df


def tokenize(
    df: _pd.DataFrame,
    input: _Union[str, int, _list],
    output: _Union[str, _list] = None,
    method: str = 'space',
    functions: dict = {}
) -> _pd.DataFrame:
    """
    type: object
    description: >-
      Split text into tokens. A variety of methods are available.
      The default method is to split on spaces.
    additionalProperties: false
    required:
      - input
    properties:
      input:
        type:
          - string
          - integer
          - array
        description: Column(s) to be split into tokens
      output:
        type: 
          - string
          - array
        description: Name of the output column
      method:
        anyOf:
          - type: string
            enum:
              - space
              - boundary
              - boundary_ignore_space
            description: >-
              Method to split the list.
              Options: space, boundary, boundary_ignore_space
              or use a custom function with custom.<function>
              or use a regex pattern with regex:<pattern>
          - type: string
            description: >-
              Method to split the list.
              Options: space, boundary, boundary_ignore_space
              or use a custom function with custom.<function>
              or use a regex pattern with regex:<pattern>
    """
    if output is None: output = input
    
    # Ensure input and outputs are lists
    if not isinstance(input, _list): input = [input]
    if not isinstance(output, _list): output = [output]

    # Ensure input and output are equal lengths
    if len(input) != len(output):
        raise ValueError('The list of inputs and outputs must be the same length for split.tokenize')
    
    func = None
    pattern = None

    # User defined custom function
    if str(method).startswith("custom."):
        func = _get_nested_function(method, None, functions)
        method = "function"
    # User defined Regex pattern
    elif str(method).lower().startswith("regex:"):
        pattern = method[6:].strip()
        method = "regex"
    # Default methods
    elif method not in ['space', 'boundary', 'boundary_ignore_space']:
        raise ValueError(
            'Method must be one of: space, boundary, '
            'boundary_ignore_space, custom.<function>, regex:<pattern>'
        )

    for in_col, out_col in zip(input, output):
        df[out_col] = _format.tokenize(df[in_col].values.tolist(), method, func, pattern)
            
    return df
