"""Original Endpoints art may be read from the user's own JetBrains app.

Tests use synthetic ZIP containers and our already-licensed SVG fixture;
no copies of closed-source JetBrains resources are committed or fabricated.
"""
from pathlib import Path
from zipfile import ZipFile

from pynix_gui.ide_local_jetbrains_icons import (
    _official_ide_bundles, _validate_svg, original_endpoints_svg,
)
from pynix_gui.ide_icon_parity import BUNDLED_ICONS


def _bundle(tmp_path: Path, *, dark_only: bool = False) -> tuple[Path, str, str]:
    app = tmp_path / "Applications" / "PyCharm.app"
    jar = app / "Contents" / "plugins" / "microservices" / "lib" / "microservices.jar"
    jar.parent.mkdir(parents=True, exist_ok=True)
    light = (BUNDLED_ICONS / "svg/toolwindows/find.svg").read_text("utf-8")
    dark = (BUNDLED_ICONS / "svg/toolwindows/find_dark.svg").read_text("utf-8")
    with ZipFile(jar, "w") as z:
        if not dark_only:
            z.writestr("icons/expui/toolwindows/endpoints.svg", light)
        z.writestr("icons/expui/toolwindows/endpoints_dark.svg", dark)
    return app, light, dark


def test_reads_exact_original_light_and_dark_svg_from_real_resource_names(tmp_path):
    app, light, dark = _bundle(tmp_path)
    assert original_endpoints_svg(roots=[app], dark=True) == dark
    assert original_endpoints_svg(roots=[app], dark=False) == light
    assert original_endpoints_svg(roots=[app], dark=True).startswith("<!-- Copyright")
    assert _official_ide_bundles([tmp_path / "Applications"]) == (app,)


def test_falls_back_to_unmodified_official_light_variant(tmp_path):
    app, light, dark = _bundle(tmp_path)
    jar = next((app / "Contents/plugins").rglob("*.jar"))
    with ZipFile(jar, "w") as z:
        z.writestr("icons/expui/toolwindows/endpoints.svg", light)
    assert original_endpoints_svg(roots=[app], dark=True) == light


def test_ignores_unrelated_jar_icons_and_rejects_unsafe_svg(tmp_path):
    app = tmp_path / "PyCharm.app"
    jar = app / "Contents" / "plugins" / "microservices" / "lib" / "icons.jar"
    jar.parent.mkdir(parents=True)
    with ZipFile(jar, "w") as z:
        z.writestr("icons/fake/endpoints.svg",
                   '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>')
    assert original_endpoints_svg(roots=[app], dark=True) is None
    assert _validate_svg(b'<svg><script>alert(1)</script></svg>') is None
    assert _validate_svg(b'<!DOCTYPE svg><svg/>') is None
    assert _validate_svg(b'<html>not SVG</html>') is None
    assert _validate_svg(b'<svg xmlns="http://www.w3.org/2000/svg"><path/></svg>') is not None


def test_explicit_user_supplied_jar_uses_original_resource_bytes(tmp_path):
    app, light, dark = _bundle(tmp_path)
    jar = next((app / "Contents/plugins").rglob("*.jar"))
    assert original_endpoints_svg(roots=[jar], dark=True) == dark
