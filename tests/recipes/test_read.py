"""
Test general read behaviour and special read functions.

Tests specific to an individual connector should go in a test
file for the respective connectors
e.g. tests/connectors/test_file.py
"""
import wrangles
import pandas as pd


# If they've entered a list, get the first key and value from the first element
def test_input_is_list():
    recipe = """
    read:
        - file:
            name: tests/samples/data.xlsx
        
    """
    df = wrangles.recipe.run(recipe)
    assert len(df.columns.to_list()) == 2

def test_union_files():
    """
    Testing Union of multiple sources together
    """
    df = wrangles.recipe.run(
        """
          read:
            - union:
                sources:
                  - test:
                      rows: 3
                      values:
                        column1: value1
                        column2: value2
                  - test:
                      rows: 3
                      values:
                        column1: value1
                        column2: value2
        """
    )
    assert (
        len(df) == 6 and 
        df.columns.to_list() == ['column1', 'column2']
    )

def test_union_one_file():
    """
    Testing that a union still works with only a single source
    """
    df = wrangles.recipe.run(
        """
          read:
            - union:
                sources:
                  - test:
                      rows: 3
                      values:
                        column1: value1
                        column2: value2
        """
    )
    assert (
        len(df) == 3 and 
        df.columns.to_list() == ['column1', 'column2']
    )

def test_concatenate_files():
    """
    Testing concatenating multiple sources
    """
    df = wrangles.recipe.run(
        """
          read:
            - concatenate:
                sources:
                  - test:
                      rows: 3
                      values:
                        column1: value1
                        column2: value2
                  - test:
                      rows: 3
                      values:
                        column3: value3
                        column4: value4
        """
    )
    assert (
        len(df) == 3 and
        df.columns.to_list() == ['column1', 'column2', 'column3', 'column4'] and
        df['column1'][0] == "value1" and
        df['column4'][0] == "value4"
    )

def test_concatenate_one_file():
    """
    Testing that a concatenate still works with only a single source
    """
    df = wrangles.recipe.run(
        """
          read:
            - concatenate:
                sources:
                  - test:
                      rows: 3
                      values:
                        column1: value1
                        column2: value2
        """
    )
    assert (
        len(df) == 3 and
        df.columns.to_list() == ['column1', 'column2'] and
        df['column1'][0] == "value1"
    )

# Testing join of multiple sources
def test_join_files():
    recipe = """
    read:
        - join:
            how: inner
            left_on: Find
            right_on: Find2
            sources:
                - file:
                    name: tests/samples/data.xlsx
                - file:
                    name: tests/samples/data2.xlsx
    """
    df = wrangles.recipe.run(recipe)
    assert len(df.columns.to_list()) == 4

def test_read_with_where():
    """
    Test a read that includes a where condition
    """
    df = wrangles.recipe.run(
        """
        read:
          - test:
              rows: 1000
              values:
                header1: <int>
              where: '"header1" > ?'
              where_params:
                - 50
        """
    )
    assert (
        len(df) < 1000
        and df["header1"].min() > 50
    )

def test_read_with_columns():
    """
    Test a read that includes a columns condition
    """
    df = wrangles.recipe.run(
        """
        read:
          - test:
              rows: 5
              values:
                header1: value1
                header2: value2
                header3: value3
              columns:
                - header1
                - header2
        """
    )
    assert list(df.columns) == ["header1","header2"]

def test_read_with_not_columns():
    """
    Test a read that includes a not_columns condition
    """
    df = wrangles.recipe.run(
        """
        read:
          - test:
              rows: 5
              values:
                header1: value1
                header2: value2
                header3: value3
              not_columns: header3
        """
    )
    assert list(df.columns) == ["header1","header2"]

def test_read_order_by():
    """
    Test a read that includes an order by condition
    """
    df = wrangles.recipe.run(
        """
        read:
          - test:
              rows: 100
              values:
                header: <number>
              order_by: header
        """
    )
    assert (
        df.tail(1)["header"].iloc[0] == max(df["header"].values)
        and df.head(1)["header"].iloc[0] == min(df["header"].values)
    )

def test_multiple_reads():
    """
    Test that multiple reads are concatenated correctly
    """
    df = wrangles.recipe.run(
        """
        read:
          - test:
              rows: 1
              values:
                header: value1
          - test:
              rows: 1
              values:
                header: value2
        """
    )
    assert list(df['header'].values) == ['value1', 'value2']

def test_read_single_plus_aggregate():
    """
    Test a read that includes an aggregating connector
    and a regular single connector
    """
    df = wrangles.recipe.run(
        """
        read:
          - union:
              sources:
                - test:
                    rows: 1
                    values:
                      header: value1
                - test:
                    rows: 1
                    values:
                      header: value2
        
          - test:
              rows: 1
              values:
                header: value3
        """
    )
    assert list(df['header'].values) == ['value1', 'value2', 'value3']

def test_all_if_false():
    """
    Test that a recipe works correctly if all reads test false
    """
    df = wrangles.recipe.run(
        """
        read:
          - test:
              if: 1 == 2
              rows: 1
              values:
                header: value1
          - test:
              if: 1 == 2
              rows: 1
              values:
                header: value2
        """
    )
    assert isinstance(df, pd.DataFrame) and df.empty

def test_overwrite_read():
    """
    Test using a custom function to overwrite a standard connector for read
    """
    class file:
        def read(name):
            return {
              "abc": pd.DataFrame({"header": ["value1", "value2"]})
            }[name]
        
    df = wrangles.recipe.run(
        """
        read:
          - file:
              name: abc
        """,
        functions=file
    )
    
    assert df['header'][0] == "value1"
