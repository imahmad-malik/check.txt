/* Bixie Library: public, browser-local gallery and salon shortlist tools. */
(function () {
  'use strict';

  const boot = function () {
    const config = window.BixieLibrary || {};
    const records = new Map();
    const pendingRecords = new Map();
    const savedKey = 'bixie.saved.v1';
    const notesKey = 'bixie.notes.v1';
    const savedLimit = 100;
    const filterNames = ['q', 'texture', 'length', 'fringe', 'colour', 'sort', 'collection', 'exclude'];
    const metadata = [
      ['texture', 'Texture'], ['length', 'Length'], ['fringe', 'Fringe'], ['colour', 'Colour'],
      ['density', 'Density'], ['strand', 'Strand'], ['finish', 'Finish'],
      ['age_reference', 'Age reference'], ['face_reference', 'Face reference']
    ];
    const integer = function (value) {
      const number = Number(value);
      return Number.isSafeInteger(number) && number > 0 ? number : 0;
    };
    const textValue = function (value) {
      if (Array.isArray(value)) return value.map(textValue).filter(Boolean).join(', ');
      if (value && typeof value === 'object') return String(value.name || value.label || '');
      return typeof value === 'string' || typeof value === 'number' ? String(value) : '';
    };
    const element = function (tag, className, text) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    };
    const safeURL = function (value) {
      if (typeof value !== 'string' || !value.trim()) return '';
      try {
        const url = new URL(value, window.location.href);
        return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
      } catch (_) { return ''; }
    };
    const endpoint = safeURL(config.restUrl || '/wp-json/bixie/v1/looks');
    const detailEndpoint = function (id) {
      const url = new URL(safeURL(config.lookUrl) || endpoint);
      if (url.searchParams.has('rest_route')) {
        url.searchParams.set('rest_route', url.searchParams.get('rest_route').replace(/\/$/, '') + '/' + id);
      } else {
        url.pathname = url.pathname.replace(/\/$/, '') + '/' + id;
      }
      return url;
    };
    const safeSrcset = function (value) {
      if (typeof value !== 'string') return '';
      return value.split(',').map(function (candidate) {
        const match = candidate.trim().match(/^(.+)\s+(\d+(?:\.\d+)?[wx])$/);
        return match && safeURL(match[1]) ? safeURL(match[1]) + ' ' + match[2] : '';
      }).filter(Boolean).join(', ');
    };
    const imageDescriptor = function (source, title) {
      return {
        id: integer(source.id), url: safeURL(source.url), alt: textValue(source.alt) || title,
        angle: textValue(source.angle), caption: textValue(source.caption), width: integer(source.width), height: integer(source.height),
        originalUrl: safeURL(source.originalUrl), thumbnailUrl: safeURL(source.thumbnailUrl),
        thumbnailSrcset: safeSrcset(source.thumbnailSrcset), thumbnailSizes: textValue(source.thumbnailSizes).slice(0, 1000)
      };
    };
    const normalize = function (raw) {
      if (!raw || !integer(raw.id)) return null;
      const item = Object.assign({}, raw, {
        id: integer(raw.id), title: textValue(raw.title) || 'Untitled look',
        url: safeURL(raw.url), excerpt: textValue(raw.excerpt), ai_concept: raw.ai_concept === true,
        images: []
      });
      const seen = new Set();
      const images = Array.isArray(raw.images) ? raw.images : [];
      images.forEach(function (photo) {
        if (!photo || !safeURL(photo.url) || seen.has(safeURL(photo.url))) return;
        seen.add(safeURL(photo.url));
        item.images.push(imageDescriptor(photo, item.title));
      });
      if (raw.image && safeURL(raw.image.url)) {
        const matching = item.images.find(function (image) { return image.url === safeURL(raw.image.url); });
        item.image = imageDescriptor(Object.assign({}, matching || {}, raw.image), item.title);
        if (!item.images.length) item.images.push(Object.assign({ angle: '' }, item.image));
      } else item.image = item.images[0] || null;
      metadata.forEach(function (field) { item[field[0]] = textValue(raw[field[0]]); });
      item.maintenance = textValue(raw.maintenance);
      item.styling = textValue(raw.styling);
      records.set(item.id, item);
      return item;
    };

    let persistentStorage = true;
    let saved = new Set();
    let notes = Object.create(null);
    const parseStored = function (value, fallback) {
      try { return JSON.parse(value); } catch (_) { return fallback; }
    };
    try {
      const rawSaved = parseStored(window.localStorage.getItem(savedKey) || '[]', []);
      if (Array.isArray(rawSaved)) saved = new Set(rawSaved.map(integer).filter(Boolean).slice(0, savedLimit));
      const rawNotes = parseStored(window.localStorage.getItem(notesKey) || '{}', {});
      if (rawNotes && typeof rawNotes === 'object' && !Array.isArray(rawNotes)) {
        Object.keys(rawNotes).forEach(function (id) {
          if (integer(id) && typeof rawNotes[id] === 'string') notes[id] = rawNotes[id].slice(0, 3000);
        });
      }
    } catch (_) { persistentStorage = false; }
    let notice;
    const announce = function (message) {
      if (dialog && dialog.open) {
        dialog.querySelector('.bixie-modal-notice').textContent = message;
        return;
      }
      if (!notice) {
        notice = element('p', 'bixie-library-notice');
        notice.setAttribute('role', 'status');
        notice.setAttribute('aria-live', 'polite');
        document.body.append(notice);
      }
      notice.textContent = message;
    };
    const persist = function () {
      try {
        window.localStorage.setItem(savedKey, JSON.stringify(Array.from(saved)));
        window.localStorage.setItem(notesKey, JSON.stringify(notes));
      } catch (_) {
        const firstFailure = persistentStorage;
        persistentStorage = false;
        if (firstFailure) announce('Browser storage is unavailable. Your saved looks and notes will last for this page visit only.');
      }
    };
    const updateSaved = function () {
      document.querySelectorAll('.bixie-saved-count').forEach(function (node) { node.textContent = String(saved.size); });
      document.querySelectorAll('.bixie-save[data-look]').forEach(function (button) {
        const id = integer(button.dataset.look);
        const isSaved = saved.has(id);
        const title = records.has(id) ? records.get(id).title : 'this look';
        button.setAttribute('aria-pressed', String(isSaved));
        button.setAttribute('aria-label', (isSaved ? 'Remove ' : 'Save ') + title + (isSaved ? ' from saved looks' : ''));
        const label = button.querySelector('[data-save-label]');
        if (label) label.textContent = isSaved ? 'Saved' : 'Save look';
        else button.textContent = isSaved ? 'Saved' : 'Save look';
      });
    };
    const saveButton = function (item) {
      const button = element('button', 'bixie-save', 'Save look');
      button.type = 'button';
      button.dataset.look = String(item.id);
      return button;
    };
    const toggleSaved = function (id, removeOnly) {
      if (!id) return;
      if (saved.has(id)) { saved.delete(id); chosen.delete(id); }
      else if (!removeOnly) {
        if (saved.size >= savedLimit) {
          announce('You can save up to ' + savedLimit + ' looks. Remove a look before adding another.');
          return;
        }
        saved.add(id);
      }
      persist();
      updateSaved();
      refreshSavedPages();
      announce(saved.has(id) ? (persistentStorage ? 'Look saved to your browser shortlist.' : 'Look saved for this page visit only. Browser storage is unavailable.') : 'Look removed from your shortlist.');
    };
    const getRecord = async function (id) {
      if (pendingRecords.has(id)) return pendingRecords.get(id);
      const request = (async function () {
        const response = await fetch(detailEndpoint(id), { credentials: 'same-origin', headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error(response.status === 404 ? 'This look is no longer available.' : 'This look could not be loaded.');
        const item = normalize(await response.json());
        if (!item || item.id !== id) throw new Error('This look could not be loaded.');
        return item;
      })();
      pendingRecords.set(id, request);
      try { return await request; } finally { pendingRecords.delete(id); }
    };
    const getSavedRecords = async function () {
      const ids = Array.from(saved);
      const result = new Array(ids.length);
      let next = 0;
      const worker = async function () {
        while (next < ids.length) {
          const index = next++;
          try { result[index] = { id: ids[index], item: await getRecord(ids[index]) }; }
          catch (error) { result[index] = { id: ids[index], error: error.message }; }
        }
      };
      await Promise.all(Array.from({ length: Math.min(6, ids.length) }, worker));
      return result;
    };
    const photo = function (item, descriptor, eager, thumbnail) {
      const image = element('img', 'bixie-look-image');
      image.src = thumbnail && descriptor.thumbnailUrl ? descriptor.thumbnailUrl : descriptor.url;
      if (thumbnail && descriptor.thumbnailSrcset) {
        image.srcset = descriptor.thumbnailSrcset;
        image.sizes = descriptor.thumbnailSizes || '(max-width: 600px) 100vw, 25vw';
      }
      image.alt = descriptor.alt || item.title;
      image.loading = eager ? 'eager' : 'lazy';
      image.decoding = 'async';
      if (descriptor.width) image.width = descriptor.width;
      if (descriptor.height) image.height = descriptor.height;
      image.addEventListener('error', function () {
        image.classList.add('bixie-image-unavailable');
        const warning = element('span', 'bixie-image-status', 'Image unavailable');
        image.after(warning);
      }, { once: true });
      return image;
    };
    const realLink = function (item, className, label) {
      if (!item.url) return element('span', className, label);
      const link = element('a', className, label);
      link.href = item.url;
      return link;
    };
    const metadataList = function (item) {
      const list = element('dl', 'bixie-look-metadata');
      metadata.forEach(function (field) {
        if (!item[field[0]]) return;
        const row = element('div', 'bixie-metadata-row');
        row.append(element('dt', '', field[1]), element('dd', '', item[field[0]]));
        list.append(row);
      });
      return list;
    };
    const conceptNote = function (item) {
      return item.ai_concept ? element('p', 'bixie-concept-note', 'AI-generated hairstyle concept. Discuss suitability and achievable results with a qualified stylist.') : null;
    };
    const photoCaption = function (descriptor) {
      if (descriptor.caption && descriptor.caption.toLowerCase() === descriptor.angle.toLowerCase()) return descriptor.caption;
      return [descriptor.angle, descriptor.caption].filter(Boolean).join(' · ');
    };
    const card = function (item, withSelection, showViews) {
      const article = element('article', 'bixie-look-card');
      article.dataset.look = String(item.id);
      const front = showViews ? (item.images.find(function (image) { return image.angle.toLowerCase() === 'front'; }) || item.image) : item.image;
      if (front) {
        const link = realLink(item, 'bixie-card-photo');
        link.append(photo(item, front, false, true));
        article.append(link);
      }
      if (showViews) {
        const views = element('div', 'bixie-card-angles');
        const seen = new Set(front ? [front.id ? 'id:' + front.id : front.url] : []);
        ['side', 'back'].forEach(function (angle) {
          const descriptor = item.images.find(function (image) {
            const key = image.id ? 'id:' + image.id : image.url;
            return image.angle.toLowerCase() === angle && !seen.has(key) && (!front || image.url !== front.url);
          });
          if (!descriptor) return;
          seen.add(descriptor.id ? 'id:' + descriptor.id : descriptor.url);
          const figure = element('figure', 'bixie-card-angle');
          const link = realLink(item, 'bixie-detail-trigger');
          link.dataset.look = String(item.id);
          link.dataset.angle = angle;
          link.setAttribute('aria-label', 'View ' + angle + ' photograph of ' + item.title);
          const image = photo(item, descriptor, false, true);
          image.sizes = '(max-width: 600px) 42vw, 14vw';
          link.append(image);
          figure.append(link, element('figcaption', '', angle === 'side' ? 'Side' : 'Back'));
          views.append(figure);
        });
        if (views.childElementCount) article.append(views);
      }
      const content = element('div', 'bixie-card-content');
      const heading = element('h3', 'bixie-card-title');
      heading.append(realLink(item, '', item.title));
      content.append(heading);
      const summary = [item.texture, item.length, item.fringe].filter(Boolean).join(' · ');
      if (summary) content.append(element('p', 'bixie-card-summary', summary));
      const concept = conceptNote(item);
      if (concept) content.append(concept);
      const actions = element('div', 'bixie-card-actions');
      const detail = element('button', 'bixie-detail-trigger', 'View look');
      detail.type = 'button';
      detail.dataset.look = String(item.id);
      detail.setAttribute('aria-label', 'View ' + item.title);
      actions.append(detail, saveButton(item));
      content.append(actions);
      if (withSelection) {
        const label = element('label', 'bixie-compare-choice');
        const input = element('input');
        input.type = 'checkbox';
        input.dataset.bixieCompare = String(item.id);
        input.checked = chosen.has(item.id);
        label.append(input, element('span', '', 'Compare ' + item.title));
        content.append(label);
      }
      article.append(content);
      return article;
    };

    const savedPages = Array.from(document.querySelectorAll('.bixie-saved-page')).map(function (root) {
      return { root: root, items: root.querySelector('.bixie-saved-items'), status: root.querySelector('.bixie-saved-page-status'), sequence: 0 };
    });
    const refreshSavedPages = function () {
      savedPages.forEach(async function (state) {
        if (!state.items || !state.status) return;
        const sequence = ++state.sequence;
        state.status.setAttribute('role', 'status');
        state.status.setAttribute('aria-live', 'polite');
        if (!saved.size) {
          state.items.replaceChildren(element('p', 'bixie-empty', 'Your shortlist is empty. Save a look from the gallery or its detail page.'));
          state.status.textContent = 'No saved looks on this browser.';
          state.root.removeAttribute('aria-busy');
          return;
        }
        state.root.setAttribute('aria-busy', 'true');
        state.status.textContent = 'Loading your current saved looks…';
        const entries = await getSavedRecords();
        if (state.sequence !== sequence) return;
        const fragment = document.createDocumentFragment();
        entries.forEach(function (entry) {
          if (entry.item) fragment.append(card(entry.item, false));
          else {
            const unavailable = element('article', 'bixie-unavailable-look');
            unavailable.append(element('h3', '', 'Saved look #' + entry.id), element('p', '', entry.error));
            const remove = element('button', 'bixie-remove-saved', 'Remove unavailable look');
            remove.type = 'button';
            remove.dataset.look = String(entry.id);
            unavailable.append(remove);
            fragment.append(unavailable);
          }
        });
        state.items.replaceChildren(fragment);
        state.status.textContent = saved.size + (saved.size === 1 ? ' saved look.' : ' saved looks.') + (persistentStorage ? ' Stored on this browser only.' : ' Storage is unavailable; this shortlist lasts for this page visit only.');
        state.root.removeAttribute('aria-busy');
        updateSaved();
      });
    };

    document.querySelectorAll('.bixie-library').forEach(function (root) {
      const form = root.querySelector('.bixie-filter-form');
      const results = root.querySelector('.bixie-results');
      const status = root.querySelector('.bixie-result-status');
      const paging = root.querySelector('.bixie-pagination');
      const showViews = root.dataset.showAngles === 'true';
      if (!form || !results || !status) return;
      const initial = root.querySelector('.bixie-initial-data');
      if (initial) {
        try {
          const data = JSON.parse(initial.textContent);
          if (Array.isArray(data.items)) data.items.forEach(normalize);
        } catch (_) { /* Keep the server-rendered gallery if initial JSON is unavailable. */ }
      }
      status.setAttribute('role', 'status');
      status.setAttribute('aria-live', 'polite');
      let controller;
      let sequence = 0;
      let debounce;
      const parameters = function (page) {
        const params = new URLSearchParams();
        const values = new FormData(form);
        filterNames.forEach(function (name) {
          const value = textValue(values.get(name)).trim();
          if (value) params.set(name, value);
        });
        if (!params.has('collection') && root.dataset.collection) params.set('collection', root.dataset.collection);
        if (!params.has('exclude') && root.dataset.exclude) params.set('exclude', root.dataset.exclude);
        params.set('page', String(page));
        params.set('per_page', String(Math.min(48, integer(root.dataset.size) || 12)));
        return params;
      };
      const fallbackURL = function (page) {
        const url = new URL(safeURL(form.getAttribute('action')) || window.location.href);
        filterNames.concat(['bixie_page', 'per_page']).forEach(function (name) { url.searchParams.delete(name); });
        parameters(page).forEach(function (value, name) { url.searchParams.set(name === 'page' ? 'bixie_page' : name, value); });
        url.hash = root.id || '';
        return url.href;
      };
      const pageLink = function (number, label, current) {
        if (current) {
          const span = element('span', 'bixie-page-current', label);
          span.setAttribute('aria-current', 'page');
          return span;
        }
        const link = element('a', 'bixie-page-link', label);
        link.href = fallbackURL(number);
        link.dataset.bixiePage = String(number);
        if (/^\d+$/.test(label)) link.setAttribute('aria-label', 'Page ' + number);
        return link;
      };
      const renderPaging = function (page, pages) {
        if (!paging) return;
        paging.replaceChildren();
        if (pages < 2) return;
        if (page > 1) paging.append(pageLink(page - 1, 'Previous'));
        const numbers = new Set([1, pages]);
        for (let number = Math.max(1, page - 2); number <= Math.min(pages, page + 2); number++) numbers.add(number);
        let previous = 0;
        Array.from(numbers).sort(function (a, b) { return a - b; }).forEach(function (number) {
          if (previous && number - previous > 1) paging.append(element('span', 'bixie-page-gap', '…'));
          paging.append(pageLink(number, String(number), number === page));
          previous = number;
        });
        if (page < pages) paging.append(pageLink(page + 1, 'Next'));
      };
      const requestPage = async function (page, fromPagination) {
        window.clearTimeout(debounce);
        if (controller) controller.abort();
        controller = new AbortController();
        const request = ++sequence;
        root.setAttribute('aria-busy', 'true');
        status.textContent = 'Loading looks…';
        root.querySelectorAll('.bixie-request-fallback').forEach(function (node) { node.remove(); });
        try {
          const url = new URL(endpoint);
          parameters(page).forEach(function (value, name) { url.searchParams.set(name, value); });
          const response = await fetch(url, { signal: controller.signal, credentials: 'same-origin', headers: { Accept: 'application/json' } });
          if (!response.ok) throw new Error('Gallery request failed.');
          const data = await response.json();
          if (!Array.isArray(data.items) || !Number.isFinite(Number(data.total)) || !Number.isFinite(Number(data.pages))) throw new Error('Gallery response unavailable.');
          if (request !== sequence) return;
          const items = data.items.map(normalize).filter(Boolean);
          const total = Math.max(0, Number(data.total));
          const pages = Math.max(0, Math.floor(Number(data.pages)));
          const current = integer(data.page) || page;
          const fragment = document.createDocumentFragment();
          items.forEach(function (item) { fragment.append(card(item, false, showViews)); });
          if (!items.length) fragment.append(element('p', 'bixie-empty', total ? 'No looks on this page. Choose another page below.' : 'No looks match these filters. Try a different texture, fringe, length, or search.'));
          results.replaceChildren(fragment);
          status.textContent = total + (total === 1 ? ' look' : ' looks') + (pages > 1 ? ' · Page ' + current + ' of ' + pages : '');
          root.dataset.page = String(current);
          renderPaging(current, pages);
          updateSaved();
          if (fromPagination) {
            status.tabIndex = -1;
            status.focus({ preventScroll: true });
            if (root.getBoundingClientRect().top < 0) root.scrollIntoView({ behavior: 'auto', block: 'start' });
          }
        } catch (error) {
          if (error.name === 'AbortError' || request !== sequence) return;
          status.textContent = 'Live filters are unavailable. The existing gallery remains available.';
          const link = element('a', 'bixie-request-fallback', 'Open these results as a full page');
          link.href = fallbackURL(page);
          status.after(link);
        } finally {
          if (request === sequence) root.removeAttribute('aria-busy');
        }
      };
      form.addEventListener('submit', function (event) { event.preventDefault(); requestPage(1, false); });
      form.addEventListener('change', function (event) {
        if (filterNames.includes(event.target.name)) requestPage(1, false);
      });
      form.addEventListener('input', function (event) {
        if (event.target.name !== 'q') return;
        window.clearTimeout(debounce);
        debounce = window.setTimeout(function () { requestPage(1, false); }, 300);
      });
      form.addEventListener('reset', function () { window.setTimeout(function () { requestPage(1, false); }, 0); });
      root.addEventListener('click', function (event) {
        const link = event.target.closest('[data-bixie-page], .bixie-pagination a[data-page]');
        if (!link || !root.contains(link) || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        requestPage(integer(link.dataset.bixiePage || link.dataset.page) || 1, true);
      });
    });

    let dialog;
    let dialogTitle;
    let dialogBody;
    let dialogFooter;
    let origin;
    let modalSequence = 0;
    let view = '';
    const chosen = new Set();
    const ensureDialog = function () {
      if (dialog) return;
      dialog = element('dialog', 'bixie-library-modal');
      dialog.setAttribute('aria-labelledby', 'bixie-library-dialog-title');
      const header = element('header', 'bixie-modal-header');
      dialogTitle = element('h2', 'bixie-modal-title');
      dialogTitle.id = 'bixie-library-dialog-title';
      const close = element('button', 'bixie-modal-close', 'Close');
      close.type = 'button';
      close.setAttribute('aria-label', 'Close look tools');
      close.addEventListener('click', function () { dialog.close(); });
      header.append(dialogTitle, close);
      dialogBody = element('div', 'bixie-modal-body');
      dialogFooter = element('footer', 'bixie-modal-footer');
      const liveNotice = element('p', 'bixie-modal-notice');
      liveNotice.setAttribute('role', 'status');
      liveNotice.setAttribute('aria-live', 'polite');
      dialog.append(header, dialogBody, liveNotice, dialogFooter);
      document.body.append(dialog);
      dialog.addEventListener('close', function () {
        ++modalSequence;
        document.documentElement.classList.remove('bixie-printing');
        document.body.classList.remove('bixie-modal-open');
        if (origin && origin.isConnected && typeof origin.focus === 'function') origin.focus({ preventScroll: true });
        view = '';
      });
      dialog.addEventListener('click', function (event) {
        if (event.target !== dialog) return;
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
      });
    };
    const openDialog = function (title, newView, trigger) {
      ensureDialog();
      if (!dialog.open) origin = trigger || document.activeElement;
      view = newView;
      dialogTitle.textContent = title;
      dialogBody.replaceChildren();
      dialogFooter.replaceChildren();
      dialog.querySelector('.bixie-modal-notice').textContent = '';
      document.documentElement.classList.remove('bixie-printing');
      const sequence = ++modalSequence;
      if (!dialog.open) {
        if (typeof dialog.showModal !== 'function') {
          announce('This browser cannot open look dialogs. Follow the look links to view full details.');
          return 0;
        }
        dialog.showModal();
        document.body.classList.add('bixie-modal-open');
      }
      dialog.scrollTop = 0;
      dialogBody.scrollTop = 0;
      dialog.querySelector('.bixie-modal-close').focus({ preventScroll: true });
      return sequence;
    };
    const modalStatus = function (message) {
      const node = element('p', 'bixie-modal-status', message);
      node.setAttribute('role', 'status');
      dialogBody.append(node);
      return node;
    };
    const toolbarButton = function (label, className) {
      const button = element('button', className, label);
      button.type = 'button';
      return button;
    };
    const showLook = async function (id, trigger, preferredAngle) {
      if (!id) return;
      const sequence = openDialog('Look details', 'detail', trigger);
      if (!sequence) return;
      modalStatus('Loading this look…');
      try {
        const item = await getRecord(id);
        if (sequence !== modalSequence || !dialog.open) return;
        dialogTitle.textContent = item.title;
        dialogBody.replaceChildren();
        const gallery = element('div', 'bixie-detail-photos');
        const requestedAngle = textValue(preferredAngle).toLowerCase();
        const requested = item.images.find(function (image) { return image.angle.toLowerCase() === requestedAngle; });
        const images = requested ? [requested].concat(item.images.filter(function (image) { return image !== requested; })) : item.images;
        let initialFigure;
        images.forEach(function (descriptor) {
          const figure = element('figure', 'bixie-detail-photo');
          figure.dataset.angle = descriptor.angle.toLowerCase();
          figure.append(photo(item, descriptor, true));
          if (descriptor.angle || descriptor.caption) figure.append(element('figcaption', '', photoCaption(descriptor)));
          if (descriptor.originalUrl) {
            const original = element('a', 'bixie-original-image', 'Open original native image');
            original.href = descriptor.originalUrl;
            original.target = '_blank';
            original.rel = 'noopener';
            figure.append(original);
          }
          if (descriptor === requested) {
            figure.tabIndex = -1;
            figure.setAttribute('aria-label', descriptor.angle + ' photograph of ' + item.title);
            initialFigure = figure;
          }
          gallery.append(figure);
        });
        if (item.images.length) dialogBody.append(gallery);
        else dialogBody.append(element('p', 'bixie-empty', 'Photography has not been published for this look.'));
        if (item.excerpt) dialogBody.append(element('p', 'bixie-look-description', item.excerpt));
        dialogBody.append(metadataList(item));
        [['maintenance', 'Maintenance'], ['styling', 'Styling notes']].forEach(function (field) {
          if (!item[field[0]]) return;
          const section = element('section', 'bixie-look-advice');
          section.append(element('h3', '', field[1]), element('p', '', item[field[0]]));
          dialogBody.append(section);
        });
        const concept = conceptNote(item);
        if (concept) dialogBody.append(concept);
        dialogFooter.append(saveButton(item), realLink(item, 'bixie-look-permalink', 'Open full look page'));
        updateSaved();
        if (initialFigure) initialFigure.focus({ preventScroll: true });
      } catch (error) {
        if (sequence !== modalSequence || !dialog.open) return;
        dialogBody.replaceChildren();
        modalStatus(error.message + ' Please try again, or open the full look page.');
        const cached = records.get(id);
        if (cached && cached.url) dialogBody.append(realLink(cached, 'bixie-look-permalink', 'Open full look page'));
      }
    };
    const updateCompareAction = function () {
      if (!dialog) return;
      const button = dialog.querySelector('.bixie-compare-selected');
      if (button) {
        button.disabled = chosen.size < 2 || chosen.size > 3;
        button.textContent = 'Compare selected looks (' + chosen.size + ')';
      }
      const message = dialog.querySelector('.bixie-compare-status');
      if (message) message.textContent = 'Select two or three available looks to compare. ' + chosen.size + ' selected.';
    };
    const showSaved = async function (trigger, compareMode) {
      const sequence = openDialog(compareMode ? 'Choose looks to compare' : 'Your saved looks', 'saved', trigger);
      if (!sequence) return;
      const intro = element('p', 'bixie-storage-note', persistentStorage ? 'Saved on this browser. Your shortlist is not uploaded or shared.' : 'Browser storage is unavailable. This shortlist lasts for this page visit only.');
      dialogBody.append(intro);
      if (!saved.size) {
        modalStatus('Your shortlist is empty. Save a look from the gallery or its detail page.');
        return;
      }
      const loading = modalStatus('Loading your current saved looks…');
      const list = await getSavedRecords();
      if (sequence !== modalSequence || !dialog.open) return;
      loading.remove();
      const valid = new Set(list.filter(function (entry) { return entry.item; }).map(function (entry) { return entry.id; }));
      Array.from(chosen).forEach(function (id) { if (!valid.has(id)) chosen.delete(id); });
      if (compareMode && chosen.size < 2) {
        Array.from(valid).slice(0, 2).forEach(function (id) { chosen.add(id); });
      }
      const compareStatus = element('p', 'bixie-compare-status');
      compareStatus.setAttribute('role', 'status');
      dialogBody.append(compareStatus);
      const grid = element('div', 'bixie-saved-grid');
      list.forEach(function (entry) {
        if (entry.item) grid.append(card(entry.item, true));
        else {
          const unavailable = element('article', 'bixie-unavailable-look');
          unavailable.append(element('h3', '', 'Saved look #' + entry.id), element('p', '', entry.error));
          const remove = toolbarButton('Remove unavailable look', 'bixie-remove-saved');
          remove.dataset.look = String(entry.id);
          unavailable.append(remove);
          grid.append(unavailable);
        }
      });
      dialogBody.append(grid);
      dialogFooter.append(toolbarButton('Compare selected looks', 'bixie-compare-selected'), toolbarButton('Create salon sheets', 'bixie-print-saved'));
      updateSaved();
      updateCompareAction();
    };
    const showCompare = async function (trigger) {
      if (chosen.size < 2 || chosen.size > 3) { showSaved(trigger, true); return; }
      const ids = Array.from(chosen);
      const sequence = openDialog('Compare your chosen looks', 'compare', trigger);
      if (!sequence) return;
      modalStatus('Loading current look details…');
      const result = await Promise.all(ids.map(async function (id) {
        try { return { item: await getRecord(id) }; } catch (error) { return { error: error.message }; }
      }));
      if (sequence !== modalSequence || !dialog.open) return;
      dialogBody.replaceChildren();
      if (result.some(function (entry) { return entry.error; })) {
        modalStatus('Some selected looks are unavailable. Return to your shortlist and choose available looks.');
        dialogFooter.append(toolbarButton('Choose other looks', 'bixie-open-compare'));
        return;
      }
      dialogBody.append(element('p', 'bixie-compare-instruction', 'Scroll horizontally to compare. You can also focus the comparison and use the arrow keys.'));
      const region = element('div', 'bixie-compare-region');
      region.tabIndex = 0;
      region.setAttribute('role', 'region');
      region.setAttribute('aria-label', 'Comparison of ' + ids.length + ' saved hairstyles');
      const grid = element('div', 'bixie-compare-grid');
      grid.style.setProperty('--bixie-compare-columns', String(ids.length));
      result.forEach(function (entry) {
        const item = entry.item;
        const article = element('article', 'bixie-compare-look');
        article.append(element('h3', '', item.title));
        if (item.image) article.append(photo(item, item.image, true));
        article.append(metadataList(item));
        if (item.maintenance) article.append(element('h4', '', 'Maintenance'), element('p', '', item.maintenance));
        if (item.styling) article.append(element('h4', '', 'Styling notes'), element('p', '', item.styling));
        const concept = conceptNote(item);
        if (concept) article.append(concept);
        article.append(realLink(item, 'bixie-look-permalink', 'Open full look page'));
        grid.append(article);
      });
      region.append(grid);
      dialogBody.append(region);
      dialogFooter.append(toolbarButton('Choose other looks', 'bixie-open-compare'), toolbarButton('Create salon sheets', 'bixie-print-saved'));
    };
    const printSheet = function (item) {
      const sheet = element('article', 'bixie-print-sheet');
      sheet.append(element('h3', '', item.title), element('p', 'bixie-sheet-id', 'Bixie Library look #' + item.id));
      const images = element('div', 'bixie-sheet-images');
      item.images.forEach(function (descriptor) {
        const figure = element('figure');
        figure.append(photo(item, descriptor, true));
        if (descriptor.angle || descriptor.caption) figure.append(element('figcaption', '', photoCaption(descriptor)));
        images.append(figure);
      });
      if (item.images.length) sheet.append(images);
      sheet.append(metadataList(item));
      if (item.maintenance) sheet.append(element('p', '', 'Maintenance: ' + item.maintenance));
      if (item.styling) sheet.append(element('p', '', 'Styling: ' + item.styling));
      const concept = conceptNote(item);
      if (concept) sheet.append(concept);
      if (item.url) sheet.append(realLink(item, 'bixie-sheet-source', 'Source: ' + item.url));
      const label = element('label', 'bixie-salon-notes-label', 'Notes for your stylist');
      const input = element('textarea', 'bixie-salon-notes');
      input.rows = 3;
      input.maxLength = 3000;
      input.dataset.look = String(item.id);
      input.id = 'bixie-salon-notes-' + item.id;
      input.value = notes[item.id] || '';
      label.htmlFor = input.id;
      const printed = element('p', 'bixie-note-print', input.value || 'Notes: ______________________________');
      sheet.append(label, input, printed);
      return sheet;
    };
    const showPrint = async function (trigger) {
      const sequence = openDialog('Your salon consultation sheets', 'print', trigger);
      if (!sequence) return;
      if (!saved.size) { modalStatus('Save at least one look before creating a salon sheet.'); return; }
      modalStatus('Preparing current saved looks…');
      const list = await getSavedRecords();
      if (sequence !== modalSequence || !dialog.open) return;
      dialogBody.replaceChildren();
      dialogBody.append(element('p', 'bixie-sheet-intro', 'Bring these references to a stylist. Discuss your hair texture, density, routine, and the adjustments needed for an achievable cut.'));
      let count = 0;
      list.forEach(function (entry) {
        if (entry.item) { dialogBody.append(printSheet(entry.item)); ++count; }
        else dialogBody.append(element('p', 'bixie-print-warning', 'Look #' + entry.id + ' was omitted: ' + entry.error));
      });
      if (count) dialogFooter.append(toolbarButton('Print salon sheets', 'bixie-print-now'));
      dialogFooter.append(toolbarButton('Return to saved looks', 'bixie-open-saved'));
    };

    document.addEventListener('click', async function (event) {
      const button = event.target.closest('.bixie-save, .bixie-detail-trigger, .bixie-open-saved, .bixie-open-compare, .bixie-print-saved, .bixie-compare-selected, .bixie-remove-saved, .bixie-print-now');
      if (!button || button.disabled || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      if (button.matches('.bixie-save, .bixie-remove-saved')) {
        const id = integer(button.dataset.look);
        if (!id) return;
        if (button.matches('.bixie-save') && !saved.has(id) && !records.has(id)) {
          button.disabled = true;
          try { await getRecord(id); }
          catch (error) { announce(error.message + ' Please try saving it again later.'); return; }
          finally { if (button.isConnected) button.disabled = false; }
        }
        toggleSaved(id, button.matches('.bixie-remove-saved'));
        if (dialog && dialog.open && view === 'saved') showSaved(origin, false);
      } else if (button.matches('.bixie-detail-trigger')) showLook(integer(button.dataset.look), button, button.dataset.angle);
      else if (button.matches('.bixie-open-saved')) showSaved(button, false);
      else if (button.matches('.bixie-open-compare')) showSaved(button, true);
      else if (button.matches('.bixie-print-saved')) showPrint(button);
      else if (button.matches('.bixie-compare-selected')) showCompare(button);
      else if (button.matches('.bixie-print-now')) {
        button.disabled = true;
        const currentSequence = modalSequence;
        Promise.race([
          Promise.all(Array.from(dialog.querySelectorAll('img')).map(function (image) { return typeof image.decode === 'function' ? image.decode().catch(function () {}) : Promise.resolve(); })),
          new Promise(function (resolve) { window.setTimeout(resolve, 5000); })
        ]).then(function () {
          button.disabled = false;
          if (!dialog.open || currentSequence !== modalSequence) return;
          document.documentElement.classList.add('bixie-printing');
          try { window.print(); } catch (_) { announce('Printing is unavailable in this browser. You can use its print command while the salon sheets are open.'); }
        });
      }
    });
    document.addEventListener('change', function (event) {
      const input = event.target.closest('[data-bixie-compare]');
      if (!input) return;
      const id = integer(input.dataset.bixieCompare);
      if (input.checked && chosen.size >= 3 && !chosen.has(id)) {
        input.checked = false;
        announce('Compare up to three looks. Deselect one before adding another.');
      } else if (input.checked) chosen.add(id);
      else chosen.delete(id);
      updateCompareAction();
    });
    document.addEventListener('input', function (event) {
      const input = event.target.closest('textarea.bixie-salon-notes');
      if (!input) return;
      notes[integer(input.dataset.look)] = input.value.slice(0, 3000);
      const printed = input.parentElement.querySelector('.bixie-note-print');
      if (printed) printed.textContent = input.value || 'Notes: ______________________________';
      persist();
    });
    window.addEventListener('beforeprint', function () {
      if (dialog && dialog.open && view === 'print') document.documentElement.classList.add('bixie-printing');
    });
    window.addEventListener('afterprint', function () { document.documentElement.classList.remove('bixie-printing'); });
    window.addEventListener('storage', function (event) {
      if (event.key !== savedKey) return;
      try {
        const updated = JSON.parse(event.newValue || '[]');
        if (!Array.isArray(updated)) return;
        saved = new Set(updated.map(integer).filter(Boolean).slice(0, savedLimit));
        Array.from(chosen).forEach(function (id) { if (!saved.has(id)) chosen.delete(id); });
        updateSaved();
        refreshSavedPages();
        if (dialog && dialog.open && view === 'saved') showSaved(origin, false);
      } catch (_) { /* Ignore invalid data from another tab. */ }
    });
    updateSaved();
    refreshSavedPages();
    const unknownIds = Array.from(new Set(Array.from(document.querySelectorAll('.bixie-save[data-look]')).map(function (button) {
      return integer(button.dataset.look);
    }).filter(function (id) { return id && !records.has(id); })));
    let hydrateIndex = 0;
    const hydrateWorker = async function () {
      while (hydrateIndex < unknownIds.length) {
        const id = unknownIds[hydrateIndex++];
        try { await getRecord(id); updateSaved(); } catch (_) { /* Keep the real detail links and retry if the visitor saves. */ }
      }
    };
    Promise.all(Array.from({ length: Math.min(6, unknownIds.length) }, hydrateWorker));
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
