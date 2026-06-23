/* ember // live build log — a pretty tail of her own coding.
 * Fetches her LOG.md (build log) and CHANGELOG.md (patch notes) raw from GitHub
 * (open CORS, no rate limit) and renders them as a glowing terminal feed that
 * polls for new cycles. Newest on top; new entries since last poll glow green. */
(function () {
  'use strict';
  var RAW = 'https://raw.githubusercontent.com/mphinance/ember/master/';
  var SRC = { log: RAW + 'LOG.md', changelog: RAW + 'CHANGELOG.md' };
  var feed = 'log';
  var seen = {};        // header -> true, to flag fresh entries
  var first = true;

  function ago(d) {
    var s = (Date.now() - new Date(d).getTime()) / 1000;
    if (isNaN(s)) return '';
    if (s < 90) return Math.round(s) + 's ago';
    if (s < 5400) return Math.round(s / 60) + 'm ago';
    if (s < 129600) return Math.round(s / 3600) + 'h ago';
    return Math.round(s / 86400) + 'd ago';
  }

  // Split a markdown doc into entries on "## " headers; keep header + body lines.
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

  function render(entries) {
    var host = document.getElementById('feed');
    host.innerHTML = '';
    entries.forEach(function (e) {
      var fresh = !first && !seen[e.head];
      seen[e.head] = true;
      var div = document.createElement('div');
      div.className = 'entry' + (fresh ? ' fresh' : '');
      // header: pull "Cycle N" + date out if present
      var m = e.head.match(/Cycle\s+(\d+)\s*[—-]\s*([\d-]+)?\s*[—-]?\s*(.*)/i);
      var h = document.createElement('div'); h.className = 'ehead';
      if (m) {
        h.innerHTML = '<span class="num">cycle ' + m[1] + '</span>'
          + (m[2] ? '<span class="date">' + m[2] + '</span>' : '')
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
    fetch(SRC[feed] + '?t=' + Date.now()).then(function (r) {
      if (!r.ok) throw new Error(r.status); return r.text();
    }).then(function (md) {
      render(parse(md));
      document.getElementById('foot').textContent =
        'live · ' + feed + ' · refreshed ' + new Date().toLocaleTimeString() + ' · polling every 20s';
    }).catch(function (e) {
      document.getElementById('foot').textContent = 'could not reach her repo (' + e + '), retrying';
    });
  }

  document.querySelectorAll('.tab').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.tab').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on'); feed = b.dataset.feed; first = true; seen = {}; poll();
    });
  });

  poll();
  setInterval(poll, 20000);
})();
