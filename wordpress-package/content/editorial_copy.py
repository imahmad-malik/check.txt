"""Short public captions from reviewed style attributes, separate from provenance."""
import re

TECHNICAL_COPY = re.compile(r'native|resolution|generated|opaque|turtleneck|shoulder|skin|lighting|same adult|complete head|no-face|coherent|single-eye|leftprofile|rightprofile|matching|studio|fictional|strict.?90|true.?90|head margin', re.I)
TEXTURES = {'straight': 'straight', 'wavy': 'wavy', 'curly': 'curly', 'coily': 'coiled'}
FRINGES = {'wispy': 'a wispy fringe', 'side-swept': 'a side-swept fringe', 'short open': 'an open fringe', 'short-open': 'an open fringe', 'curtain': 'a curtain fringe', 'full': 'a full fringe', 'none': 'an open face frame'}


def style_phrase(meta):
    colour = str(meta.get('colour', '')).replace('-', ' ')
    texture = TEXTURES.get(meta.get('texture'), '')
    phrase = ' '.join(part for part in [colour, texture, 'bixie'] if part)
    fringe = FRINGES.get(meta.get('fringe'))
    return phrase + (' with ' + fringe if fringe else '')


def title_and_excerpt(declaration, meta):
    phrase = style_phrase(meta)
    title = declaration.get('title', '')
    if not title or re.search(r'^Bixie (?:reference|concept)\b|\s\d{2}$', title, re.I):
        title = phrase[0].upper() + phrase[1:]
    excerpt = declaration.get('excerpt', '')
    if not excerpt or TECHNICAL_COPY.search(excerpt):
        excerpt = phrase[0].upper() + phrase[1:] + '. Front, side and back photographs show the face frame, crown and nape.'
    return title, excerpt


def caption_for_view(image, meta):
    caption = image.get('caption', '')
    if caption and not TECHNICAL_COPY.search(caption):
        return caption
    angle = image['angle']
    subject = {'front': 'Face frame and fringe', 'side': 'Temple, ear coverage and nape transition', 'back': 'Crown outline and nape'}[angle]
    # A side-facing portrait need not be an anatomically exact90-degree profile.
    label = {'front': 'Front view', 'side': 'Side angle', 'back': 'Back view'}[angle]
    return label + ': ' + subject[0].lower() + subject[1:] + '.'
