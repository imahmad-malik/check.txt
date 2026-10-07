#!/usr/bin/env python3
"""Add image-led guide allocations without altering integrated theme requirements.

Only completed, approved canonical look sets may provide the eventual gallery.
This patch supplies no generated images and never inflates original counts.
"""
from pathlib import Path
import json, html

def paragraph(text):
    return '<!-- wp:paragraph -->\n<p>'+text+'</p>\n<!-- /wp:paragraph -->'

def heading(text):
    return '<!-- wp:heading -->\n<h2 class="wp-block-heading">'+html.escape(text)+'</h2>\n<!-- /wp:heading -->'

def bullets(items):
    body='\n'.join('<!-- wp:list-item -->\n<li>'+item+'</li>\n<!-- /wp:list-item -->' for item in items)
    return '<!-- wp:list -->\n<ul class="wp-block-list">'+body+'</ul>\n<!-- /wp:list -->'

def link(path,text):
    return '<a href="'+html.escape(path,quote=True)+'">'+html.escape(text)+'</a>'

def blocks(*items):
    return '\n\n'.join(items)

ROOT=Path(__file__).resolve().parent
path=ROOT/'catalog.json'
catalog=json.loads(path.read_text())
allocations={
 'what-is-a-bixie-haircut':[('classic-01','Classic bixie concept: compare the crown, face frame and nape.')],
 'what-to-ask-your-stylist':[('classic-02','A coherent bixie reference set for discussing the shape with your stylist.')],
 'styling-a-bixie':[('easy-styling-03','Bixie concept reference: discuss which details involve styling and which belong to the cut.')],
 'fine-vs-thin-hair':[('fine-hair-01','Fine-strand bixie concept reference.'),('thin-hair-01','Lower-density bixie concept reference.')],
 'reading-haircut-references':[('layered-02','The same layered bixie concept in corresponding front, side and back views.')],
 'growing-out-a-bixie':[('long-03','Long bixie target-shape reference; not a documented growth sequence.')],
 'bixie-shixie-wolf-cut':[('shaggy-03','Shaggy bixie concept: identify the visible shape before choosing an informal label.')],
}
copy={
 'what-is-a-bixie-haircut':blocks(
     paragraph('A bixie combines a shorter pixie-like back and crown with longer bob-like pieces around the face. Start with the visible outline rather than one fixed cutting name.'),
     heading('Read the shape'),
     paragraph('Compare the fringe from the front, ear coverage from the side and graduation at the nape from the back. The corresponding photos illustrate one bixie concept.'),
     heading('Bixie, pixie and bob'),
     paragraph('A pixie generally has a more compact short outline; a bob generally has a more continuous perimeter. Boy bob and long pixie-bob names can overlap. Describe the actual length, crown and face frame you prefer instead of treating every label as an exact synonym.'),
     paragraph('AI-created concepts do not guarantee a salon result. '+link('/collections/classic/','Explore classic bixies')+' or '+link('/guides/what-to-ask-your-stylist/','prepare your stylist questions')+'.')),
 'what-to-ask-your-stylist':blocks(
     paragraph('Choose a small reference set and name the details you like. The front, side and back views help make the preferred proportions clearer.'),
     heading('Four useful questions'),
     bullets(['How much length do I want around my ears and jaw?','Would I prefer a compact or softer nape?','Which fringe and parting feel comfortable?','How much daily styling and shape maintenance do I want?']),
     paragraph('Ask which visible details come from the cut and which require styling. Your texture, density and growth direction may differ from the fictional model’s concept.'),
     paragraph(link('/saved-looks/','Save a shortlist')+', '+link('/compare/','compare two or three looks')+' and '+link('/print/','print the available views')+' with your own notes. A generated reference is a starting point for discussion, not a promise of an exact result.')),
 'styling-a-bixie':blocks(
     paragraph('Choose the finish you want on an ordinary day. A smooth, airy, wavy or curly photograph does not establish how much effort the same outline will take on your hair.'),
     heading('Compare texture and finish'),
     paragraph('Notice the parting, crown separation and pieces beside the face. Discuss your natural texture and which photographed details involve styling. For curls and waves, talk through the preferred dry outline and fringe.'),
     heading('Keep the routine realistic'),
     paragraph('Daily effort and appointments to refresh the outline are separate questions. Follow the instructions for any tools or products you choose. The site does not test or endorse particular products.'),
     paragraph(link('/collections/easy-styling/','Explore easy-styling concepts')+' and read the <a href="https://www.aad.org/public/everyday-care/hair-scalp-care/hair/healthy-hair-tips">AAD’s general hair-care guidance</a> for further care information. No reference is universally low-maintenance.')),
 'fine-vs-thin-hair':blocks(
     paragraph('Fine hair describes the diameter of individual strands. Thin or low-density hair describes how much hair is present. These are separate attributes, and a person can have fine strands with relatively high density.'),
     heading('Compare the references'),
     paragraph('The fine-strand and lower-density concept sets illustrate different browsing categories. Look at the parting, fringe separation and perimeter; do not assume the fullest generated photo will translate directly to your hair.'),
     heading('Discuss the outline'),
     paragraph('Ask which areas you want to keep more continuous, how much layering you prefer and whether the shown finish involves a routine you want to maintain.'),
     paragraph('These images are haircut inspiration, not hair-loss diagnosis or treatment. '+link('/collections/fine-hair/','Browse fine-hair concepts')+' and '+link('/collections/thin-hair/','lower-density references')+' separately. Concerning changes in density belong in a healthcare discussion.')),
 'reading-haircut-references':blocks(
     paragraph('Corresponding views show the same haircut concept from different positions. A front crop cannot reveal the nape, and another crop of it must not be labelled a back view.'),
     heading('Front, side and back'),
     bullets(['Front: compare the fringe, parting and face-framing pieces.','Side: compare ear coverage and the transition from longer front pieces to the shorter back.','Back: compare the crown outline, graduation and nape.']),
     paragraph('Look for the same model, hair colour, fringe and overall structure across the set. A missing angle should remain unavailable.'),
     paragraph('Even a complete AI-created set does not show a cutting method or predict your own hair’s behaviour. '+link('/compare/','Compare a shortlist')+' and '+link('/print/','prepare a reference sheet')+' for discussion.')),
 'growing-out-a-bixie':blocks(
     paragraph('As a bixie grows, its shorter nape and crown can reach different stages from its longer face frame. Start by choosing the outline you want next.'),
     heading('Use a target shape'),
     paragraph('The photos illustrate a long bixie target concept, not a real before-and-after or a documented growth sequence. Compare the side and back as well as the fringe.'),
     heading('Discuss the transition'),
     paragraph('Ask which areas you want to preserve and which parts of the outline could be adjusted. A shaping appointment depends on your starting cut, target and preferences; the site promises no fixed growth rate or timetable.'),
     paragraph(link('/collections/long/','Explore longer bixie references')+' and '+link('/guides/what-to-ask-your-stylist/','prepare consultation questions')+'. Pixie grow-out examples may start from different proportions, so compare the actual shape before borrowing a label.')),
 'bixie-shixie-wolf-cut':blocks(
     paragraph('Bixie, shixie and wolf-cut labels can overlap in inspiration searches. Use the actual shape to describe what you want. The photos here illustrate a shaggy bixie concept.'),
     heading('Look beyond the name'),
     paragraph('A bixie balances a shorter back with longer face-framing pieces. Shaggy describes visible layered movement; shixie is informal shorthand for a shag-and-pixie mix. Wolf-cut descriptions often emphasize more strongly layered proportions and do not all belong in a bixie collection.'),
     heading('Compare four details'),
     bullets(['Length beside the face.','Crown relative to the nape.','Fringe and its connection to the sides.','The difference between structure and a styled finish.']),
     paragraph(link('/collections/shaggy/','Browse shaggy bixies')+' or '+link('/guides/what-is-a-bixie-haircut/','read the bixie definition')+'. A hairstyle name alone cannot guarantee a particular salon result.')),
}

for p in catalog['pages']:
    if p['key']=='contact' and '<!-- wp:bixie/contact-details' not in p['content']:
        p['content']+='\n\n<!-- wp:bixie/contact-details /-->'
    if p['key'] not in allocations: continue
    sets=[{'look_key':look,'angles':['front','side','back'],'caption':caption} for look,caption in allocations[p['key']]]
    p.update({'content':copy[p['key']],'photo_set_requirements':sets,'minimum_photos':3*len(sets),
              'photo_insert_after_block':1,'photo_block_type':'core/gallery',
              'status':'draft','indexability':'eligible-when-populated',
              'publish_when':'All allocated look sets have genuine approved front/side/back attachments meeting the catalog native-quality requirement; insert real native Gallery/Image blocks and preserve owner edits.'})

catalog['site']['guide_presentation']='Image-led reference pages; concise editable notes below coherent native gallery blocks.'
catalog['counts']['required_guide_photo_references']=24
catalog['counts']['additional_originals_required_for_guides']=0
catalog['counts']['provided_guide_photo_references']=0
path.write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
(ROOT/'guide-photo-allocation.json').write_text(json.dumps({'version':'1.0.0','status':'required-not-provided','original_counting_rule':'Canonical look views referenced by guides remain counted once as original source assets.','allocations':[{ 'page_key':key,'photo_sets':[{'look_key':look,'angles':['front','side','back'],'caption':caption} for look,caption in refs],'minimum_photos':len(refs)*3} for key,refs in allocations.items()]},indent=2)+'\n')
print('Updated seven image-led guide records; 24 canonical photo references required, zero provided.')
