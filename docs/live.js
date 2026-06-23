/* ember // live build log — a pretty tail of her own coding.
 * Fetches her LOG.md (build log) and CHANGELOG.md (patch notes) raw from GitHub
 * (open CORS, no rate limit, polled every 20s) and renders them as a glowing
 * terminal feed. ALSO fetches the GitHub commits API (throttled to every 120s to
 * stay under the 60/hr unauth rate limit) to stamp each cycle with the REAL time
 * the commit landed, plus a "last activity" clock so you know exactly when things
 * ran. Newest on top; new entries since last poll glow green. */
(function () {
  'use strict';
  var RAW = 'https://raw.githubusercontent.com/mphinance/ember/master/';
  var SRC = { log: RAW + 'LOG.md', changelog: RAW + 'CHANGELOG.md' };
  var COMMITS = 'https://api.github.com/repos/mphinance/ember/commits?per_page=80';
  var feed = 'log';
  var seen = {};            // header -> true, to flag fresh entries
  var first = true;
  var cycleTimes = {};      // cycle number -> ISO commit date
  var latestTs = null;      // newest commit of any kind (the heartbeat)
  var lastCycleNum = null, lastCycleTs = null;  // newest "cycle N" commit
  var commitsAt = 0;        // last time we hit the API (throttle)
  var lastEntries = null;   // cached parse, so we can re-render when times arrive

  function ago(d) {
    var s = (Date.now() - new Date(d).getTime()) / 1000;
    if (isNaN(s)) return '';
    if (s < 90) return Math.round(s) + 's ago';
    if (s < 5400) return Math.round(s / 60) + 'm ago';
    if (s < 129600) return Math.round(s / 3600) + 'h ago';
    return Math.round(s / 86400) + 'd ago';
  }
  function clock(d) {
    try { return new Date(d).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }); }
    catch (e) { return ''; }
  }

  // Pull commit timestamps and map them to cycle numbers (throttled).
  function fetchCommits(force) {
    if (!force && Date.now() - commitsAt < 110000) return Promise.resolve();
    commitsAt = Date.now();
    return fetch(COMMITS).then(function (r) {
      if (!r.ok) throw new Error(r.status); return r.json();
    }).then(function (commits) {
      if (!Array.isArray(commits) || !commits.length) return;
      latestTs = commits[0].commit.committer.date;
      var lastRefresh = null, refreshHr = 0, hourAgo = Date.now() - 3600000;
      commits.forEach(function (c) {
        var msg = (c.commit.message || '').split('\n')[0];
        var date = c.commit.committer.date;
        var m = msg.match(/cycle\s+(\d+)/i);
        if (m) {
          if (cycleTimes[m[1]] == null) cycleTimes[m[1]] = date;
          if (lastCycleTs == null) { lastCycleNum = m[1]; lastCycleTs = date; }
        }
        if (/scan refresh/i.test(msg)) {
          if (lastRefresh == null) lastRefresh = date;
          if (new Date(date).getTime() >= hourAgo) refreshHr++;
        }
      });
      heartbeat(lastRefresh, refreshHr);
      status();
      if (lastEntries) render(lastEntries);   // re-paint now that times are known
    }).catch(function () { /* rate-limited or offline: keep last known times */ });
  }

  // Show the box's 30-min data heartbeat so the page never looks dead between
  // the (hourly) feature cycles.
  function heartbeat(lastRefresh, refreshHr) {
    var el = document.getElementById('heartbeat');
    if (!el) return;
    if (!lastRefresh) { el.innerHTML = ''; return; }
    var alive = (Date.now() - new Date(lastRefresh).getTime()) < 2700000; // < 45 min = healthy
    var dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:'
      + (alive ? '#39ff8a' : '#ff7a18') + ';box-shadow:0 0 8px ' + (alive ? '#39ff8a' : '#ff7a18')
      + ';margin-right:8px;vertical-align:middle"></span>';
    el.innerHTML = dot + (alive ? 'box alive' : 'box quiet')
      + ' &middot; data refreshed <b style="color:#c7d0d6">' + ago(lastRefresh) + '</b> (' + clock(lastRefresh) + ')'
      + ' &middot; ' + refreshHr + ' refreshes in the last hour'
      + ' &middot; <span style="color:#6b7a8d">feature cycles below run hourly when idle</span>';
  }

  function status() {
    var foot = document.getElementById('foot');
    if (!foot) return;
    var bits = [];
    if (latestTs) bits.push('last activity ' + ago(latestTs) + ' (' + clock(latestTs) + ')');
    if (lastCycleTs) bits.push('last cycle: cycle ' + lastCycleNum + ' at ' + clock(lastCycleTs));
    bits.push(feed + ' refreshed ' + clock(Date.now()));
    foot.textContent = bits.join('  ·  ');
  }

  function parse(md) {
    var out = [], cur = null;
    md.split('\n').forEach(function (ln) {
      if (/^##\s+/.test(ln)) {
        if (cur) out.push(cur);
        cur = { head: ln.replace(/^##\s+/, ''), lines: [] };
      } else if (cur && ln.trim() && !/^#\s/.test(ln) && !/^>/.test(ln)) {
        cur.lines.push(ln);
      }
    });
    if (cur) out.push(cur);
    return out;
  }

  function tagFor(s) {
    s = s.toLowerCase();
    if (/🟢|feature/.test(s)) return 'feat';
    if (/🔴|bugfix/.test(s)) return 'fix';
    if (/🟡|infra/.test(s)) return 'infra';
    if (/🧠|learned/.test(s)) return 'learn';
    return '';
  }

  function timeTag(cycleNum) {
    var ts = cycleNum && cycleTimes[cycleNum];
    if (!ts) return '';
    return '<span class="ctime" style="color:#39ff8a;font-weight:600;font-size:11px;margin-left:8px">'
      + clock(ts) + ' · ' + ago(ts) + '</span>';
  }

  function render(entries) {
    var host = document.getElementById('feed');
    host.innerHTML = '';
    entries.forEach(function (e) {
      var fresh = !first && !seen[e.head];
      seen[e.head] = true;
      var div = document.createElement('div');
      div.className = 'entry' + (fresh ? ' fresh' : '');
      var m = e.head.match(/Cycle\s+(\d+)\s*[—-]\s*([\d-]+)?\s*[—-]?\s*(.*)/i);
      var h = document.createElement('div'); h.className = 'ehead';
      if (m) {
        h.innerHTML = '<span class="num">cycle ' + m[1] + '</span>'
          + (m[2] ? '<span class="date">' + m[2] + '</span>' : '')
          + timeTag(m[1])
          + '<div style="margin-top:3px">' + esc(m[3] || '') + '</div>';
      } else {
        var t = tagFor(e.head);
        h.innerHTML = (t ? '<span class="tag ' + t + '">' + t + '</span>' : '') + esc(e.head.replace(/^[🟢🔴🔵🟡🧠]\s*/, '').replace(/^(FEATURE|BUGFIX|REFACTOR|INFRA|LEARNED)\s*[-—]\s*/i, ''));
      }
      div.appendChild(h);
      e.lines.forEach(function (ln) {
        var txt = ln.replace(/^\s*[-*]\s*/, '').trim();
        if (!txt) return;
        var p = document.createElement('div');
        var learn = /learn|made|shipped|built|found|wrote back/i.test(txt);
        p.className = 'line' + (learn ? ' learn' : (/^[A-Z]/.test(txt) ? ' k' : ''));
        p.innerHTML = esc(txt);
        div.appendChild(p);
      });
      host.appendChild(div);
    });
    first = false;
  }

  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

  function poll() {
    fetchCommits(false);   // throttled inside; refreshes the times map + clock
    fetch(SRC[feed] + '?t=' + Date.now()).then(function (r) {
      if (!r.ok) throw new Error(r.status); return r.text();
    }).then(function (md) {
      lastEntries = parse(md);
      render(lastEntries);
      status();
    }).catch(function (e) {
      var foot = document.getElementById('foot');
      if (foot) foot.textContent = 'could not reach her repo (' + e + '), retrying';
    });
  }

  document.querySelectorAll('.tab').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.tab').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on'); feed = b.dataset.feed; first = true; seen = {}; poll();
    });
  });

  fetchCommits(true);
  poll();
  setInterval(poll, 20000);
})();
