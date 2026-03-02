/**
 * Realtime polling for PPC dashboards.
 * Polls a JSON endpoint on an interval and updates the page or invokes a callback.
 *
 * Usage:
 *   // With callback
 *   const stop = startPolling('/api/client/dashboard/poll', 5000, (data) => {
 *     document.getElementById('total-clicks').textContent = data.summary.total_clicks;
 *   });
 *   // stop() when leaving page or pausing
 *
 *   // With custom event (for data-poll-url on a container)
 *   <div data-poll-url="/api/affiliate/dashboard/poll" data-poll-interval="5">
 *     <span data-poll-bind="total_earnings">0</span>
 *   </div>
 *   DashboardPolling.autoStart();
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

  /**
   * Start polling an endpoint. Returns a stop function.
   * @param {string} url - Full or relative URL (e.g. /api/client/dashboard/poll)
   * @param {number} intervalMs - Interval in milliseconds (default 5000)
   * @param {function(object)|null} callback - Called on each successful response with parsed JSON
   * @returns {function()} stop - Call to clear the interval
   */
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

  /**
   * Bind polled data to elements by data-poll-bind="path.to.key".
   * Container must have data-poll-url and optional data-poll-interval (seconds).
   */
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

  /**
   * Find all [data-poll-url] containers and start polling; update [data-poll-bind] children.
   */
  function autoStart() {
    var containers = document.querySelectorAll('[data-poll-url]');
    containers.forEach(function (container) {
      var url = container.getAttribute('data-poll-url');
      var intervalSec = parseInt(container.getAttribute('data-poll-interval'), 10) || 5;
      if (!url) return;
      startPolling(url, intervalSec * 1000, function (data) {
        if (data._authRequired) return;
        bindPollData(container, data);
        // Also support summary.* and earnings.* at top level
        if (data.summary) bindPollData(container, { summary: data.summary, campaigns: data.campaigns });
        if (data.earnings) bindPollData(container, { earnings: data.earnings });
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
