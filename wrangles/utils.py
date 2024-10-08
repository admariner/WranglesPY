import re as _re
import logging as _logging
import types as _types
import inspect as _inspect
from typing import Union as _Union


def wildcard_expansion_dict(all_columns: list, selected_columns: dict) -> list:
    """
    Finds matching columns for wildcards or regex from all available columns

    This expects the input to be in the format:
    {"in_col": "out_col", "unchanged": "unchanged"}
    
    :param all_columns: List of all available columns in the dataframe
    :param selected_columns: List or string with selected columns. May contain wildcards (*) or regex.
    """
    # Convert wildcards (*) to regex patterns
    tmp_columns = {}
    for k, v in selected_columns.items():
        # If column contains * without escape
        if _re.search(r'[^\\]?\*', str(k)) and not str(k).lower().startswith('regex:'):
            # Convert wildcard to a regex pattern for key
            k = 'regex:' + _re.sub(r'(?<!\\)\*', r'(.*)', k)
            # Convert wildcard to a regex pattern for value
            group_counter = [0]
            def replacer(_):
                """
                Increment group number using a mutable object
                each time this function is called to give
                a unique capture group number for each wildcard
                """
                # Use the current counter value, then increment it
                group_counter[0] += 1                
                return fr'\g<{group_counter[0]}>'
            v = _re.sub(r'(?<!\\)\*', replacer, v)
            tmp_columns[k] = v
        else:
            tmp_columns[k] = v

    selected_columns = tmp_columns

    # Create output dictionary
    result_columns = {}

    # Identify any matching columns using regex within the list
    for column in selected_columns:
        if column.lower().startswith('regex:'):
            # result_columns.update() # Read Note below
            matching_columns = dict.fromkeys(list(
                filter(_re.compile(column[6:].strip()).fullmatch, all_columns)
            ))
            try:
                if column == selected_columns[column]:
                    # If the column is not renamed, maintain the original matching column names
                    renamed_columns = [_re.sub("(" + column[6:].strip() + ")", r"\1", col, count=1) for col in matching_columns]
                else:
                    # Else rename the columns using the provided regex pattern
                    renamed_columns = [_re.sub(column[6:].strip(), selected_columns[column], col, count=1) for col in matching_columns]
            except _re.error as e:
                raise ValueError(f"Invalid regex pattern: {selected_columns[column]}. Are you missing a capture group?") from None
            
            if len(renamed_columns) != len(set(renamed_columns)):
                _logging.warning(
                    "Renamed columns contain duplicate values. Consider including a wildcard or regex capture group."
                )

            result_columns = {
                **{
                    k: v
                    for k, v in zip(matching_columns, renamed_columns)
                },
                **result_columns
            }
        else:
            # Check if a column is indicated as
            # optional with column_name?
            optional_column = False
            if column[-1] == "?" and column not in all_columns:
                column = column[:-1]
                optional_column = True

            if column in all_columns:
                result_columns[column] = selected_columns[column]
            else:
                if not optional_column:
                    raise KeyError(f'Column {column} does not exist')

    return result_columns


def get_nested_function(
    fn_string: str,
    stock_functions: _types.ModuleType = None,
    custom_functions: dict = None,
    default_stock_functions: str = None
):
    """
    Get a nested function from obj as defined by a string
    e.g. 'custom.my_function' or 'my_function' or 'my_module.my_function'

    :param fn_string: String defining the function to get
    :param stock_functions: Module containing stock functions
    :param custom_functions: Dictionary of user defined custom functions
    :param default_stock_functions: Some stock functions use a default final function to call
    """
    if custom_functions is None and stock_functions is None:
        raise ValueError('No functions provided')

    fn_list = fn_string.strip().split('.')
    if fn_list[0] == 'custom':
        if len(fn_list) == 1:
            raise ValueError('Custom function not defined correctly')
        fn_list = fn_list[1:]
        obj = custom_functions
    else:
        if default_stock_functions:
            fn_list.append(default_stock_functions)
        obj = stock_functions
        
    for fn_name in fn_list:
        if isinstance(obj, dict):
            if fn_name not in obj:
                raise ValueError(f'Function {fn_string} not recognized')
            obj = obj[fn_name]
        else:
            if not hasattr(obj, fn_name):
                raise ValueError(f'Function {fn_string} not recognized')
            obj = getattr(obj, fn_name)
    
    return obj


def add_special_parameters(
    params: dict,
    fn: _types.FunctionType,
    functions: dict = {},
    variables: dict = {},
    error: Exception = None,
    common_params: dict = {}
):
    """
    Add special parameters to the params dictionary if they are required by the function

    :param params: Dictionary of parameters to pass to the function
    :param fn: Function to check for special parameters
    :param functions: Dictionary of custom functions
    :param variables: Dictionary of variables
    :param error: Exception object
    :param common_params: These are parameters that are common to all functions. \
        They will only be passed as a parameter if the function requests them.
    """
    # Check args and pass on special parameters if requested
    argspec = _inspect.getfullargspec(fn).args
    if ("functions" not in params and "functions" in argspec):
        params['functions'] = functions
    if ("variables" not in params and "variables" in argspec):
        params['variables'] = variables

    if error and "error" not in params and "error" in argspec:
        params['error'] = error

    # Allow functions to access common
    # parameters only if they need them
    if common_params:
        params = {
            **params,
            **{
                k: v
                for k, v in common_params.items()
                if k in argspec
            }
        }

    return params


def wildcard_expansion(all_columns: list, selected_columns: _Union[str, list]) -> list:
    """
    Finds matching columns for wildcards or regex from all available columns
    
    :param all_columns: List of all available columns in the dataframe
    :param selected_columns: List or string with selected columns. May contain wildcards (*) or regex.
    """
    if not isinstance(selected_columns, list): selected_columns = [selected_columns]

    # Convert wildcards to regex pattern
    for i in range(len(selected_columns)):
        # If column contains * without escape
        if _re.search(r'[^\\]?\*', str(selected_columns[i])) and not str(selected_columns[i]).lower().startswith('regex:'):
            selected_columns[i] = 'regex:' + _re.sub(r'(?<!\\)\*', r'(.*)', selected_columns[i])

    # Using a dict to preserve insert order.
    # Order is preserved for Dictionaries from Python 3.7+
    result_columns = {}

    # Identify any matching columns using regex within the list
    for column in selected_columns:
        if column.lower().startswith('regex:'):
            result_columns.update(dict.fromkeys(list(
                filter(_re.compile(column[6:].strip()).fullmatch, all_columns)
            ))) # Read Note below
        else:
            # Check if a column is indicated as
            # optional with column_name?
            optional_column = False
            if column[-1] == "?" and column not in all_columns:
                column = column[:-1]
                optional_column = True

            if column in all_columns:
                result_columns[column] = None
            else:
                if not optional_column:
                    raise KeyError(f'Column {column} does not exist')
    
    # Return, preserving original order
    return list(result_columns.keys())
