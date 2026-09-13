"""The section badge counts itself, so two sections can never share a number again.

The numbers used to be typed into every template by hand (`m.section(10, ...)` twice in one file, and a gap in
the single-issuer template), which is a bug class, not a typo: nothing linked the number to the section order.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = sorted((ROOT / "templates").glob("*.html"))


def test_no_template_types_a_section_number_by_hand():
    offenders = []
    for f in TEMPLATES:
        for i, ln in enumerate(f.read_text().splitlines(), 1):
            if re.search(r"m\.section\(\s*\d", ln):
                offenders.append(f"{f.name}:{i}: {ln.strip()[:80]}")
    assert not offenders, "a section number was typed by hand:\n" + "\n".join(offenders)


def test_section_badges_count_up_without_gaps_or_collisions():
    from server.routers.pdf import render_html_for_ticker

    html = render_html_for_ticker("AMMN", None)[1]
    badges = [b for b in re.findall(r'class="section-no">([^<]*)<', html) if b.strip()]
    assert badges, "no section badge rendered"
    assert badges == [str(i) for i in range(1, len(badges) + 1)], f"section badges out of order: {badges}"


def test_the_risk_rail_numbers_every_risk_and_borrows_its_figure():
    from server.routers.pdf import render_html_for_ticker

    html = render_html_for_ticker("AMMN", None)[1]
    rail = re.search(r'<ol class="risk-rail">([\s\S]*?)</ol>', html)
    assert rail, "the risk rail did not render"
    numbers = re.findall(r'class="risk-no">([^<]*)<', rail.group(1))
    assert numbers == [f"{i:02d}" for i in range(1, len(numbers) + 1)], f"risk rail numbers: {numbers}"
    # a figure on the rail has to be one the risk's own sentence already prints
    for value, _label in re.findall(r'class="risk-anchor">([^<]*)<i>([^<]*)</i>', rail.group(1)):
        assert value.strip() in rail.group(1).replace("&minus;", "−"), f"anchor {value!r} is not in its own row"


def test_a_declared_risk_anchor_is_still_something_the_row_prints():
    """Declaring a figure is allowed; inventing one is not."""
    from server.routers.pdf import render_html_for_ticker

    _t, html, payload = render_html_for_ticker("AMMN", None)
    for r in payload.get("risks") or []:
        stat = r.get("stat")
        if not stat:
            continue
        row = f"{r.get('bucket', '')} {r.get('detail', '')}"
        assert str(stat) in row, f"declared anchor {stat!r} is not printed by its own row: {r.get('bucket')}"
