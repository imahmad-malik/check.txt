#!/usr/bin/env python3
"""Build portable, block-editable content and an honest production plan.

This script does not generate images or claim planned assets are delivered.
"""
from pathlib import Path
import csv, json, html, re, subprocess, sys

OUT=Path(__file__).resolve().parent
RESEARCH=OUT/'research'

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

def page(key,slug,title,content,description,parent=None,kind='page',status='publish',**extra):
    row={'key':key,'slug':slug,'title':title,'content':content,'excerpt':description,
         'seo_title':title+' | Bixie Haircut' if len(title)<44 else title,
         'meta_description':description,'type':kind,'status':status,'menu_order':0,
         'indexability':'eligible' if kind not in ['tool','contact'] else 'noindex',
         'publish_when':'editorial copy ready; verify actual linked media and routes',**extra}
    if parent: row['parent_key']=parent
    return row

COLLECTIONS=[
 ('classic','Classic bixie haircuts','shape','A balanced bob-pixie shape: a shorter nape, soft crown and face-framing pieces that make the hybrid easy to read.','Compare the outline around the ears and jaw rather than choosing from the front view alone. A classic bixie can have a light fringe or an open forehead; the relationship between its shorter back and longer front is the useful starting point.',['long','short','layered'],{'length':'medium'},'Editorial collection; direct head-term support'),
 ('short','Short bixie haircuts','shape','Shorter bixie references keep the nape compact while preserving enough length around the face to read as a bob-pixie hybrid.','Look for a clear crown-to-nape transition and enough temple length to distinguish the cut from a close pixie. Talk through how often you want the outline refreshed and how much ear coverage you prefer.',['classic','undercut','easy-styling'],{'length':'short'},'Editorial modifier; broader adjacent short-hair terms'),
 ('long','Long bixie haircuts','shape','Long bixies lean toward a bob around the face, with shorter layering and graduation through the back.','Longer front pieces give more options for parting and tucking. Check the side and back references before using a long pixie-bob photo: a standard one-length bob is a different shape.',['classic','layered','bangs'],{'length':'long'},'Direct long bixie and equivalent long pixie-bob terms'),
 ('layered','Layered bixie haircuts','finish','Layered bixie references show how the crown, face frame and nape can connect without making every section the same length.','A photograph can suggest the outline but cannot show a cutting plan. Bring the front, side and back views to discuss where you want softness, separation or a more compact perimeter.',['fine-hair','feathered','choppy'],{'finish':'layered'},'Measured layered pixie-bob equivalent'),
 ('choppy','Choppy bixie haircuts','finish','Choppy bixies use more visible separation and an uneven-looking finish, while retaining a readable short back and longer face frame.','Notice whether the movement comes from the cut, styling or both. These concepts are visual references, not a guarantee of how a particular hair texture will behave without styling.',['shaggy','layered','90s-inspired'],{'finish':'choppy'},'Editorial subdivision; no exact modifier measured'),
 ('shaggy','Shaggy bixie haircuts','finish','Shaggy bixies bring soft, piece-like movement to a compact bob-pixie shape.','Shixie and wolf-cut labels can overlap in casual use, but they do not describe one fixed haircut. Compare the actual crown, fringe and nape before deciding which name to use with your stylist.',['choppy','wavy','bangs'],{'finish':'shaggy'},'Direct bixie wolf-cut/shixie comparison context'),
 ('feathered','Feathered bixie haircuts','finish','Feathered bixie references have lighter-looking edges and a soft directional finish around the face and ears.','Pay attention to the silhouette as well as individual strands. A feathered-looking finish may involve styling, so discuss the shape you want when the hair is in its ordinary everyday state.',['layered','natural-grey','over-50'],{'finish':'feathered'},'Editorial subdivision; no exact modifier measured'),
 ('straight','Straight-hair bixies','texture','Straight-hair bixies make the outline and layer transitions especially visible, from sleek longer fronts to softer airy crowns.','Decide whether you prefer a smooth outline or visible separation. Your parting, hair growth direction and strand thickness can affect how a reference translates; the photograph alone cannot assess them.',['classic','fine-hair','long'],{'texture':'straight'},'Editorial collection; adjacent texture context'),
 ('wavy','Wavy bixie haircuts','texture','Wavy bixie references show loose bends and movement within a shorter layered outline.','Compare the natural-looking wave around the crown and temples, then look at the nape. Discuss how your hair behaves as it dries and which parts of the photographed finish involve styling.',['shaggy','easy-styling','long'],{'texture':'wavy'},'Direct bixie haircut wavy hair'),
 ('curly','Curly bixie haircuts','texture','Curly bixies combine a short back with a face-framing curly shape. Each reference keeps the overall silhouette visible.','Curl pattern, density and the way hair contracts as it dries differ from person to person. Use the photos to discuss your preferred outline, fringe and amount of length around the ears.',['wavy','thick-hair','easy-styling'],{'texture':'curly'},'Direct curly bixie'),
 ('fine-hair','Bixie haircuts for fine hair','strand','Fine hair describes strand diameter. These concepts use believable delicate strands rather than treating all fine hair as low-density hair.','Compare the parting, crown separation and perimeter. A styling finish in a generated photo does not show what your own hair will do; discuss the shape and amount of layering you want to maintain.',['thin-hair','layered','straight'],{'strand':'fine'},'Direct fine hair bixie and fine hair pixie-bob'),
 ('thin-hair','Bixie haircuts for thin hair','density','Thin or low-density hair describes how much hair is present. It is a different attribute from having fine individual strands.','Use references with a credible parting and perimeter instead of assuming a very dense photo will translate directly. These are haircut concepts, not hair-loss treatment advice or promises of additional density.',['fine-hair','short','easy-styling'],{'density':'low'},'Direct bixie haircut for thin hair'),
 ('thick-hair','Bixie haircuts for thick hair','density','Thick-hair bixie references explore the outline of a fuller crown and the transition into a shorter graduated nape.','Density and strand diameter are separate qualities. Discuss the amount of fullness you want to keep, the face-framing outline and how the shape feels when you wear your hair naturally.',['curly','layered','shaggy'],{'density':'high'},'Editorial collection; broader thick-hair competitor support'),
 ('bangs','Bixie haircuts with bangs','fringe','Bangs and fringe change the relationship between a bixie’s crown and face frame, from open curtain shapes to fuller front sections.','Use the filters to compare curtain, wispy, side-swept and full-fringe references. Look at the side view too: a fringe can sit differently depending on the parting and growth direction.',['layered','90s-inspired','long'],{'fringe':'any-bangs'},'Direct bixie with bangs / haircut with bangs'),
 ('over-40','Bixie haircuts over 40','age','A collection of original adult hairstyle concepts for people browsing bixie references in their forties and beyond.','Age is a browsing context rather than a haircut rule. Focus on the outline, texture and styling effort you prefer; the same structural questions matter at every age.',['over-50','classic','natural-grey'],{'age_reference':'over-40'},'Editorial collection; no exact bixie modifier measured'),
 ('over-50','Bixie haircuts over 50','age','Original mature bixie concepts show a range of fringes, crown shapes, textures and natural or coloured hair.','Use age-based browsing as one route into the archive. A haircut cannot promise to make someone look younger, and no photo establishes that a cut is suitable for every person over fifty.',['over-60','natural-grey','feathered'],{'age_reference':'over-50'},'Direct bixie haircut over 50'),
 ('over-60','Bixie haircuts over 60','age','Bixie references for mature adults include compact napes, longer face frames and varied finishes without prescribing a single age-based style.','Start with the amount of length you enjoy around your face, then compare the side and back outline. Hair texture, density and preferred upkeep offer more useful detail than age alone.',['over-50','natural-grey','easy-styling'],{'age_reference':'over-60'},'Direct bixie haircut over 60'),
 ('natural-grey','Natural-grey bixie haircuts','colour','Natural-grey and silver-toned bixie concepts keep the hair shape central, with different partings, layers and fringe outlines.','Grey colour is a visual attribute rather than a separate cutting structure. Compare the shape and texture first, and use the colour references for discussion without treating every silver variation as a new haircut.',['over-50','over-60','feathered'],{'colour':'grey'},'Editorial colour collection; no exact modifier measured'),
 ('90s-inspired','90s-inspired bixie haircuts','mood','An original visual edit of 90s-inspired bob-pixie shapes: airy crowns, longer face frames and softly separated fringes.','This collection interprets an era rather than copying a celebrity photograph. Compare the structure you like and discuss a present-day version suited to your preferences and upkeep.',['classic','bangs','choppy'],{'finish':'90s-inspired'},'Direct 90s bixie wording variants'),
 ('round-face','Bixie references for round faces','face','A set of visual bixie references for readers exploring how different fringes, partings and outlines frame a round face.','Face shape is a loose browsing description, not a suitability test. Use these concepts to compare where length sits around the cheeks and jaw and how open or covered you want the forehead.',['long','bangs','layered'],{'face_reference':'round'},'Direct bixie haircut round face'),
 ('undercut','Undercut pixie-bob references','shape','These references combine a genuine bob-pixie outline with a visibly shorter undercut area.','Check both the exposed and covered views when discussing an undercut. Decide how visible you want the contrast to be and ask your stylist about maintaining the transition as the shorter area grows.',['short','long','choppy'],{'finish':'undercut'},'Measured undercut pixie-bob equivalent'),
 ('easy-styling','Bixie haircuts with easy styling','maintenance','Low-maintenance intent starts with the amount of styling you want to do and the outline you are comfortable maintaining.','No haircut is effortless for everyone. Compare natural-looking finishes, your texture and preferred fringe, then discuss both daily styling and appointments to refresh the shape.',['short','wavy','classic'],{'maintenance':'simple'},'Direct low-maintenance pixie-bob/bixie queries'),
]

COLLECTION_DESCRIPTIONS={
 'classic':'Classic bixie haircuts balance a shorter nape with a soft crown and longer face frame. Compare original references and discuss the outline with your stylist.',
 'short':'Short bixie haircuts keep the back compact with longer pieces near the face. Compare the crown, ear coverage and nape in original three-angle references.',
 'long':'Long bixie haircuts lean toward a bob at the face with a shorter layered back. Compare original pixie-bob references and the full front-to-back outline.',
 'layered':'Layered bixie haircuts connect the crown, face frame and nape with varied length. Compare original concepts and discuss the shape rather than a cutting recipe.',
 'choppy':'Choppy bixie haircuts show visible separation within a bob-pixie shape. Compare original references and discuss which details involve the cut or styling.',
 'shaggy':'Shaggy bixie haircuts bring soft layered movement to a compact hybrid shape. Compare original references and understand where shixie and wolf-cut labels differ.',
 'feathered':'Feathered bixie haircuts show soft directional edges around the face and ears. Compare original concepts and discuss the outline and everyday styling finish.',
 'straight':'Straight-hair bixies reveal the outline and layer transitions clearly. Compare original sleek and airy concepts by the crown, face frame and shorter nape.',
 'wavy':'Wavy bixie haircuts show loose bends within a shorter layered shape. Compare original references and discuss your natural wave, fringe and preferred finish.',
 'curly':'Curly bixie haircuts pair a shorter back with a face-framing curly shape. Compare original references by curl pattern, crown outline, fringe and ear coverage.',
 'fine-hair':'Bixie haircuts for fine hair use believable delicate strands. Compare original references by the crown, fringe and perimeter without confusing density with diameter.',
 'thin-hair':'Bixie haircuts for thin hair show credible lower-density references. Compare the parting and perimeter without promises of thicker growth or extra density.',
 'thick-hair':'Bixie haircuts for thick hair explore a fuller crown and shorter nape. Compare original references while keeping density separate from individual strand thickness.',
 'bangs':'Bixie haircuts with bangs include curtain, wispy, side-swept and full fringes. Compare original references by the parting, forehead coverage and side outline.',
 'over-40':'Bixie haircuts over 40 offer original adult shape references. Compare texture, fringe and preferred upkeep without treating age as a haircut suitability rule.',
 'over-50':'Bixie haircuts over 50 show original mature references with varied fringes and finishes. Compare shape and texture without promises of looking younger.',
 'over-60':'Bixie haircuts over 60 offer mature shape references with compact napes and longer face frames. Compare original concepts by texture, fringe and upkeep.',
 'natural-grey':'Natural-grey bixie haircuts keep the shape central with varied layers and partings. Compare original silver-toned concepts without counting colour as a new cut.',
 '90s-inspired':'90s-inspired bixie haircuts feature airy crowns and longer face frames. Browse original fictional concepts and discuss a modern version of the shape you like.',
 'round-face':'Bixie references for round faces compare fringes, partings and cheek-level length. Explore original concepts without treating face shape as a suitability test.',
 'undercut':'Undercut pixie-bob references show a genuine hybrid shape and shorter undercut areas. Compare original concepts and discuss contrast, visibility and upkeep.',
 'easy-styling':'Bixie haircuts with easy styling begin with realistic daily effort. Compare original natural-looking finishes and discuss texture, fringe and shape maintenance.',
}

collections=[]
for slug,title,group,intro,note,related,filters,evidence in COLLECTIONS:
    related_links=[{'route':'/collections/'+x+'/','label':next(c[1] for c in COLLECTIONS if c[0]==x)} for x in related]
    content=blocks(paragraph(intro),heading('What to compare'),paragraph(note),
                   paragraph('Each published reference identifies its available views. '+link('/guides/reading-haircut-references/','Read a front, side and back reference')+' before choosing the details to discuss.'),
                   heading('Explore related shapes'),paragraph(' · '.join(link(x['route'],x['label']) for x in related_links)))
    collections.append({'key':slug,'slug':slug,'name':title,'title':title,'description':intro,'content':content,
                        'seo_title':title,'meta_description':COLLECTION_DESCRIPTIONS[slug],
                        'group':group,'filters':filters,'evidence_status':evidence,'required_unique_images':20,
                        'required_primary_look_ids':[slug+'-'+str(n).zfill(2) for n in range(1,8)],
                        'minimum_complete_looks':7,'planned_unique_view_images':21,
                        'expansion_look_ids':[slug+'-'+str(n).zfill(2) for n in range(8,21)],
                        'provided_primary_images':0,'provided_complete_angle_sets':0,
                        'status':'draft-until-media-reviewed','indexability':'eligible-when-populated',
                        'publish_when':'At least 20 distinct original approved view images from at least 7 complete three-angle looks; original native long edge >=1024, no upscaling or8K claim; useful copy and working links.',
                        'related_links':related_links})

pages=[]
pages.append(page('home','home','Find your next bixie.',blocks(
    paragraph('A visual edit of short hair. Explore original bixie haircut concepts by shape, texture and finish.'),
    paragraph(link('/looks/','Explore the gallery')+' · '+link('/collections/','Browse the collections')),
    paragraph('AI-created hairstyle concepts. Use each reference as a starting point for a conversation with your stylist.')),
    'Discover original bixie haircut concepts, browse image-led collections, save favourite looks and compare the shape from the available views.',kind='home'))
pages.append(page('collections','collections','Bixie haircut collections',blocks(paragraph('Find a useful starting point by texture, density, fringe, length or finish. Each collection focuses on a different part of the bob-pixie shape.'),paragraph('Filters offer narrower preferences without creating a separate page for every combination.'),
    bullets([link('/collections/'+c['slug']+'/',c['name']) for c in collections])),
    'Explore bixie haircut collections by texture, density, length, bangs, finish and age reference, with original imagery and clear hairstyle notes.',kind='directory'))
pages.append(page('looks','looks','The bixie collection',blocks(paragraph('Browse the published hairstyle references. Search by a detail you like, or combine texture, length and fringe preferences.'),paragraph('Photo counts describe the actual published collection. Front, side and back views are labelled only when those separate views are available.')),
    'Browse original bixie haircut ideas, filter by texture, length and bangs, save references and compare the available views before a stylist discussion.',kind='archive'))
pages.append(page('find-your-bixie','find-your-bixie','Find your look',blocks(paragraph('Choose the texture, length and fringe you want to explore. The results are a browsing aid, not a face-analysis service or a guarantee of suitability.'),paragraph(link('/looks/','Browse every published look')),'<!-- wp:bixie/finder /-->'),
    'Choose texture, length and fringe preferences to discover bixie references. This simple gallery helper supports browsing without making suitability promises.',kind='tool'))
pages.append(page('saved-looks','saved-looks','Saved looks',blocks(paragraph('Keep a shortlist for later comparison. Saved looks stay in this browser and do not create an account.'),paragraph('Your saved list can disappear when browser storage is cleared, blocked or unavailable. You can print a reference sheet when you are ready.'),paragraph(link('/looks/','Explore the gallery')),'<!-- wp:bixie/saved-looks /-->'),
    'Review the bixie looks saved in this browser, remove references, compare selected shapes and prepare a print-friendly sheet for your stylist.',kind='tool'))
pages.append(page('compare','compare','Compare bixie looks',blocks(paragraph('Choose two or three published references and compare the crown, face frame, fringe and available views. A missing view is shown as unavailable.'),paragraph('The comparison describes the concepts. It does not predict the result on your own hair.')),
    'Compare two or three saved bixie references by the available views and haircut details, then discuss your preferred shape and upkeep with your stylist.',kind='tool'))
pages.append(page('print','print','Salon reference sheet',blocks(paragraph('Print the selected references or use your browser’s Save as PDF option. Include the concept title, available views and the details you want to discuss.'),paragraph('AI-created hairstyle concepts. These references are not evidence of real salon transformations or guaranteed results.')),
    'Prepare a print-friendly sheet of selected bixie references, available angles and concise haircut notes for a practical conversation with your stylist.',kind='tool'))

guides=[]
def guide(key,title,desc,intro,sections,related):
    content=[paragraph(intro)]
    for h,paras in sections:
        content.append(heading(h))
        for p in paras:
            content.append(bullets(p) if isinstance(p,list) else paragraph(p))
    content.extend([heading('Explore the references'),paragraph(' · '.join(link(r,l) for r,l in related))])
    result=page(key,key,title,blocks(*content),desc,parent='guides',kind='guide',related_links=[{'route':r,'label':l} for r,l in related])
    guides.append(result)

guide('what-is-a-bixie-haircut','What is a bixie haircut?',
      'Understand the bixie haircut, how its bob-pixie shape differs from a pixie or bob, and which visual details to take to a conversation with your stylist.',
      'A bixie is a bob-pixie hybrid. The useful distinction is its shape: a shorter back and crown work with longer pieces around the face. The name does not describe one fixed length, fringe or cutting technique.',[
 ('Bixie, pixie and bob',["A pixie usually presents a more compact overall short shape. A bob usually keeps a more continuous perimeter around the head. A bixie can borrow the shorter back and layered crown of a pixie while retaining the face-framing outline associated with a bob.","The boundaries overlap. A long pixie-bob photo may be a useful bixie reference, but an ordinary bob or close pixie should not be renamed simply to fit a search term."]),
 ('What about a boy bob?',["Boy bob is another informal styling name, commonly used for a compact bob shape. Instead of relying on a label, compare the perimeter, length at the ears, graduation at the nape and proportion of the crown. A boy-bob-versus-bixie comparison is most useful when those actual differences are visible."]),
 ('Read the outline before the finish',[["Front: compare the fringe, parting and pieces beside the cheeks.","Side: compare ear coverage, crown height and the front-to-back transition.","Back: look for the nape shape and how the layers connect above it."],"Colour and a styled finish can attract attention without changing the underlying haircut structure. Start with the shape you like, then discuss texture and upkeep."]),
 ('Use the image as a conversation',["The images here are AI-created concepts featuring fictional adults. They are not client photographs, cutting instructions or guaranteed salon results. Your own texture, density, growth direction and preferred styling routine need a separate discussion with your stylist."])],
 [('/looks/','Browse the bixie collection'),('/collections/classic/','Classic bixies'),('/guides/what-to-ask-your-stylist/','What to ask your stylist')])

guide('what-to-ask-your-stylist','What to ask your stylist',
      'Prepare a clear bixie haircut reference with the shape, fringe, nape and styling details you want to discuss, using the available front, side and back views.',
      'A useful consultation starts with the details you want to keep, change or avoid. Bring a small shortlist of references and say which parts matter to you, rather than asking for a photograph to be reproduced exactly.',[
 ('Describe the shape',[["How much length would you like around your ears and jaw?","Do you prefer a compact back, a softer longer nape or a visible undercut?","Would you like a fuller crown or a flatter, smoother outline?","Which fringe and parting feel comfortable in everyday wear?"]]),
 ('Talk about your ordinary routine',["Describe how you usually dry and wear your hair, how much time you want to spend styling and how often you are comfortable refreshing a short outline. A polished photo does not show the effort required to create its finish.","Ask which visible details come from the haircut and which involve products, tools or styling. Texture and growth direction can make the same reference behave differently on different people."]),
 ('Bring corresponding angles',["Choose a coherent set of views when one is available. Mixing the front of one haircut with the back of an unrelated one can leave important proportions unclear. A single-view reference is still useful if you state which details cannot be seen."]),
 ('Use your shortlist',["Saved looks are stored in your browser. Compare two or three concepts, then print the titles, available views and notes you want to discuss. The sheet keeps the AI-concept disclosure so the reference cannot be mistaken for a real salon transformation."])],
 [('/saved-looks/','Review saved looks'),('/compare/','Compare the shapes'),('/guides/reading-haircut-references/','Read three-angle references')])

guide('styling-a-bixie','Styling a bixie',
      'Explore practical bixie styling choices for straight, wavy and curly references, with realistic notes about finish, daily effort and maintenance.',
      'A bixie can look smooth, airy, wavy or curly. Before choosing a styling routine, distinguish the shape of the cut from the finish in the photograph and decide what you want to do on an ordinary day.',[
 ('Start with the finish you prefer',["Choose a reference close to your natural texture when you want a straightforward starting point. A smooth finish on naturally curly hair, or a highly textured finish on very straight hair, can involve extra styling. No photo establishes that a haircut is low-maintenance for everyone."]),
 ('Straight-hair references',["Compare a sleek outline with a separated, airy finish. A parting or tuck can change how the front pieces sit, while the underlying nape and crown remain the same. Discuss the amount of movement you want without assuming every lifted crown is created by the haircut alone."]),
 ('Wavy and curly references',["Look at where the wave or curl sits around the face and crown. Your natural pattern and the way it contracts as it dries affect the outline. Discuss the preferred dry length and fringe shape with your stylist rather than treating a generated reference as a measurement."]),
 ('Keep the routine realistic',["Follow the instructions for any product or tool you choose. If you use heat, discuss appropriate handling and protection rather than assuming a stronger setting improves the result. This site does not test or recommend particular products.","The <a href=\"https://www.aad.org/public/everyday-care/hair-scalp-care/hair/healthy-hair-tips\">American Academy of Dermatology’s hair-care guidance</a> is an external starting point for general care. It does not endorse this site or these generated haircut concepts."]),
 ('What low maintenance means',["Daily styling effort and appointments to maintain the outline are different questions. Use the easy-styling collection to compare natural-looking finishes, then decide which fringe, length and upkeep tradeoffs suit your preferences."])],
 [('/collections/easy-styling/','Easy-styling references'),('/collections/wavy/','Wavy bixies'),('/collections/curly/','Curly bixies')])

guide('fine-vs-thin-hair','Fine hair versus thin hair',
      'Separate fine strand diameter from thin or low-density hair when choosing bixie references, and compare the parting, perimeter and styling finish clearly.',
      'Fine hair and thin hair describe different things. Fine refers to the diameter of an individual strand; thin or low-density hair refers to how much hair is present. Someone can have fine strands and a relatively dense head of hair.',[
 ('Fine, coarse and dense',["Coarse and fine are strand descriptions. Dense and low-density describe the amount of hair. Casual styling names often blur these distinctions, so a useful reference should identify which visual quality is actually being discussed."]),
 ('Compare believable references',["For fine strands, examine the separation around the fringe and crown. For lower density, consider the visible parting and perimeter. A very full generated hairstyle is not proof that a particular cut will create the same apparent density on your hair."]),
 ('Discuss the outline',[["How much layering would you like to see?","Which areas would you prefer to keep visually more continuous?","How do you usually wear your parting and fringe?","Does the desired photographed finish involve styling you want to do?"]]),
 ('Keep the claim limited',["These collections are haircut inspiration. They do not diagnose changing density, recommend hair-loss treatments or promise thicker growth. A sudden or concerning hair change belongs in a discussion with an appropriate healthcare professional."])],
 [('/collections/fine-hair/','Fine-hair bixies'),('/collections/thin-hair/','Thin-hair bixies'),('/collections/thick-hair/','Thick-hair references')])

guide('reading-haircut-references','How to read haircut references',
      'Read front, side and back bixie references by comparing the fringe, crown, ear coverage and nape, and understand what a single image cannot show.',
      'A front portrait can show a fringe beautifully while hiding the part of the haircut that makes it a bixie. Corresponding views help you understand the whole outline and the details that remain uncertain.',[
 ('Front: fringe and face frame',["Compare the parting, fringe coverage and the pieces beside the cheeks. Notice whether the hair is tucked or pushed away from the face: styling can temporarily hide part of the outline."]),
 ('Side: the transition',["The side view shows how the front connects to the crown and back. Look at ear coverage, the position of the longer pieces and the relationship between the crown and shorter nape."]),
 ('Back: crown and nape',["The back view helps you compare a compact, graduated or softer nape. It should belong to the same fictional model and same haircut as the front and side. A different crop of a front image is not a back view."]),
 ('Know what remains unknown',["Even three generated views do not reveal a cutting method, your hair’s growth direction or the exact salon result. Images are references for discussion. A missing view should remain labelled unavailable rather than being invented or replaced with another look."]),
 ('Build a reference sheet',["Keep two or three coherent concepts and note the details you prefer from each. Print the available views and titles so the shape can be discussed without relying on a scrolling screen."])],
 [('/looks/','Browse the available looks'),('/compare/','Compare references'),('/print/','Prepare a print sheet')])

guide('growing-out-a-bixie','Growing out a bixie',
      'Consider the changing crown, fringe and nape as a bixie grows out, with useful reference questions for shaping choices and maintenance discussions.',
      'Growing out a bixie is a change in shape as well as length. Its shorter nape and crown may reach different stages from the longer face-framing pieces, so the outline can change before it resembles a continuous bob.',[
 ('Decide your next shape',["Choose whether you want to keep a short layered form, move toward a longer bixie or work toward a bob. A clear target helps you describe which areas you want to preserve and which transitions are bothering you."]),
 ('Look at the back as well as the front',["Fringe length can be easy to see, while the nape and side transition are harder to assess from your own front view. Use side and back references when discussing a shape adjustment rather than judging progress by the fringe alone."]),
 ('Ask about maintenance',["A shaping appointment can address the outline, but the details depend on your starting cut and target. There is no fixed grow-out timetable here and no promised growth rate. Ask what can be adjusted while preserving the length you want to keep."]),
 ('Pixie grow-out references',["Pixie grow-out articles may offer useful comparison, but a pixie and a bixie do not always start from the same proportions. Compare the actual nape, crown and face frame before transferring a staged photo sequence to your own haircut."]),
 ('Keep references practical',["Choose a current reference and a target reference, and write the difference you want to discuss. The site’s fictional concepts illustrate possible outlines; they are not a documented before-and-after transformation."])],
 [('/collections/long/','Long bixie references'),('/collections/classic/','Classic shapes'),('/guides/what-to-ask-your-stylist/','Consultation questions')])

guide('bixie-shixie-wolf-cut','Bixie, shixie and wolf cut',
      'Compare bixie, shixie and wolf-cut labels by the actual crown, fringe, face frame and nape, without treating overlapping hairstyle names as exact synonyms.',
      'Haircut names are shorthand. Bixie, shixie and wolf cut can appear together in inspiration searches, but the useful question is what the photograph shows rather than which fashionable name is attached to it.',[
 ('A bixie starts with a bob-pixie balance',["Look for the relationship between a compact back and longer face-framing sections. A softer or more separated finish can still sit on that bob-pixie structure."]),
 ('Shaggy and shixie descriptions',["Shaggy usually describes visible layered movement and a less continuous-looking finish. Shixie is often used as shorthand for a shag-and-pixie combination. These informal labels do not establish one cutting technique or fixed length."]),
 ('Wolf-cut references',["Wolf-cut descriptions commonly emphasize a more strongly layered shape. Some short references may overlap with shaggy bixie concepts, while others have proportions that do not belong in a bixie collection. Keep the actual outline visible and label the reference accurately."]),
 ('Compare the same details',[["How long are the pieces around the face?","How compact is the nape relative to the crown?","Where is the fringe, and how does it connect to the sides?","Is the separated finish a structure you want, a styled effect, or both?"]]),
 ('Use a precise reference',["Bring the photo and the details you like. A stylist can discuss whether the label is useful; the site does not promise that using a name alone will produce a particular result."])],
 [('/collections/shaggy/','Shaggy bixie concepts'),('/collections/choppy/','Choppy references'),('/guides/what-is-a-bixie-haircut/','Bixie versus pixie and bob')])

pages.append(page('guides','guides','The short-hair notes',blocks(paragraph('Short supporting guides for reading a reference, comparing shape and preparing a useful conversation with your stylist.'),bullets([link('/guides/'+g['slug']+'/',g['title']) for g in guides])),
    'Read concise bixie haircut guides on shape, styling, fine versus thin hair, three-angle references, consultation questions and growing out a short cut.',kind='directory'))
pages.extend(guides)

pages.append(page('about','about','About Bixie Haircut',blocks(paragraph('Bixie Haircut is an image-led inspiration library focused on the bob-pixie hybrid. Browse the haircut shape, compare available views and save a small shortlist of details you want to discuss.'),paragraph('The hairstyle imagery is created with AI and depicts fictional adults. The collection does not present real clients, salon transformations, celebrity photographs or professional endorsements.'),heading('A useful visual reference'),paragraph('Each concept is described by its visible shape and attributes. Colour and additional angles are not counted as entirely new haircut structures. Collections organize related references without making a separate page for every search spelling.'),paragraph(link('/image-policy/','How the images are created')+' · '+link('/guides/','Read the short-hair notes'))),
    'Learn how Bixie Haircut organizes original AI-created hairstyle concepts into a clear visual library, with honest image labels and practical reference notes.'))
pages.append(page('image-policy','image-policy','Image policy',blocks(paragraph('Our hairstyle pictures are AI-created concepts featuring fictional adults. They are inspiration references rather than photographs of real clients or verified salon results.'),heading('Original assets and clear counts'),paragraph('A final image is counted once as a source asset. Resized files, thumbnail crops and format conversions are renditions, not extra original photographs. A different angle of one hairstyle is a view of that concept, not a separate haircut.'),heading('Views and consistency'),paragraph('Front, side and back labels are used only when the corresponding views are available and have been reviewed for consistency. A missing view is marked unavailable. Images with the wrong identity, fringe, colour or shape should remain unpublished until corrected.'),heading('Use as a reference'),paragraph('Generated hair and skin detail can contain imperfections. No picture guarantees that a salon can reproduce the concept exactly or that the style will suit every viewer. Discuss your texture, density, growth direction and upkeep with your stylist.'),heading('Sources and rights'),paragraph('The original collection is created for this project. Competitor photographs, unlicensed social-media images and fabricated celebrity portraits are not source material. Requests about a specific image can be sent through the site’s configured contact details.')),
    'Read how Bixie Haircut creates and labels original AI hairstyle concepts, counts source assets, reviews angles and explains the limits of visual references.'))
pages.append(page('privacy','privacy','Privacy policy',blocks(paragraph('This policy describes the package’s default visitor tools. The site owner must confirm their hosting practices and update this page before a public launch, especially if adding analytics, advertising, forms or external services.'),heading('Saved looks'),paragraph('The favourites tool stores selected look IDs in your browser using local storage. The packaged feature does not create a visitor account or send that saved list to the site. Clearing or blocking browser storage can remove the list.'),heading('WordPress and hosting'),paragraph('WordPress may use cookies for logged-in administration and other core functions when enabled. Your hosting provider can process request information in server logs. The owner should add the provider’s retention and contact information here rather than promising logging practices that have not been verified.'),heading('Analytics and contact'),paragraph('The package does not automatically install third-party analytics or advertising. Contact details require the owner’s genuine configuration. If the owner later adds a form, newsletter or tracking service, this policy must explain the data it processes.'),heading('Your browser controls'),paragraph('You can clear the saved-look list through the gallery tools or remove browser site data. Use the owner’s published contact details for questions about additional data processing on the live site.')),
    'Understand the default saved-look browser storage and the privacy details the owner must verify for WordPress, hosting and any services added before launch.',status='draft',launch_dependencies=['owner legal/contact details','hosting log policy review']))
pages.append(page('disclaimer','disclaimer','Reference disclaimer',blocks(paragraph('Bixie Haircut provides visual hairstyle inspiration and general descriptive information. It does not provide a personal hair assessment, professional consultation, medical diagnosis or guaranteed salon outcome.'),paragraph('AI-created concepts can illustrate a shape without demonstrating how the same haircut will behave on your own texture or density. Informal style names can overlap; discuss the actual details and your routine with a qualified stylist.'),paragraph('No ranking, indexing, hair-growth, age-related or suitability guarantee is attached to an image or collection. External information links do not imply an endorsement of this site.')),
    'Understand the limits of Bixie Haircut’s AI-created hairstyle references and descriptive guides before using a concept in a personal stylist conversation.'))
pages.append(page('contact','contact','Contact',blocks(paragraph('The site owner’s genuine contact details must be configured before this page is published. There is no packaged message form and no invented email address.'),paragraph('Once configured, use the published details for image questions, corrections or site enquiries. Please identify the concept title or page so the owner can review the issue.')),
    'Contact the Bixie Haircut site owner about an image, correction or website question using the genuine details configured before public launch.',kind='contact',status='draft',launch_dependencies=['owner_contact_email'],publish_when='A genuine owner-controlled contact address is configured; replace configuration text with the actual contact block.'))

# A page per collection is supplied so a compatible importer can make the copy
# editable in Gutenberg and connect it to the collection taxonomy gallery.
for c in collections:
    library='<!-- wp:bixie/library '+json.dumps({'collection':c['key'],'perPage':12},separators=(',',':'))+' /-->'
    pages.append(page('collection-'+c['key'],c['slug'],c['name'],c['content']+'\n\n'+library,c['meta_description'],parent='collections',kind='collection',status='draft',gallery_collection=c['key'],
                      required_unique_images=20,indexability='eligible-when-populated',publish_when=c['publish_when']))

# These are production concepts, not posts and not generated/approved imagery.
crowns=['soft rounded','airy separated','compact rounded','directional lifted','smooth flat','lightly tousled']
napes=['short graduated','soft tapered','compact squared','curved graduated','low blended','textured tapered']
fringes=['wispy','side-swept','curtain','full','no-bangs','short open','long divided','angled','light broken','swept-back']
ear_shapes=['ear-revealing temple pieces','half-covered ears with curved temple pieces','ear-covering face frame']
textures=['straight','wavy','curly','coily']
briefs=[]
signatures=set()
for ci,c in enumerate(collections):
    for n in range(1,21):
        absolute=ci*20+n-1
        # Unique structure labels describe intended haircut design differences;
        # age and colour are not used as the sole distinctness basis.
        crown=crowns[absolute%len(crowns)]
        nape=napes[(absolute//len(crowns))%len(napes)]
        fringe=fringes[(absolute//(len(crowns)*len(napes)))%len(fringes)]
        ear=ear_shapes[(absolute//(len(crowns)*len(napes)*len(fringes)))%len(ear_shapes)]
        signature=' | '.join([crown,nape,fringe,ear,str(absolute%5)+'-crown-to-front-proportion'])
        # The signature is an editorial design brief, not proof that a generator
        # has delivered or a stylist has validated a distinct construction.
        assert signature not in signatures,signature
        signatures.add(signature)
        look_id=c['key']+'-'+str(n).zfill(2)
        attrs={'texture':c['filters'].get('texture',textures[n%4]),'strand':c['filters'].get('strand','medium'),
               'density':c['filters'].get('density','medium'),'length':c['filters'].get('length',['short','medium','long'][n%3]),
               'fringe':fringe,'colour':['brunette','blonde','copper','dark','grey'][n%5],
               'finish':c['filters'].get('finish','natural'),'age_reference':c['filters'].get('age_reference','adult'),
               'face_reference':c['filters'].get('face_reference','unspecified'),'maintenance':c['filters'].get('maintenance','discuss')}
        if c['key']=='natural-grey': attrs['colour']='grey'
        if c['key']=='bangs' and attrs['fringe'] in ['no-bangs','swept-back']: attrs['fringe']='side-swept'
        title=c['name'].replace('haircuts','reference').replace('haircut','reference')+' '+str(n).zfill(2)
        front_alt=f'Front reference of a {attrs["texture"]} bixie with a {crown} crown and {attrs["fringe"]} fringe.'
        side_alt=f'Side reference of the same bixie, showing {ear} and the transition to a {nape} nape.'
        back_alt=f'Back reference of the same bixie, showing the {nape} nape and {crown} crown outline.'
        prompt=f'Create one original editorial photograph of a fictional adult with a true bob-pixie hybrid. Primary collection: {c["name"]}. Design: {signature}. Attributes: {json.dumps(attrs)}. Neutral warm stone setting, natural skin, soft studio daylight, full head/hair/ears/nape visible without crop. Fully covered modest outfit, closed high neckline, long sleeves, no exposed shoulders, chest or back. Portrait 4:5, no words, watermark or logos. Do not substitute an ordinary bob, close pixie or long wolf cut. Render a clearly distinct haircut concept rather than only changing colour or model age. Use the highest available original native resolution, at least1024long edge; record actual dimensions, do not upscale and do not claim native8K.'
        briefs.append({'key':look_id,'slug':look_id,'title':title,'primary_collection':c['key'],'collections':[c['key']],
                       'meta':{**attrs,'ai_concept':True},'shape_brief':{'crown':crown,'nape':nape,'fringe':attrs['fringe'],'ear_outline':ear,'distinctness_basis':signature},
                       'status':'required-not-generated','scope':'launch-target' if n<=7 else 'expansion-plan','required_primary_images':1,'required_three_angle_images':3,
                       'provided_media_ids':[], 'publish':False, 'generation_prompt':prompt,
                       'images':[{'key':look_id+'-'+angle,'file':None,'angle':angle,'status':'required-not-generated','alt_spec':alt,'caption_spec':cap,'width':None,'height':None,'review_status':'not-reviewed'}
                                 for angle,alt,cap in [('front',front_alt,'Front: compare the fringe, parting and face frame.'),('side',side_alt,'Side: compare ear coverage and the crown-to-nape transition.'),('back',back_alt,'Back: compare the nape outline and graduation.')]],
                       'review_checks':['actual bob-pixie hybrid','distinct structure from other concepts','credible texture/density','complete visible hair silhouette','same identity and haircut across supplied angles','no distorted ears/strands','alt/caption updated to actual image'],
                       'stylist_note':'Discuss the preferred face frame, crown, nape and ordinary styling routine. This generated concept is not a guaranteed result.'})

route_overrides={'/guides/bixie-vs-pixie-vs-bob/':'/guides/what-is-a-bixie-haircut/',
                 '/guides/bixie-vs-shixie-vs-wolf-cut/':'/guides/bixie-shixie-wolf-cut/',
                 '/guides/reading-haircut-references/':'/guides/reading-haircut-references/',
                 '/collections/wavy-hair/':'/collections/wavy/','/collections/curly-hair/':'/collections/curly/'}
keyword_map=[]
for csvfile in ['bixie_keyword_coverage.csv','supporting_keyword_candidates.csv']:
    with (RESEARCH/csvfile).open(newline='') as f:
        for r in csv.DictReader(f):
            route=route_overrides.get(r['suggested_route'],r['suggested_route'])
            disposition='mapped-context' if r['classification'].startswith('Selected') else 'mapped-canonical'
            if r['classification'].startswith('Excluded'): disposition='excluded-celebrity-intent';route=None
            elif r['classification'].startswith('Adjacent'): disposition='supporting-comparison-only'
            elif r['classification'].startswith('Historical'): disposition='historical-context-only'
            keyword_map.append({'keyword':r['keyword'],'classification':r['classification'],'disposition':disposition,
                                'canonical_route':route,'keyword_magic_volume':r['keyword_magic_volume'],
                                'keyword_magic_difficulty':r['keyword_magic_difficulty'],
                                'keyword_magic_snapshot':r['keyword_magic_snapshot'],
                                'positions_export_volume':r['positions_export_volume'],'positions_export_kd':r['positions_export_kd'],
                                'organic_positions':r['best_exported_organic_position_by_competitor'],'sources':r['sources'],'notes':r['notes']})

catalog={'version':'1.0.0','schema_version':1,'site':{'title':'BIXIE HAIRCUT','description':'An original visual library of bixie haircut concepts.','home_slug':'home','posts_slug':None,
         'language':'en_US','image_disclosure':'AI-created hairstyle concepts.','contact_email':None,'domain_status':'owner supplied domain/hosting not verified'},
         'collections':collections,'pages':pages,'looks':[],
         'canonical_keyword_map':keyword_map,
         'production_manifest':'production-briefs.json','provided_media_manifest':None,
         'counts':{'required_collections':len(collections),'minimum_unique_collection_view_images':len(collections)*20,
                   'required_complete_launch_looks':len(collections)*7,'planned_launch_view_images':len(collections)*7*3,
                   'expansion_look_briefs':len(briefs),'expansion_view_briefs':len(briefs)*3,
                   'provided_unique_primary_collection_images':0,'provided_importable_looks':0,'provided_complete_three_angle_sets':0,
                   'supporting_guides':len(guides),'editable_page_records':len(pages),'reviewed_relevant_and_excluded_terms':len(keyword_map)},
         'requirements':{'require_complete_angles':True,'minimum_collection_photos':20,'minimum_native_long_edge':1024,'native_resolution_tier':'generator-native','no_upscaling':True,'no_8k_claim':True,'minimum_complete_looks_per_collection':7,'allow_source_reuse_between_primary_collections':False},
         'import_policy':{'owner_initiated':True,'preserve_owner_edits':True,'idempotent_keys':True,'missing_media':'draft'},
         'indexability':{'populated_editorial_pages':'eligible','complete_reviewed_looks':'eligible','empty_collections':'draft or noindex','incomplete_view_sets':'draft where three-view scope required','internal_search':'noindex','faceted_combinations':'noindex','saved_compare_print':'noindex','contact_privacy':'owner review before publication','paginated_archives':'self canonical when indexable'},
         'verification_limits':['No fresh Google US SERP audit performed.','Supplied volume/KD estimates have different snapshots.','Primary AAD/Google documentation retrieval returned proxy403 in this environment; no live external-source verification claimed.','Generated/reviewed media counts must be reconciled from actual asset files before publication.','Contact and hosting/privacy details require genuine owner configuration.'],
         'external_editorial_references':[{'url':'https://www.aad.org/public/everyday-care/hair-scalp-care/hair/healthy-hair-tips','purpose':'general hair-care reference','retrieval_status':'proxy403, current content not verified'}]}

for p in catalog['pages']:
    if p['key']=='looks': p['content']+='\n\n<!-- wp:bixie/library /-->'
    if p['key'] in ['compare','print']: p['content']+='\n\n<!-- wp:bixie/saved-looks /-->'
    if p['key']=='home': p['status']='draft';p['publish_when']='Approved complete original launch media and required collection photo thresholds; original native long edge >=1024, no upscale or8Kclaim.'

# Preserve explicit integration/media configuration added after the editorial
# build. This is not a WordPress import and must not reset asset handoffs.
existing_path=OUT/'catalog.json'
if existing_path.exists():
    existing=json.loads(existing_path.read_text())
    catalog['requirements'].update(existing.get('requirements',{}))
    for k,v in existing.get('site',{}).items():
        if k not in catalog['site']: catalog['site'][k]=v
    if existing.get('provided_media_manifest'):
        catalog['provided_media_manifest']=existing['provided_media_manifest']
    if existing.get('looks'):
        catalog['looks']=existing['looks']
    for k,v in existing.get('counts',{}).items():
        if k.startswith('provided_'): catalog['counts'][k]=v
(OUT/'catalog.json').write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
(OUT/'production-briefs.json').write_text(json.dumps({'version':'1.0.0','status':'planning-only','launch_look_count':154,'launch_view_image_count':462,'expansion_concept_brief_count':len(briefs),'required_views_per_look':3,'briefs':briefs},indent=2,ensure_ascii=False)+'\n')
with (OUT/'keyword-map.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(keyword_map[0]));w.writeheader();w.writerows(keyword_map)
print(json.dumps(catalog['counts'],indent=2))
subprocess.run([sys.executable,str(OUT/'apply_guide_photo_requirements.py')],check=True)
