"""Phase 6: Automated frontend testing of Streamlit application using AppTest."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.skipif(
    True,
    reason="Skip loading real dataset in unit tests if not desired, remove to run",
)
def test_streamlit_rendering() -> None:
    # Initialize the AppTest from the main entrypoint
    at = AppTest.from_file("src/app/main.py")
    
    # Run the initial render
    at.run(timeout=60)
    assert not at.exception

    # Assert basic structure is present
    # There should be selectboxes for City and Cuisine
    assert len(at.selectbox) >= 2
    
    # Verify titles/labels are rendering
    # The default City should be Bangalore (or the first available)
    assert at.selectbox[0].value == "Bangalore"
    
    # Verify the budget radio has options
    assert len(at.radio) >= 1
    assert at.radio[0].value == "Medium"

    # Verify minimum rating slider is present
    assert len(at.slider) >= 1
    assert at.slider[0].value == 3.0

    # Verify vibes text area
    assert len(at.text_area) >= 1
    assert at.text_area[0].value == ""
