import random
import string
import wrangles
import pytest


def test_write_and_read():
    """
    Write a random string to CKAN server,
    then read results back to verify
    """
    random_string = ''.join(random.choices(string.ascii_lowercase, k=8))
    recipe = """
    read:
      - test:
          rows: 5
          values:
            header: ${RANDOM_VALUE}
    
    write:
      - ckan:
          host: https://catalog.wrangle.works
          dataset: test
          file: test.csv
          api_key: ${CKAN_API_KEY}
    """
    wrangles.recipe.run(
        recipe,
        variables={
            'RANDOM_VALUE': random_string
        }
    )

    recipe = """
    read:
      - ckan:
          host: https://catalog.wrangle.works
          dataset: test
          file: test.csv
          api_key: ${CKAN_API_KEY}
    """
    df = wrangles.recipe.run(recipe)
    assert df['header'].values[0] == random_string

def test_missing_apikey():
    """
    Check error if user omits API KEY
    """
    recipe = """
    read:
      - ckan:
          host: https://catalog.wrangle.works
          dataset: test
          file: test.csv
    """
    with pytest.raises(RuntimeError) as info:
        raise wrangles.recipe.run(recipe)
    
    assert info.typename == 'RuntimeError' and info.value.args[0].startswith('Access Denied')

def test_invalid_apikey():
    """
    Check error if user has invalid API KEY
    """
    recipe = """
    read:
      - ckan:
          host: https://catalog.wrangle.works
          dataset: test
          file: test.csv
          api_key: aaaaaa
    """
    with pytest.raises(RuntimeError) as info:
        raise wrangles.recipe.run(recipe)
    
    assert info.typename == 'RuntimeError' and info.value.args[0].startswith('Access Denied')

def test_missing_dataset():
    """
    Check error if dataset isn't found
    """
    recipe = """
    read:
      - ckan:
          host: https://catalog.wrangle.works
          dataset: aaaaaaaaaaaaa
          file: test.csv
          api_key: ${CKAN_API_KEY}
    """
    with pytest.raises(ValueError) as info:
        raise wrangles.recipe.run(recipe)
    
    assert info.typename == 'ValueError' and info.value.args[0][:22] == 'Unable to find dataset'


def test_missing_file():
    """
    Check error if file isn't found in the dataset
    """
    recipe = """
    read:
      - ckan:
          host: https://catalog.wrangle.works
          dataset: test
          file: aaaaaaaaaaaaaa.csv
          api_key: ${CKAN_API_KEY}
    """
    with pytest.raises(ValueError) as info:
        raise wrangles.recipe.run(recipe)
    
    assert info.typename == 'ValueError' and info.value.args[0][:14] == 'File not found'


def test_upload_file():
    """
    Test run action to upload a file
    """
    random_string = ''.join(random.choices(string.ascii_lowercase, k=8))

    wrangles.recipe.run(
        """
          run:
            on_success:
              - ckan.upload:
                  host: https://catalog.wrangle.works
                  dataset: test
                  file: tests/temp/test.csv
                  api_key: ${CKAN_API_KEY}
                  output_file: test.csv

          read:
            - test:
                rows: 5
                values:
                  header: ${RANDOM_STRING}
            
          write:
            - file:
               name: tests/temp/test.csv
        """,
        variables = {
          'RANDOM_STRING': random_string
        }
    )

    df = wrangles.recipe.run(
        """
          read:
            - ckan:
                host: https://catalog.wrangle.works
                dataset: test
                file: test.csv
                api_key: ${CKAN_API_KEY}
        """
    )

    assert df['header'][0] == random_string

def test_upload_files():
    """
    Test run action to upload a list of file
    """
    random_strings = [
        ''.join(random.choices(string.ascii_lowercase, k=8)),
        ''.join(random.choices(string.ascii_lowercase, k=8))
    ]

    wrangles.recipe.run(
        """
        run:
          on_success:
            - ckan.upload:
                host: https://catalog.wrangle.works
                dataset: test
                file:
                  - tests/temp/test0.csv
                  - tests/temp/test1.csv
                api_key: ${CKAN_API_KEY}
                output_file:
                  - test0.csv
                  - test1.csv

        read:
          - test:
              rows: 5
              values:
                header0: ${RANDOM_STRING_0}
                header1: ${RANDOM_STRING_1}
            
        write:
          - file:
              name: tests/temp/test0.csv
              columns:
                - header0
          - file:
              name: tests/temp/test1.csv
              columns:
                - header1
        """,
        variables = {
            'RANDOM_STRING_0': random_strings[0],
            'RANDOM_STRING_1': random_strings[1],
        }
    )

    df = wrangles.recipe.run(
        """
          read:
            - concatenate:
                sources:
                  - ckan:
                      host: https://catalog.wrangle.works
                      dataset: test
                      file: test0.csv
                      api_key: ${CKAN_API_KEY}
                  - ckan:
                      host: https://catalog.wrangle.works
                      dataset: test
                      file: test1.csv
                      api_key: ${CKAN_API_KEY}
        """
    )

    assert df['header0'][0] == random_strings[0] and df['header1'][0] == random_strings[1]

def test_download_file():
    """
    Test run action to download a file
    """
    df = wrangles.recipe.run(
        """
          run:
            on_start:
              - ckan.download:
                  host: https://catalog.wrangle.works
                  dataset: test
                  file: test.csv
                  api_key: ${CKAN_API_KEY}
                  output_file: tests/temp/test.csv

          read:
            - file:
                name: tests/temp/test.csv
        """
    )

    assert len(df) > 0

def test_download_files():
    """
    Test run action to download multiple files
    """
    df = wrangles.recipe.run(
        """
          run:
            on_start:
              - ckan.download:
                  host: https://catalog.wrangle.works
                  dataset: test
                  file:
                    - test.csv
                    - test1.csv
                  api_key: ${CKAN_API_KEY}
                  output_file:
                    - tests/temp/test.csv
                    - tests/temp/test1.csv

          read:
            - union:
               sources:
                - file:
                    name: tests/temp/test.csv
                - file:
                    name: tests/temp/test1.csv
        """
    )

    assert len(df) > 0
