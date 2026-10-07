(() => {
  'use strict';
  const config = window.BixieDownloads;
  const start = document.getElementById('bixie-download-start');
  const pause = document.getElementById('bixie-download-pause');
  const status = document.getElementById('bixie-download-status');
  const progress = document.getElementById('bixie-download-progress');
  if (!config || !start || !pause || !status || !progress) return;
  let running = false;
  let paused = false;
  const request = async operation => {
    const body = new URLSearchParams({ action: `bixie_media_download_${operation}`, nonce: config.nonce });
    const response = await fetch(config.url, { method: 'POST', credentials: 'same-origin', body });
    let data;
    try { data = await response.json(); } catch (_) { throw new Error('The server did not return download status. Check hosting time limits and retry.'); }
    if (!response.ok || !data.success) throw new Error(data?.data?.message || 'The media download could not continue.');
    return data.data;
  };
  const render = state => {
    progress.max = Math.max(1, Number(state.total) || 1);
    progress.value = Number(state.cursor) || 0;
    status.textContent = `${state.cursor || 0} of ${state.total || 0} media parts verified${state.last_part ? `; latest ${state.last_part}` : ''}.`;
  };
  pause.addEventListener('click', () => { paused = true; pause.disabled = true; status.textContent = 'Pausing after the current media part finishes.'; });
  start.addEventListener('click', async () => {
    if (running || start.disabled) return;
    running = true; paused = false; start.disabled = true; pause.disabled = false;
    try {
      let state = await request('start'); render(state);
      while (state.status === 'running' && !paused) { state = await request('step'); render(state); }
      if (state.status === 'complete') {
        status.textContent = 'All package media parts are verified. Starting the editable content import.';
        const importer = document.getElementById('bixie-import-start');
        if (importer && !importer.disabled) importer.click();
        else status.textContent = 'All package media parts are verified. Use Start or resume import above.';
      } else status.textContent += ' Paused. Press Download media and import package to resume.';
    } catch (error) { status.textContent = `${error.message} Verified parts remain saved; retry resumes safely. Local ZIP uploads are also available.`; }
    finally { running = false; start.disabled = false; pause.disabled = true; }
  });
})();
