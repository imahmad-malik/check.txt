/* Native Gutenberg controls. No build step, generated block markup, or automatic media approval. */
(function (wp) {
  'use strict';
  if (!wp || !wp.blocks || !wp.element || !wp.components || !wp.blockEditor) return;
  const el = wp.element.createElement;
  const Fragment = wp.element.Fragment;
  const useEffect = wp.element.useEffect;
  const useRef = wp.element.useRef;
  const InspectorControls = wp.blockEditor.InspectorControls;
  const useBlockProps = wp.blockEditor.useBlockProps;
  const PanelBody = wp.components.PanelBody;
  const TextControl = wp.components.TextControl;
  const TextareaControl = wp.components.TextareaControl;
  const ToggleControl = wp.components.ToggleControl;
  const RangeControl = wp.components.RangeControl;
  const Button = wp.components.Button;
  const Notice = wp.components.Notice;
  const ServerSideRender = wp.serverSideRender && (wp.serverSideRender.default || wp.serverSideRender);
  const positive = function (value) {
    const parsed = Number(value);
    return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : 0;
  };
  const preview = function (name, props, description) {
    const wrapperProps = useBlockProps ? useBlockProps() : { className: 'bixie-editor-preview' };
    const contextId = positive(props.context && props.context.postId);
    return el('div', wrapperProps,
      el('p', { style: { fontSize: '12px', opacity: .75 } }, description + ' Preview uses the last saved WordPress content.'),
      ServerSideRender ? el(ServerSideRender, {
        block: name, attributes: props.attributes,
        urlQueryArgs: contextId ? { post_id: contextId } : undefined
      }) : el('p', null, 'A live server preview is unavailable in this editor. Save and view the page to see this block.')
    );
  };
  const register = function (name, settings) {
    if (!wp.blocks.getBlockType(name)) wp.blocks.registerBlockType(name, Object.assign({
      apiVersion: 3, category: 'widgets', supports: { html: false }, save: function () { return null; }
    }, settings));
  };
  register('bixie/library', {
    title: 'Bixie Look Library', icon: 'images-alt2',
    description: 'A filterable gallery of published, approved hairstyle records.',
    attributes: {
      collection: { type: 'string', default: '' }, perPage: { type: 'number', default: 12 },
      excludeLookIds: { type: 'array', items: { type: 'number' }, default: [] },
      showViews: { type: 'boolean' }
    },
    edit: function (props) {
      return el(Fragment, null,
        el(InspectorControls, null, el(PanelBody, { title: 'Gallery settings' },
          el(TextControl, {
            label: 'Collection slug', value: props.attributes.collection || '',
            help: 'Leave empty for all approved looks, or enter an existing collection slug.',
            onChange: function (value) { props.setAttributes({ collection: value }); }
          }),
          el(RangeControl, {
            label: 'Looks per page', value: props.attributes.perPage || 12, min: 1, max: 48,
            onChange: function (value) { props.setAttributes({ perPage: Math.min(48, positive(value) || 12) }); }
          }),
          el(ToggleControl, {
            label: 'Show front, side and back photographs',
            checked: typeof props.attributes.showViews === 'boolean' ? props.attributes.showViews : !!props.attributes.collection,
            help: 'Collection galleries show all available views by default. Each photograph uses its real proportions.',
            onChange: function (value) { props.setAttributes({ showViews: !!value }); }
          })
        )),
        preview('bixie/library', props, 'Visitors can filter real, published looks and save a browser-local shortlist.')
      );
    }
  });
  register('bixie/look-meta', {
    title: 'Bixie Look Details', icon: 'id-alt',
    description: 'The saved metadata and optional photography for a real hairstyle record.',
    attributes: { lookId: { type: 'number', default: 0 }, showImages: { type: 'boolean', default: false } },
    usesContext: ['postId', 'postType'],
    edit: function (props) {
      return el(Fragment, null,
        el(InspectorControls, null, el(PanelBody, { title: 'Look details settings' },
          el(TextControl, {
            label: 'Look ID override', type: 'number', min: 0, step: 1,
            value: String(props.attributes.lookId || 0),
            help: 'Use 0 for the current look. A positive ID displays that existing look.',
            onChange: function (value) { props.setAttributes({ lookId: positive(value) }); }
          }),
          el(ToggleControl, {
            label: 'Show published look photographs', checked: props.attributes.showImages === true,
            help: 'Displays actual available images and their recorded angles.',
            onChange: function (value) { props.setAttributes({ showImages: !!value }); }
          })
        )),
        preview('bixie/look-meta', props, 'Look metadata comes from its WordPress record.')
      );
    }
  });
  register('bixie/saved-looks', {
    title: 'Bixie Saved Looks', icon: 'heart',
    description: 'The visitor’s browser-local shortlist, comparison, and salon sheets.',
    edit: function (props) { return preview('bixie/saved-looks', props, 'Every visitor sees their own browser-local saved looks; this editor does not invent saved records.'); }
  });
  register('bixie/finder', {
    title: 'Bixie Haircut Finder', icon: 'search',
    description: 'A texture, length, and fringe finder linked to the real look library.',
    edit: function (props) { return preview('bixie/finder', props, 'A simple finder sends visitors to matching gallery results.'); }
  });
  register('bixie/contact-details', {
    title: 'Bixie Contact Details', icon: 'email',
    description: 'The genuine contact details configured in Bixie settings.',
    edit: function (props) { return preview('bixie/contact-details', props, 'Displays the configured contact details, or a truthful notice when they have not been supplied.'); }
  });

  if (!wp.data || !wp.editPost || !wp.editPost.PluginDocumentSettingPanel || !wp.plugins) return;
  const DocumentPanel = wp.editPost.PluginDocumentSettingPanel;
  const MediaUpload = wp.blockEditor.MediaUpload;
  const MediaUploadCheck = wp.blockEditor.MediaUploadCheck;
  const fields = [
    ['texture', 'Texture', 'Use the matching filter value, such as fine, straight, wavy, curly, or coily.'],
    ['length', 'Length', 'Use the matching library filter value.'],
    ['fringe', 'Fringe', 'Use the matching library filter value.'],
    ['colour', 'Colour', 'Use the matching library filter value.'],
    ['density', 'Density'], ['strand', 'Strand'], ['finish', 'Finish'],
    ['age_reference', 'Age reference'], ['face_reference', 'Face reference'],
    ['primary_collection', 'Primary collection slug', 'Use an existing collection slug. Photography counts toward this primary collection; leave empty to use the first assigned collection.']
  ];
  const roles = ['front', 'side', 'back'];
  const walkBlocks = function (blocks, callback) {
    (blocks || []).forEach(function (block) {
      callback(block);
      if (block.innerBlocks && block.innerBlocks.length) walkBlocks(block.innerBlocks, callback);
    });
  };
  const namedImages = function (blocks) {
    const result = [];
    walkBlocks(blocks, function (block) {
      const name = block.attributes && block.attributes.metadata && block.attributes.metadata.name;
      if (block.name !== 'core/image' || typeof name !== 'string') return;
      const angle = name.replace(/^bixie-/, '');
      if (name === 'bixie-' + angle && roles.includes(angle)) result.push({ block: block, angle: angle });
    });
    return result;
  };
  const plainCaption = function (value) {
    return String(value || '').replace(/<[^>]*>/g, '').replace(/&(?:amp|lt|gt|quot|apos|#39|#\d+|#x[\da-f]+);/gi, function (entity) {
      const named = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'", '&#39;': "'" };
      if (named[entity.toLowerCase()]) return named[entity.toLowerCase()];
      const match = entity.match(/^&#(x[\da-f]+|\d+);$/i);
      if (!match) return entity;
      const code = match[1][0].toLowerCase() === 'x' ? parseInt(match[1].slice(1), 16) : Number(match[1]);
      return code > 0 && code <= 0x10ffff ? String.fromCodePoint(code) : '';
    });
  };
  const richCaption = function (value) {
    return String(value || '').replace(/[&<>"']/g, function (character) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character];
    });
  };
  const sourceURL = function (value) {
    if (typeof value !== 'string' || !value.trim()) return '';
    try {
      const url = new URL(value, window.location.href);
      return ['https:', 'http:'].includes(url.protocol) ? url.href : '';
    } catch (_) { return ''; }
  };
  const PhotoSlot = function (props) {
    const attachmentId = positive(props.entry && props.entry.id);
    const media = wp.data.useSelect(function (select) {
      return attachmentId ? select('core').getMedia(attachmentId) : null;
    }, [attachmentId]);
    const label = props.angle.charAt(0).toUpperCase() + props.angle.slice(1);
    const choose = function (selected) {
      const selectedId = positive(selected && selected.id);
      if (!selectedId) return;
      props.onChange({ id: selectedId, angle: props.angle, caption: props.entry ? String(props.entry.caption || '') : '' }, selected);
    };
    const imageURL = media && sourceURL(media.source_url);
    return el('section', { style: { marginBottom: '24px' } },
      el('h4', { style: { marginBottom: '8px' } }, label + ' photograph'),
      imageURL ? el('img', {
        src: imageURL, alt: media.alt_text || label + ' photograph',
        style: { display: 'block', width: '100%', height: 'auto', maxHeight: '200px', objectFit: 'contain', marginBottom: '8px' }
      }) : null,
      attachmentId ? el('p', { style: { fontSize: '12px' } }, 'Actual WordPress attachment #' + attachmentId) : null,
      MediaUpload && MediaUploadCheck ? el(MediaUploadCheck, null, el(MediaUpload, {
        allowedTypes: ['image'], value: attachmentId || undefined, onSelect: choose,
        render: function (controls) {
          return el(Button, { variant: 'secondary', onClick: controls.open }, (attachmentId ? 'Replace ' : 'Choose ') + label.toLowerCase() + ' photograph');
        }
      })) : el('p', null, 'Use the WordPress Media Library to add photographs.'),
      attachmentId ? el(Fragment, null,
        el(TextControl, {
          label: label + ' caption', value: String(props.entry.caption || ''),
          onChange: function (caption) { props.onChange({ id: attachmentId, angle: props.angle, caption: caption }); }
        }),
        el(Button, { variant: 'tertiary', isDestructive: true, onClick: function () { props.onChange(null); } }, 'Remove ' + label.toLowerCase() + ' from this look')
      ) : null
    );
  };
  const LookSettings = function () {
    const state = wp.data.useSelect(function (select) {
      const editor = select('core/editor');
      const blockEditor = select('core/block-editor');
      return {
        type: editor.getCurrentPostType(), postId: editor.getCurrentPostId ? editor.getCurrentPostId() : 0,
        meta: editor.getEditedPostAttribute('meta') || {},
        blocks: blockEditor && blockEditor.getBlocks ? blockEditor.getBlocks() : []
      };
    }, []);
    const dispatch = wp.data.useDispatch('core/editor');
    const blockDispatch = wp.data.useDispatch('core/block-editor');
    const canonicalSeen = useRef(false);
    const currentPost = useRef(0);
    const meta = state.meta;
    const setMeta = function (key, value) {
      const latest = wp.data.select('core/editor').getEditedPostAttribute('meta') || meta;
      dispatch.editPost({ meta: Object.assign({}, latest, { [key]: value }) });
    };
    const images = Array.isArray(meta.bixie_images) ? meta.bixie_images : [];
    const canonical = namedImages(state.blocks);
    const blockSignature = JSON.stringify(canonical.map(function (entry) {
      return { angle: entry.angle, id: positive(entry.block.attributes.id), caption: plainCaption(entry.block.attributes.caption) };
    }));
    const metaSignature = JSON.stringify(images);
    useEffect(function () {
      if (currentPost.current !== state.postId) {
        currentPost.current = state.postId;
        canonicalSeen.current = false;
      }
      if (state.type !== 'bixie_look') { canonicalSeen.current = false; return; }
      const latestBlocks = wp.data.select('core/block-editor').getBlocks();
      const latestCanonical = namedImages(latestBlocks);
      if (latestCanonical.length) canonicalSeen.current = true;
      if (!canonicalSeen.current) return;
      const latestMeta = wp.data.select('core/editor').getEditedPostAttribute('meta') || {};
      const latestImages = Array.isArray(latestMeta.bixie_images) ? latestMeta.bixie_images : [];
      const next = latestImages.filter(function (entry) { return entry && !roles.includes(entry.angle); });
      roles.forEach(function (angle) {
        const match = latestCanonical.find(function (entry) { return entry.angle === angle && positive(entry.block.attributes.id); });
        if (!match) return;
        next.push({ id: positive(match.block.attributes.id), angle: angle, caption: plainCaption(match.block.attributes.caption) });
      });
      if (JSON.stringify(next) !== JSON.stringify(latestImages)) setMeta('bixie_images', next);
    }, [state.type, state.postId, blockSignature, metaSignature]);
    if (state.type !== 'bixie_look') return null;
    const setAngle = function (angle, next, attachment) {
      const latestMeta = wp.data.select('core/editor').getEditedPostAttribute('meta') || {};
      const latestImages = Array.isArray(latestMeta.bixie_images) ? latestMeta.bixie_images : [];
      const updated = latestImages.filter(function (entry) { return entry && entry.angle !== angle; });
      const latestBlocks = wp.data.select('core/block-editor').getBlocks();
      const match = namedImages(latestBlocks).find(function (entry) { return entry.angle === angle; });
      if (!next) {
        if (match) blockDispatch.removeBlocks(match.block.clientId, false);
      } else {
        const selected = attachment || wp.data.select('core').getMedia(next.id) || {};
        const fullSource = sourceURL(selected.source_url || (selected.sizes && selected.sizes.full && selected.sizes.full.url) || selected.url);
        const attributes = {
          id: next.id, caption: richCaption(next.caption), sizeSlug: 'full',
          metadata: Object.assign({}, match ? match.block.attributes.metadata : {}, { name: 'bixie-' + angle })
        };
        if (fullSource) { attributes.url = fullSource; attributes.alt = selected.alt_text || selected.alt || ''; }
        else if (!match || positive(match.block.attributes.id) !== next.id) { attributes.url = ''; attributes.alt = ''; }
        if (match) blockDispatch.updateBlockAttributes(match.block.clientId, attributes);
        else {
          let gallery;
          walkBlocks(latestBlocks, function (block) {
            if (block.name !== 'core/gallery') return;
            if (!gallery || namedImages(block.innerBlocks).length) gallery = block;
          });
          const newBlock = wp.blocks.createBlock('core/image', attributes);
          if (gallery) blockDispatch.insertBlocks(newBlock, gallery.innerBlocks.length, gallery.clientId);
          else blockDispatch.insertBlocks(newBlock);
        }
      }
      if (next) updated.push(next);
      setMeta('bixie_images', updated);
    };
    const complete = roles.every(function (angle) {
      return images.some(function (entry) { return entry && entry.angle === angle && positive(entry.id); });
    });
    return el(Fragment, null,
      el(DocumentPanel, { name: 'bixie-look-details', title: 'Bixie look details', icon: 'id-alt' },
        fields.map(function (field) {
          return el(TextControl, {
            key: field[0], label: field[1], help: field[2], value: String(meta['bixie_' + field[0]] || ''),
            onChange: function (value) { setMeta('bixie_' + field[0], value); }
          });
        }),
        el(TextareaControl, {
          label: 'Maintenance', value: String(meta.bixie_maintenance || ''),
          onChange: function (value) { setMeta('bixie_maintenance', value); }
        }),
        el(TextareaControl, {
          label: 'Styling notes', value: String(meta.bixie_styling || ''),
          onChange: function (value) { setMeta('bixie_styling', value); }
        }),
        el(ToggleControl, {
          label: 'AI-generated hairstyle concept', checked: meta.bixie_ai_concept === true,
          help: 'Enable when this look uses AI-generated concept images. Published looks then show the concept disclosure.',
          onChange: function (value) { setMeta('bixie_ai_concept', !!value); }
        })
      ),
      el(DocumentPanel, { name: 'bixie-look-photographs', title: 'Bixie look photographs', icon: 'format-gallery' },
        el(Notice, { status: 'info', isDismissible: false },
          'Choose separate front, side, and back originals. Review every attachment in the Media Library for a complete head, loose opaque high collar, original native-source provenance, and source dimensions that meet the configured minimum. Record the composition and native-source approvals there. This editor never approves media automatically.'
        ),
        el('p', null, complete ? 'Three angle records are present. Publication still requires distinct, approved originals that pass the server’s image checks.' : 'This look is incomplete. It must remain a draft until all three distinct approved angles are present.'),
        roles.map(function (angle) {
          return el(PhotoSlot, {
            key: angle, angle: angle,
            entry: images.find(function (entry) { return entry && entry.angle === angle; }) || null,
            onChange: function (next, attachment) { setAngle(angle, next, attachment); }
          });
        })
      )
    );
  };
  if (!wp.plugins.getPlugin || !wp.plugins.getPlugin('bixie-look-settings')) {
    wp.plugins.registerPlugin('bixie-look-settings', { icon: 'format-gallery', render: LookSettings });
  }
})(window.wp);
