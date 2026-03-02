/**
 * Realtime polling for PPC dashboards.
 */
(function (global) {
  'use strict';

  var DEFAULT_INTERVAL_MS = 5000;
  var POLL_EVENT = 'dashboard-poll';

  function fetchOptions() {
    return {
      credentials: 'same-origin',
      headers: { 'Accept': 'application/json' }
    };
  }

  function startPolling(url, intervalMs, callback) {
    intervalMs = intervalMs || DEFAULT_INTERVAL_MS;
    var intervalId = null;

    function tick() {
      fetch(url, fetchOptions())
        .then(function (res) {
          if (res.status === 401) {
            if (typeof callback === 'function') callback({ _authRequired: true });
            return null;
          }
          if (!res.ok) return null;
          return res.json();
        })
        .then(function (data) {
          if (data && typeof callback === 'function' && !data._authRequired) callback(data);
          if (data && data._authRequired) return;
          if (data) {
            try {
              var event = new CustomEvent(POLL_EVENT, { detail: data });
              window.dispatchEvent(event);
            } catch (e) {}
          }
        })
        .catch(function () {});
    }

    tick();
    intervalId = setInterval(tick, intervalMs);

    return function stop() {
      if (intervalId) clearInterval(intervalId);
      intervalId = null;
    };
  }

  function bindPollData(container, data) {
    if (!container || !data) return;
    var bindings = container.querySelectorAll('[data-poll-bind]');
    bindings.forEach(function (el) {
      var path = (el.getAttribute('data-poll-bind') || '').trim();
      if (!path) return;
      var keys = path.split('.');
      var value = data;
      for (var i = 0; i < keys.length && value != null; i++) value = value[keys[i]];
      if (value != null) {
        if (el.hasAttribute('data-poll-format') && el.getAttribute('data-poll-format') === 'currency') {
          value = typeof value === 'number' ? '₹' + value.toFixed(2) : value;
        }
        el.textContent = value;
      }
    });
  }

  function autoStart() {
    var containers = document.querySelectorAll('[data-poll-url]');
    containers.forEach(function (container) {
      var url = container.getAttribute('data-poll-url');
      var intervalSec = parseInt(container.getAttribute('data-poll-interval'), 10) || 5;
      if (!url) return;
      startPolling(url, intervalSec * 1000, function (data) {
        if (data._authRequired) return;
        bindPollData(container, data);
        if (data.summary) bindPollData(container, { summary: data.summary, campaigns: data.campaigns });
        if (data.valid_clicks != null) bindPollData(container, data);
      });
    });
  }

  global.DashboardPolling = {
    startPolling: startPolling,
    autoStart: autoStart,
    POLL_EVENT: POLL_EVENT
  };
})(typeof window !== 'undefined' ? window : this);
