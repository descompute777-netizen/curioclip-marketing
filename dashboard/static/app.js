// CurioClip Mission Control — frontend interactions
(function() {

  // ─── Toast for API responses ──────────────────────────────────────────
  const toast = document.createElement('div');
  toast.id = 'toast';
  document.body.appendChild(toast);

  function showToast(msg, type = 'info') {
    toast.textContent = msg;
    toast.style.borderColor = type === 'error' ? '#ef4444' : (type === 'success' ? '#10b981' : '#fbbf24');
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  }

  // Intercept HTMX responses for feedback
  document.body.addEventListener('htmx:afterRequest', (e) => {
    if (!e.detail || !e.detail.requestConfig) return;
    const verb = e.detail.requestConfig.verb;
    const url = e.detail.requestConfig.path;
    if (verb !== 'get' && e.detail.successful) {
      let msg = '✓ OK';
      if (url.includes('calibrate')) msg = '📐 Predictor recalibrado';
      else if (url.includes('scan_patterns')) msg = '🔬 Patrones escaneados';
      else if (url.includes('produce_all')) msg = '🎬 produce_all iniciado en background';
      else if (url.includes('poll_metrics')) msg = '⟳ Metricas refrescadas';
      else if (url.includes('seed')) msg = '♻ Re-seed completado';
      else if (verb === 'delete') msg = '🗑 Eliminado';
      else if (verb === 'patch') msg = '✓ Actualizado';
      else if (verb === 'post') msg = '✓ Creado';
      showToast(msg, 'success');
    } else if (!e.detail.successful) {
      showToast('⚠ Error en la peticion', 'error');
    }
  });

  // ─── Auto-refresh overview cada 60s ───────────────────────────────────
  let autoRefreshTimer = null;
  document.body.addEventListener('htmx:afterSwap', (e) => {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    if (e.target.id === 'main') {
      const isOverview = e.detail.pathInfo && e.detail.pathInfo.path && e.detail.pathInfo.path.includes('overview');
      if (isOverview) {
        autoRefreshTimer = setInterval(() => {
          if (document.visibilityState === 'visible') {
            htmx.ajax('GET', '/partial/overview', '#main');
          }
        }, 60000);
      }
    }
  });

  // ─── jinja filter alias for fromjson (parser hack) ───────────────────
  // (no-op; left for documentation)

})();
