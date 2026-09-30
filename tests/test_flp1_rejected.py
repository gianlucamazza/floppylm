from pathlib import Path

import pytest

from floppylm.pack import LEGACY_REVISION, FormatError, unpack

FIXTURE = Path(__file__).parent / "fixtures" / "flp1_smoke.flp"


def test_flp1_is_rejected_with_pointer_to_reference_revision() -> None:
    with pytest.raises(FormatError, match=f"FLP1.*{LEGACY_REVISION}"):
        unpack(FIXTURE.read_bytes())
