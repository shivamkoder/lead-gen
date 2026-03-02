/**
 * PPC Platform — API client (same-origin, session cookies).
 * Use after loading; all methods return Promises.
 */
(function (global) {
  'use strict';

  var BASE = ''; // same origin

  function opts(method, body) {
    var o = {
      method: method,
      credentials: 'same-origin',
      headers: { 'Accept': 'application/json' }
    };
    if (body !== undefined) {
      o.headers['Content-Type'] = 'application/json';
      o.body = typeof body === 'string' ? body : JSON.stringify(body);
    }
    return o;
  }

  function json(res) {
    if (res.status === 204) return Promise.resolve(null);
    return res.json().then(function (data) {
      if (!res.ok) {
        var err = new Error(data.error || data.message || 'Request failed');
        err.status = res.status;
        err.data = data;
        throw err;
      }
      return data;
    });
  }

  var api = {
    // Auth
    register: function (data) {
      return fetch(BASE + '/api/auth/register', opts('POST', data)).then(json);
    },
    login: function (email, password, remember) {
      return fetch(BASE + '/api/auth/login', opts('POST', { email: email, password: password, remember: !!remember })).then(json);
    },
    logout: function () {
      return fetch(BASE + '/api/auth/logout', opts('POST')).then(json);
    },
    me: function () {
      return fetch(BASE + '/api/auth/me', opts('GET')).then(json);
    },

    // Client
    clientRegister: function (data) {
      return fetch(BASE + '/api/client/register', opts('POST', data || {})).then(json);
    },
    clientCampaigns: function () {
      return fetch(BASE + '/api/client/campaigns', opts('GET')).then(json);
    },
    clientCreateCampaign: function (data) {
      return fetch(BASE + '/api/client/campaigns', opts('POST', data)).then(json);
    },
    clientCampaign: function (id) {
      return fetch(BASE + '/api/client/campaigns/' + id, opts('GET')).then(json);
    },
    clientUpdateCampaign: function (id, data) {
      return fetch(BASE + '/api/client/campaigns/' + id, opts('PUT', data)).then(json);
    },
    clientDashboard: function () {
      return fetch(BASE + '/api/client/dashboard', opts('GET')).then(json);
    },
    clientDashboardPoll: function () {
      return fetch(BASE + '/api/client/dashboard/poll', opts('GET')).then(json);
    },

    // Affiliate
    affiliateRegister: function (data) {
      return fetch(BASE + '/api/affiliate/register', opts('POST', data || {})).then(json);
    },
    affiliateProfile: function () {
      return fetch(BASE + '/api/affiliate/profile', opts('GET')).then(json);
    },
    affiliateCampaigns: function () {
      return fetch(BASE + '/api/affiliate/campaigns', opts('GET')).then(json);
    },
    affiliateLink: function (campaignId) {
      return fetch(BASE + '/api/affiliate/links/' + campaignId, opts('GET')).then(json);
    },
    affiliateEarnings: function () {
      return fetch(BASE + '/api/affiliate/earnings', opts('GET')).then(json);
    },
    affiliateDashboardPoll: function () {
      return fetch(BASE + '/api/affiliate/dashboard/poll', opts('GET')).then(json);
    }
  };

  global.PPC_API = api;
})(typeof window !== 'undefined' ? window : this);
