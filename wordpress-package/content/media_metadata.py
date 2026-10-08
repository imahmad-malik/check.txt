"""Structured look attributes; per-angle descriptive review notes stay separate."""
LOOK_METADATA_FIELDS = frozenset({
    'texture', 'strand', 'density', 'length', 'fringe', 'colour', 'finish',
    'age_reference', 'face_reference', 'maintenance', 'styling', 'ai_concept',
})


def public_metadata_value(field, value):
    # "discuss" is a production-planning marker, not published maintenance advice.
    return '' if field == 'maintenance' and value == 'discuss' else value
