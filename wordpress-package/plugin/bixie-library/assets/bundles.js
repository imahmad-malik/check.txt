/* Owner-only multipart media bundle upload. Verification is server-side; import is a separate action. */
(function () {
  'use strict';
  const boot = function () {
    const root = document.getElementById('bixie-bundles');
    if (!root) return;
    const form = document.getElementById('bixie-bundle-form');
    const input = document.getElementById('bixie-bundle-files');
    const button = document.getElementById('bixie-bundle-upload');
    const status = document.getElementById('bixie-bundle-status');
    const list = document.getElementById('bixie-bundle-list');
    const config = window.BixieBundles || {};
    if (!form || !input || !button || !status || !list || !window.FormData || !window.XMLHttpRequest) return;
    let target;
    try {
      target = new URL(config.url, window.location.href);
      if (!['http:', 'https:'].includes(target.protocol) || target.origin !== window.location.origin || typeof config.nonce !== 'string' || !config.nonce) return;
    } catch (_) { return; }
    const configuredMax = Number(config.maxBytes);
    const maxBytes = Number.isFinite(configuredMax) && configuredMax > 0 ? Math.min(26214400, Math.floor(configuredMax)) : 26214400;
    const maxLabel = (maxBytes / 1048576).toLocaleString(undefined, { maximumFractionDigits: 2 }) + ' MiB';
    const originalLabel = button.textContent;
    let busy = false;
    let statusSequence = 0;
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    const displayParts = function (parts) {
      if (!Array.isArray(parts)) return;
      list.textContent = parts.length ? JSON.stringify(parts, null, 2) : 'No verified media bundle parts have been uploaded.';
    };
    const messageFrom = function (value) {
      if (typeof value === 'string') return value.slice(0, 600);
      if (value && typeof value.message === 'string') return value.message.slice(0, 600);
      if (Array.isArray(value)) return value.map(messageFrom).filter(Boolean).join(' ').slice(0, 600);
      return '';
    };
    const request = function (action, file, onProgress) {
      return new Promise(function (resolve, reject) {
        const body = new FormData();
        body.append('action', action);
        body.append('nonce', config.nonce);
        if (file) body.append('bundle', file, file.name);
        const xhr = new XMLHttpRequest();
        xhr.open('POST', target.href, true);
        xhr.timeout = 120000;
        const fail = function (message, halt) {
          const error = new Error(message);
          error.halt = !!halt;
          reject(error);
        };
        if (file && onProgress) {
          xhr.upload.addEventListener('progress', function (event) {
            if (event.lengthComputable) onProgress(Math.min(100, Math.round(event.loaded / event.total * 100)));
          });
        }
        xhr.addEventListener('load', function () {
          let response;
          try { response = JSON.parse(xhr.responseText); }
          catch (_) {
            fail(xhr.status === 413 ? 'The host rejected this file size. Check its upload limit and use a smaller ZIP part.' : 'WordPress returned an unexpected response. Refresh this page before retrying.', xhr.status === 401 || xhr.status === 403 || xhr.status === 404);
            return;
          }
          if (xhr.status === 401 || xhr.status === 403 || response === -1) {
            fail('Authorization expired or access was denied. Refresh this admin page before uploading the remaining parts.', true);
            return;
          }
          if (response === 0 || !response || typeof response !== 'object') {
            fail('The media bundle handler is unavailable. Refresh this page and confirm Bixie Library is active.', true);
            return;
          }
          if (xhr.status < 200 || xhr.status >= 300 || response.success !== true) {
            fail(messageFrom(response.data) || 'WordPress rejected this media bundle part. Check its manifest and the host upload limit.', xhr.status === 404);
            return;
          }
          resolve(response.data || {});
        });
        xhr.addEventListener('error', function () { fail('The request could not reach WordPress. Check the connection and refresh the uploaded-parts list before retrying.', false); });
        xhr.addEventListener('timeout', function () { fail('The request timed out. WordPress may have received the file; refresh the uploaded-parts list before retrying it.', false); });
        xhr.addEventListener('abort', function () { fail('The upload was interrupted. Check the uploaded-parts list before retrying.', false); });
        xhr.send(body);
      });
    };
    const refresh = async function (announce) {
      const sequence = ++statusSequence;
      try {
        const data = await request('bixie_media_bundle_status');
        if (sequence !== statusSequence) return;
        const parts = Array.isArray(data) ? data : data.parts;
        displayParts(parts);
        if (announce && !busy) status.textContent = Array.isArray(parts) && parts.length ? parts.length + ' verified part(s) stored on the server. Uploading does not import or publish content.' : 'No verified parts are stored yet.';
      } catch (error) {
        if (sequence === statusSequence && announce && !busy) status.textContent = error.message;
      }
    };
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      if (busy) return;
      const files = Array.from(input.files || []);
      if (!files.length) { status.textContent = 'Choose one or more ZIP media bundle parts first.'; input.focus(); return; }
      busy = true;
      ++statusSequence;
      form.setAttribute('aria-busy', 'true');
      button.disabled = true;
      input.disabled = true;
      button.textContent = 'Uploading parts…';
      const failures = [];
      let verified = 0;
      let halted = false;
      try {
        for (let index = 0; index < files.length; index++) {
          const file = files[index];
          const prefix = 'Part ' + (index + 1) + ' of ' + files.length + ': ' + file.name;
          if (!/\.zip$/i.test(file.name)) { failures.push(file.name + ': choose a ZIP bundle part.'); continue; }
          if (!file.size) { failures.push(file.name + ': the ZIP file is empty.'); continue; }
          if (file.size > maxBytes) { failures.push(file.name + ': exceeds the ' + maxLabel + ' per-part limit.'); continue; }
          status.textContent = prefix + ' — uploading…';
          try {
            const data = await request('bixie_media_bundle_upload', file, function (percent) {
              status.textContent = prefix + ' — ' + percent + '% uploaded' + (percent === 100 ? '; verifying on the server…' : '');
            });
            if (data.status !== 'verified') throw new Error('The server did not confirm verification. Check the uploaded-parts list before retrying.');
            ++verified;
            displayParts(data.parts);
            status.textContent = prefix + ' — verified and stored.';
          } catch (error) {
            failures.push(file.name + ': ' + error.message);
            if (error.halt) { halted = true; break; }
          }
        }
      } finally {
        busy = false;
        form.removeAttribute('aria-busy');
        button.disabled = false;
        input.disabled = false;
        button.textContent = originalLabel;
        const summary = verified + ' of ' + files.length + ' selected part(s) verified and stored.';
        status.textContent = summary + (halted ? ' Remaining uploads were stopped. ' : ' ') + (failures.length ? failures.join(' ') + ' ' : '') + 'Uploading does not import or publish content. Upload all required parts before running the separate import action.';
        await refresh(false);
        if (!failures.length) input.value = '';
      }
    });
    refresh(true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
