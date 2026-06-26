/* ember // live build log — a pretty tail of her own coding.
 * The DEFAULT "activity" view renders EVERY commit (cycles, the box's data
 * refreshes, and every direct fix/feature) from the GitHub commits API, readable,
 * timestamped, and tagged by type, with the repetitive data-refreshes collapsed so
 * the real coding stands out. So the page is always current even between the
 * (idle-fired) numbered feature cycles. "cycle log" and "patch notes" still render
 * her LOG.md / CHANGELOG.md raw. Newest on top; new since last poll glows green. */
(function () {
  'use strict';
  var RAW = 'https://raw.githubusercontent.com/mphinance/ember/master/';
  var SRC = { log: RAW + 'LOG.md', changelog: RAW + 'CHANGELOG.md' };
  var COMMITS = 'https://api.github.com/repos/mphinance/ember/commits?per_page=80';
  var feed = 'activity';
  var seen = {};            // header -> true, to flag fresh entries
  var first = true;
  var allCommits = [];      // full commit list, for the activity stream
  var cycleTimes = {};      // cycle number -> ISO commit date
  var latestTs = null;      // newest commit of any kind (the heartbeat)
  var lastCycleNum = null, lastCycleTs = null;  // newest "cycle N" commit
  var commitsAt = 0;        // last time we hit the API (throttle)
  var lastEntries = null;   // cached parse, so we can re-render when times arrive
  // ---- vitals the campfire reads (her "face") ----
  var fireDown = false;     // any clock tripped the watchdog -> burn angry red
  var lastRefreshHr = 0;    // box data refreshes in the last hour
  var fire = null;          // the canvas fire instance
  var firePrevCycle = null, flareUntil = 0;   // detect a fresh feature-cycle landing
  var WHISPERS = [], whisperIdx = 0;           // hover one-liners (brain/ember-lines.md)

  function ago(d) {
    var s = (Date.now() - new Date(d).getTime()) / 1000;
    if (isNaN(s)) return '';
    if (s < 90) return Math.round(s) + 's ago';
    if (s < 5400) return Math.round(s / 60) + 'm ago';
    if (s < 129600) return Math.round(s / 3600) + 'h ago';
    return Math.round(s / 86400) + 'd ago';
  }
  function clock(d) {
    try {
      return new Date(d).toLocaleTimeString([],
        { hour: 'numeric', minute: '2-digit', timeZoneName: 'short' });
    } catch (e) { return ''; }
  }

  // ---- the campfire: ember's face -----------------------------------------
  // A canvas particle fire driven entirely off vitals the page already fetches.
  // It burns BRIGHT + tall when commits flow, flares GREEN when a feature cycle
  // lands, settles to glowing EMBERS when she's quiet, and goes ANGRY RED when
  // the clock-watchdog trips. No backend, no new data. "A small fire that doesn't
  // go out." On hover it whispers a line from brain/ember-lines.md, in her voice.
  function lerp(a, b, t) { return Math.round(a + (b - a) * t); }
  function lerp3(c0, c1, c2, t) {           // hot core -> mid -> smoke across a particle's life
    if (t < 0.5) { var u = t / 0.5; return [lerp(c0[0], c1[0], u), lerp(c0[1], c1[1], u), lerp(c0[2], c1[2], u)]; }
    var v = (t - 0.5) / 0.5; return [lerp(c1[0], c2[0], v), lerp(c1[1], c2[1], v), lerp(c1[2], c2[2], v)];
  }
  function makeFire(cv) {
    if (!cv || !cv.getContext) return null;
    var ctx = cv.getContext('2d'), W = cv.width, H = cv.height;
    var parts = [], mode = 'warm', target = 0.55, cur = 0.55;
    var PAL = {                              // [core, mid, smoke] per mood
      warm:  [[255, 214, 90], [255, 122, 24], [150, 40, 8]],
      green: [[150, 255, 180], [57, 255, 138], [20, 150, 80]],
      red:   [[255, 190, 120], [255, 64, 56], [120, 16, 22]]
    };
    function spawn() {
      var spread = W * (0.16 + cur * 0.12);
      parts.push({
        x: W / 2 + (Math.random() - 0.5) * spread,
        y: H - 5 - Math.random() * 3,
        vx: (Math.random() - 0.5) * 0.6,
        vy: -(0.5 + Math.random() * 1.3) * (0.5 + cur),   // taller flames at higher intensity
        life: 1,
        decay: 0.018 + Math.random() * 0.022 + (1 - cur) * 0.02, // shorter-lived when quiet
        r: 2.5 + Math.random() * 3.5
      });
    }
    function tick() {
      cur += (target - cur) * 0.05;          // ease toward the vitals-set intensity
      var flick = 0.8 + Math.sin(Date.now() / 190) * 0.12 + Math.sin(Date.now() / 70) * 0.08;
      var rate = Math.max(1, Math.round((1 + cur * 6) * flick));
      for (var i = 0; i < rate; i++) spawn();
      ctx.clearRect(0, 0, W, H);
      // dark logs + a base glow so it reads as a campfire even at embers
      var bg = ctx.createRadialGradient(W / 2, H - 3, 1, W / 2, H - 3, W * 0.55);
      var pal0 = (PAL[mode] || PAL.warm)[1];
      bg.addColorStop(0, 'rgba(' + pal0[0] + ',' + pal0[1] + ',' + pal0[2] + ',' + (0.18 + cur * 0.22) + ')');
      bg.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = bg; ctx.fillRect(0, H - 12, W, 12);
      ctx.globalCompositeOperation = 'lighter';
      var pal = PAL[mode] || PAL.warm;
      for (var j = parts.length - 1; j >= 0; j--) {
        var p = parts[j];
        p.x += p.vx; p.y += p.vy; p.vy *= 0.985; p.life -= p.decay;
        if (p.life <= 0 || p.y < 2) { parts.splice(j, 1); continue; }
        var c = lerp3(pal[0], pal[1], pal[2], 1 - p.life);
        var rad = p.r * (0.6 + p.life * 0.9);
        var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, rad);
        g.addColorStop(0, 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + (p.life * 0.85) + ')');
        g.addColorStop(1, 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',0)');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(p.x, p.y, rad, 0, 6.283); ctx.fill();
      }
      ctx.globalCompositeOperation = 'source-over';
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
    return { set: function (m, intensity) { mode = m; target = Math.max(0.12, Math.min(1, intensity)); } };
  }

  // Translate the vitals into a flame mood + intensity. Priority: a tripped clock
  // (red) beats a fresh ship (green flare) beats the normal commit-flow brightness.
  function updateFire() {
    if (!fire) return;
    var now = Date.now();
    if (lastCycleNum != null) {              // green flare for ~8s when a NEW cycle lands
      if (firePrevCycle == null) {
        if (lastCycleTs && now - new Date(lastCycleTs).getTime() < 180000) flareUntil = now + 8000;
      } else if (lastCycleNum !== firePrevCycle) {
        flareUntil = now + 8000;
      }
      firePrevCycle = lastCycleNum;
    }
    if (fireDown) { fire.set('red', 0.9); return; }
    if (now < flareUntil) { fire.set('green', 1); return; }
    var age = latestTs ? (now - new Date(latestTs).getTime()) / 60000 : 999;  // minutes since any commit
    var intensity = age <= 8 ? 1 : age >= 55 ? 0.2 : 1 - ((age - 8) / 47) * 0.8;
    if (lastRefreshHr > 2 && intensity < 0.55) intensity = 0.55;              // a busy box still glows
    fire.set('warm', intensity);
  }

  // Hover whispers, in her voice, from brain/ember-lines.md.
  function loadWhispers() {
    fetch(RAW + 'brain/ember-lines.md?t=' + Date.now())
      .then(function (r) { return r.ok ? r.text() : ''; })
      .then(function (md) {
        WHISPERS = md.split('\n').map(function (l) { return l.replace(/^\s*[-*]\s*/, '').trim(); })
          .filter(function (l) { return l && !/^#/.test(l) && !/^>/.test(l); });
        for (var i = WHISPERS.length - 1; i > 0; i--) {   // light shuffle: not the same order each load
          var k = Math.floor(Math.random() * (i + 1)), t = WHISPERS[i]; WHISPERS[i] = WHISPERS[k]; WHISPERS[k] = t;
        }
      }).catch(function () { });
  }
  function initWhisper(cv) {
    var tip = document.getElementById('whisper');
    if (!cv || !tip) return;
    var rot = null;
    function show() {
      tip.textContent = WHISPERS.length ? WHISPERS[whisperIdx++ % WHISPERS.length] : 'still warming up';
      var r = cv.getBoundingClientRect();
      tip.style.left = Math.round(r.left) + 'px';
      tip.style.top = Math.round(r.bottom + 8) + 'px';
      tip.style.opacity = '1'; tip.style.transform = 'translateY(0)';
    }
    cv.addEventListener('mouseenter', function () { show(); rot = setInterval(show, 3600); });
    cv.addEventListener('mouseleave', function () {
      if (rot) clearInterval(rot);
      tip.style.opacity = '0'; tip.style.transform = 'translateY(-4px)';
    });
  }

  // Pull commit timestamps and map them to cycle numbers (throttled).
  function fetchCommits(force) {
    if (!force && Date.now() - commitsAt < 110000) return Promise.resolve();
    commitsAt = Date.now();
    return fetch(COMMITS).then(function (r) {
      if (!r.ok) throw new Error(r.status); return r.json();
    }).then(function (commits) {
      if (!Array.isArray(commits) || !commits.length) return;
      allCommits = commits;
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
      lastRefreshHr = refreshHr;
      heartbeat(lastRefresh, refreshHr);
      watchdog(commits);
      status();
      updateFire();
      if (feed === 'activity') renderActivity();      // the always-current stream
      else if (lastEntries) render(lastEntries);      // re-paint with known times
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
      + ' &middot; <span style="color:#6b7a8d">every commit below; numbered CYCLEs are her idle-fired feature builds</span>';
  }

  // ---- clock watchdog: catch a stalled clock the way a human reads the log ----
  // Each ember "clock" leaves a footprint in the commit stream. If one goes quiet
  // past its cron interval + slack while the others keep ticking, paint a red bar.
  // This is exactly the failure that took the feature + critic clocks down for a
  // day: cron fired on schedule but the scripts were committed chmod 644, so every
  // tick died "Permission denied" — no commits, while the data clock kept flowing.
  // Watching from the commit stream the page already has means this watchdog can
  // never itself silently die (it is just part of the page).
  var CLOCKS = [
    { key: 'feature', name: 'feature clock', limitH: 5,  cron: 'cron every 2h' },
    { key: 'critic',  name: 'critic',        limitH: 15, cron: 'cron every 3h' },
    { key: 'data',    name: 'data clock',    limitH: 1,  cron: 'cron every 30m' }
  ];
  // Newest-first commits -> first match per clock is its latest tick. Michael's own
  // commits (committer "Michael H") are NOT a clock tick, so a quiet human doesn't
  // mask a dead clock.
  function lastByClock(commits) {
    var last = { feature: null, critic: null, data: null };
    commits.forEach(function (c) {
      var msg = (c.commit.message || '').split('\n')[0];
      var who = (c.commit.committer && c.commit.committer.name) || '';
      var t = new Date(c.commit.committer.date).getTime();
      var key = /scan refresh/i.test(msg) ? 'data'
        : (/^critic/i.test(msg) || who === 'ember-critic') ? 'critic'
        : (who === 'ember') ? 'feature' : null;
      if (key && last[key] == null) last[key] = t;
    });
    return last;
  }
  function watchdog(commits) {
    var el = document.getElementById('clockwatch');
    if (!el) return;
    if (!commits || !commits.length) { el.style.display = 'none'; return; }
    var last = lastByClock(commits), now = Date.now(), down = [];
    fireDown = false;
    CLOCKS.forEach(function (cl) {
      var t = last[cl.key];
      // null = no footprint in the whole commit window => long dead. Else compare age.
      if (t == null || (now - t) > cl.limitH * 3600000) down.push({ cl: cl, last: t });
    });
    if (!down.length) { el.style.display = 'none'; el.innerHTML = ''; return; }
    fireDown = true;
    el.style.display = 'block';
    var rows = down.map(function (d) {
      return '<b style="color:#fff">' + d.cl.name + '</b> silent '
        + (d.last ? '<b style="color:#fff">' + ago(d.last) + '</b>' : 'over a day (off the log)')
        + ' <span style="color:#d98">(' + d.cl.cron + ')</span>';
    });
    el.innerHTML = '<span style="font-weight:800;letter-spacing:.06em;color:#ff5b6e">⚠ CLOCK DOWN</span> &middot; '
      + rows.join(' &middot; ')
      + ' &middot; <span style="color:#c98">cron likely erroring — check /var/log/ember-*.log on the box</span>';
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

  // ---- activity stream: every commit, readable, tagged ---------------------
  // kind -> { label, bg, fg } for the little pill on each row.
  var KINDS = {
    cycle: { label: 'CYCLE', bg: '#39ff8a', fg: '#04140a' },
    critic:{ label: 'CRITIC', bg: '#c79bff', fg: '#160a24' },
    feat:  { label: 'BUILD', bg: '#7ef0ff', fg: '#04140a' },
    fix:   { label: 'FIX',   bg: '#ff5b6e', fg: '#1a0608' },
    data:  { label: 'DATA',  bg: '#243042', fg: '#9fb0c4' },
    note:  { label: 'NOTE',  bg: '#ffb000', fg: '#1a1200' },
    other: { label: '·',     bg: '#1b2230', fg: '#8c9bb0' }
  };
  function classify(msg) {
    var s = msg.toLowerCase();
    if (/^critic/.test(s)) return 'critic';
    if (/cycle\s+\d+/.test(s)) return 'cycle';
    if (/scan refresh|data refresh|refresh data|scan\.json|site data|rebuild data/.test(s)) return 'data';
    if (/^fix|bugfix|hotfix|🔴|repair|broke|patch/.test(s)) return 'fix';
    if (/^feat|feature|🟢|add |new |build |ship|implement/.test(s)) return 'feat';
    if (/queue|roadmap|goal|learn|🧠|reference|memory|note|doc/.test(s)) return 'note';
    return 'other';
  }
  function cleanMsg(msg) {
    return msg.replace(/^[🟢🔴🔵🟡🧠]\s*/, '')
              .replace(/^(feat|fix|bugfix|infra|refactor|docs|chore)(\([^)]*\))?:\s*/i, '')
              .trim();
  }

  function renderActivity() {
    var host = document.getElementById('feed');
    if (!allCommits.length) return;   // wait for the first commits fetch
    // Collapse consecutive box data-refreshes into one row so the coding shows.
    var items = [];
    allCommits.forEach(function (c) {
      var msg = (c.commit.message || '').split('\n')[0];
      var date = c.commit.committer.date;
      var kind = classify(msg);
      var prev = items[items.length - 1];
      if (kind === 'data' && prev && prev.kind === 'data') { prev.count++; return; }
      items.push({ kind: kind, msg: msg, date: date, count: 1 });
    });
    host.innerHTML = '';
    items.forEach(function (it) {
      var k = KINDS[it.kind] || KINDS.other;
      var key = 'a:' + it.date + it.msg;
      var fresh = !first && !seen[key];
      seen[key] = true;
      var div = document.createElement('div');
      div.className = 'entry' + (fresh ? ' fresh' : '');
      var label = it.kind === 'data' && it.count > 1 ? k.label + ' ×' + it.count : k.label;
      var text = it.kind === 'data'
        ? (it.count > 1 ? 'box refreshed the option data ' + it.count + ' times' : 'box refreshed the option data')
        : cleanMsg(it.msg);
      var pill = '<span class="tag" style="background:' + k.bg + ';color:' + k.fg + '">' + label + '</span>';
      var time = '<span class="ctime" style="color:#5d6b7d;font-weight:600;font-size:11px;margin-left:8px">'
        + clock(it.date) + ' · ' + ago(it.date) + '</span>';
      var h = document.createElement('div');
      h.className = 'ehead';
      h.style.fontSize = '13px';
      h.style.fontWeight = it.kind === 'data' ? '600' : '800';
      if (it.kind === 'data') { div.style.opacity = '.62'; }
      h.innerHTML = pill + '<span style="color:' + (it.kind === 'data' ? '#8c9bb0' : '#d8e2ee') + '">'
        + esc(text) + '</span>' + time;
      div.appendChild(h);
      host.appendChild(div);
    });
    first = false;
  }

  function poll() {
    if (feed === 'activity') {
      fetchCommits(false).then(function () { renderActivity(); status(); });
      return;
    }
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

  fire = makeFire(document.getElementById('fire'));
  initWhisper(document.getElementById('fire'));
  loadWhispers();

  fetchCommits(true);
  poll();
  setInterval(poll, 20000);
  setInterval(updateFire, 20000);   // let embers fade live between commit fetches
})();
