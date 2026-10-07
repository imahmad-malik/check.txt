(() => {
  'use strict';
  const config = window.BixieImport;
  const start = document.getElementById('bixie-import-start');
  const pause = document.getElementById('bixie-import-pause');
  const message = document.getElementById('bixie-import-message');
  const log = document.getElementById('bixie-import-log');
  const progress = document.getElementById('bixie-import-progress');
  if (!config || !start) return;
  let paused = false;
  const request = async (action, extra = {}) => {
    const body = new URLSearchParams({action, nonce: config.nonce, ...extra});
    const response = await fetch(config.url, {method: 'POST', credentials: 'same-origin', body});
    const json = await response.json();
    if (!response.ok || !json.success) throw new Error(json.data?.message || 'Import request failed. Existing progress is retained; use Start or resume to retry.');
    return json.data;
  };
  const show = state => {
    progress.max = Math.max(1, state.total || 1); progress.value = state.cursor || 0;
    log.textContent = JSON.stringify({status: state.status, counts: state.counts, log: state.log, diagnostics: state.diagnostics}, null, 2);
    message.textContent = state.status === 'complete' ? 'Import finished. Review diagnostics: publication gates are separate from installation progress.' : `Imported step ${state.cursor || 0} of ${state.total || 0}.`;
  };
  pause.addEventListener('click', () => { paused = true; message.textContent = 'Pausing after the active batch. Progress remains saved for resuming.'; });
  start.addEventListener('click', async () => {
    start.disabled = true; pause.disabled = false; paused = false;
    try {
      let state = await request('bixie_import_start', {overwrite: document.getElementById('bixie-overwrite').checked ? '1' : '', configure: document.getElementById('bixie-configure').checked ? '1' : ''}); show(state);
      while (!paused && state.status === 'running') { state = await request('bixie_import_batch'); show(state); }
      if (paused) message.textContent = 'Paused. Use Start or resume to continue the saved import.';
    } catch (error) { message.textContent = error.message; }
    finally { start.disabled = false; pause.disabled = true; }
  });
})();
