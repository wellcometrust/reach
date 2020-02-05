
from deep_reference_parser.split_section import SplitSection
from reach.refparse.refparse import SectionedDocument

import pytest

section_splitter = SplitSection()

def test_empty_sections():
    references = section_splitter.split(" ")
    assert references == [], "Should be []"

@pytest.mark.xfail()
def test_oneline_section():
    references = section_splitter.split("Smith et al. 2019. This is a title. Journal of journals. 1-2")
    assert len(references) == 1, "There should be 1 reference found"

def test_oneline_section_brackets():
    references = section_splitter.split("Smith et al. (2019). This is a title. Journal of journals. 1-2")
    assert len(references) == 1, "There should be 1 reference found"

def test_empty_lines_section():
    references = section_splitter.split("\n\n\n")
    assert references == [], "Should be []"

@pytest.mark.xfail()
def test_normal_section():
    references = section_splitter.split(
        "References \n1. Smith et al. 2019. This is a title. Journal of journals. 1-2. "+
        "\n2. Smith et al. 2019. This is a title. Journal of journals. 1-2. "+
        "\n3. Smith et al. 2019. This is a title. Journal of journals. 1-2."
    )

    assert len(references) == 3, "There should be 3 reference found"

def test_normal_section_brackets():
    references = section_splitter.split(
        "References \n1. Smith et al. (2019). This is a title. Journal of journals. 1-2. "+
        "\n2. Smith et al. (2019). This is a title. Journal of journals. 1-2. "+
        "\n3. Smith et al. (2019). This is a title. Journal of journals. 1-2."
    )

    assert len(references) == 3, "There should be 3 reference found"
