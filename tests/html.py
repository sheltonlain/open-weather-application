"""Shared helpers for inspecting rendered HTML in tests."""


def without_units_toggle(response) -> str:
    """Return the HTML minus the units toggle, whose labels name both units."""
    html = response.content.decode()
    if 'id="units-toggle"' not in html:
        return html
    start = html.rindex("<form", 0, html.index('id="units-toggle"'))
    end = html.index("</form>", start) + len("</form>")
    return html[:start] + html[end:]
