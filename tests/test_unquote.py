# -*- coding:utf-8 -*-

from ..unquotemail import Unquote
import pytest, os


SAMPLE_DIR = 'samples'
EXPECTED_DIR = 'expecteds'


# Function to get pairs of sample and expected file names
def get_sample_expected_files():
    # os.path.join with the local folder, and add SAMPLE_DIR:
    sample_files = os.listdir(os.path.join(os.path.dirname(__file__), SAMPLE_DIR))
    expected_files = os.listdir(os.path.join(os.path.dirname(__file__), EXPECTED_DIR))

    # Ensure that both directories have the same set of filenames
    sample_files_set = set(sample_files)
    expected_files_set = set(expected_files)

    # assert sample_files_set == expected_files_set, "Mismatch between sample and expected files"

    # Return pairs of filenames
    return [(f, f) for f in sample_files]


# You can call one by doing:
# pytest -k "test_unquote[with_indent.txt-with_indent.txt]"

@pytest.mark.parametrize("sample_filename, expected_filename", get_sample_expected_files())
def test_unquote(sample_filename, expected_filename, request):
    # Test if fp is dir
    if os.path.isdir(os.path.join(os.path.dirname(__file__), SAMPLE_DIR, sample_filename)):
        return

    # Load the content of the sample file
    with open(os.path.join(os.path.dirname(__file__), SAMPLE_DIR, sample_filename), 'r') as sample_file:
        sample_content = sample_file.read()

    is_verbose = request.config.getoption("-k") is not None and "test_unquote[" in request.config.getoption("-k")

    if is_verbose:
        # Show debug message to say debose is enabled
        print('Debug mode enabled')
        print('Processing file ' + sample_filename)

    # Run the function and compare the result
    result = None
    if sample_filename.endswith('.html'):
        unquote = Unquote(sample_content, None, parse=False)
        unquote.parse()
        result = unquote.get_html()
    else:
        assert sample_filename.endswith('.txt')
        unquote = Unquote(None, sample_content, parse=False)
        unquote.parse()
        result = unquote.get_text()

    assert result is not None
    if os.path.exists(os.path.join(os.path.dirname(__file__), EXPECTED_DIR, expected_filename)):
        # Load the expected output
        with open(os.path.join(os.path.dirname(__file__), EXPECTED_DIR, expected_filename), 'r') as expected_file:
            expected_content = expected_file.read()
            try:
                assert result == expected_content, f"Test failed for {sample_filename}."
            except AssertionError as e:
                """
                # We move the file at sample_filename to the failing folder, in order to fix these later on
                os.rename(
                    os.path.join(os.path.dirname(__file__), SAMPLE_DIR, sample_filename),
                    os.path.join(os.path.dirname(__file__), SAMPLE_DIR, 'failing', sample_filename)
                )
                """
                if is_verbose:
                    print('Expected:')
                    print('-' * 80)
                    print(expected_content)
                    print('-' * 80)
                    print('Result:')
                    print('-' * 80)
                    print(result)
                    print('')
                raise e
    else:
        # In this case, we create what we consider would be the appropriate output
        with open(os.path.join(os.path.dirname(__file__), EXPECTED_DIR, '_' + expected_filename), 'w') as expected_file:
            expected_file.write(result)

        # Then, we raise a warning error for Pytest
        pytest.warns(UserWarning, f"Expected file {expected_filename} was not found. Created a new one with the output.")
