/* arkitect web: five screens over the server's JSON (arkitect/web/server.py).
   Workspace, Sheets, Gate, Decisions, Review -- the designs in "Arkitect Web UI".
   Everything shown is a --json tool's output or a file the workspace holds; every button
   that changes something runs the command a person would type, and says what it printed. */
'use strict';

// ------------------------------------------------------------------ small tools

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, '');
    else el.setAttribute(k, v);
  }
  add(el, kids);
  return el;
}
function add(el, kids) {
  for (const k of kids.flat(Infinity)) {
    if (k === null || k === undefined || k === false) continue;
    el.appendChild(k instanceof Node ? k : document.createTextNode(String(k)));
  }
  return el;
}
const svg = (path) => {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('width', '20'); s.setAttribute('height', '20'); s.setAttribute('viewBox', '0 0 24 24');
  s.setAttribute('fill', 'none'); s.setAttribute('stroke', 'currentColor'); s.setAttribute('stroke-width', '1.6');
  s.innerHTML = path;              // constant markup, below
  return s;
};
const ICON = {
  workspace: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
  sheets: '<rect x="3" y="4" width="18" height="16"/><line x1="16" y1="4" x2="16" y2="20"/><line x1="16" y1="15" x2="21" y2="15"/>',
  gate: '<path d="M4 12l5 5L20 6"/>',
  decisions: '<path d="M12 3v18M5 7h14M5 7l-3 7h6zM19 7l-3 7h6z"/>',
  review: '<circle cx="11" cy="11" r="6"/><line x1="16" y1="16" x2="21" y2="21"/>',
};
const fmtN = (n) => (n === null || n === undefined) ? '—' : Number(n).toLocaleString('en-US');
const today = () => new Date().toISOString().slice(0, 10);

async function api(path, body) {
  const opt = body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
  const r = await fetch(path, opt);
  const data = await r.json().catch(() => ({ error: 'the server answered ' + r.status }));
  if (!r.ok) throw new Error(data.error || ('HTTP ' + r.status));
  return data;
}
async function job(path, body) {
  let j = await api(path, body || {});
  while (j.status === 'running') {
    await new Promise((res) => setTimeout(res, 700));
    j = await api('/api/jobs/' + j.id);
  }
  if (j.status === 'failed') throw new Error(j.error);
  return j.result;
}
let toastTimer = null;
function toast(msg, err) {
  document.querySelectorAll('.toast').forEach((t) => t.remove());
  const t = h('div', { class: 'toast' + (err ? ' err' : ''), role: 'status' }, msg);
  document.body.appendChild(t);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.remove(), err ? 12000 : 5000);
}

// ------------------------------------------------------------------ what the pages share

const S = { ws: null, projects: {}, decisions: null };      // loaded once, refreshed on writes

async function loadWorkspace(force) {
  if (!S.ws || force) S.ws = await api('/api/workspace');
  return S.ws;
}
async function loadProject(slug, force) {
  if (!S.projects[slug] || force) S.projects[slug] = await api('/api/projects/' + slug);
  return S.projects[slug];
}
async function loadDecisions(force) {
  if (!S.decisions || force) S.decisions = (await api('/api/decisions')).decisions;
  return S.decisions;
}
function refresh() { S.ws = null; S.projects = {}; S.decisions = null; }

const DISCIPLINE = { G: 'GENERAL', C: 'CIVIL', A: 'ARCHITECTURAL', S: 'STRUCTURAL', M: 'MECHANICAL',
                     E: 'ELECTRICAL', P: 'PLUMBING', L: 'LANDSCAPE', F: 'FIRE' };
const projName = (slug) => (S.projects[slug] && S.projects[slug].address) || slug;
const movedOf = (g, slug) => ((g && g.projects[slug] && g.projects[slug].sheets_moved) || [])
  .map((m) => Object.assign({}, m, { sheet: m.sheet.split('#')[0] })).filter((m) => m.sheet !== '(document)');

function nav(active) {
  const ws = S.ws || {}; const g = ws.gate;
  const open = (S.decisions || []).filter((d) => d.status === 'open').length;
  const openF = Object.values(S.projects).reduce((n, p) => n + (p.sheets || []).reduce((m, s) => m + s.open, 0), 0);
  const item = (href, label, key, extra, cls) => h('a', { href, class: 'item' + (active === key ? ' on' : '') },
    label, extra !== undefined ? h('span', { class: cls || '' }, extra) : null);
  return h('nav', { class: 'nav', 'aria-label': 'Workspace' },
    h('div', { class: 'brand' }, h('b', {}, 'ARKITECT'), h('div', {}, 'engine ' + (ws.engine || '?') + ' · schema ' + (ws.schema || '?'))),
    h('div', { class: 'links' },
      item('#/', 'Workspace', 'workspace'),
      item('#/gate', 'Gate', 'gate', g ? (g.ok ? 'PASS' : 'FAIL') : 'not run', g ? (g.ok ? 'pass' : 'fail') : ''),
      item('#/decisions', 'Decisions', 'decisions', S.decisions ? String(open) : ''),
      item('#/review', 'Review', 'review', openF + ' open')),
    h('div', { class: 'section' }, 'PROJECTS'),
    (ws.projects || []).map((p) => h('a', { class: 'proj', href: '#/sheets/' + p.slug },
      h('span', {}, projName(p.slug)),
      h('span', {}, p.slug + (S.projects[p.slug] ? ' · ' + S.projects[p.slug].sheets.length + ' sheets' : '')))),
    h('div', { class: 'foot' }, h('div', { title: ws.workspace }, (ws.workspace || '').replace(/^\/Users\/[^/]+/, '~')),
      h('div', {}, (ws.designer || 'the designer') + ' · designer of record')));
}
function rail(active) {
  const a = (href, key, label) => h('a', { href, 'aria-label': label, title: label, class: active === key ? 'on' : '' }, svg(ICON[key]));
  return h('nav', { class: 'rail', 'aria-label': 'Workspace' },
    h('a', { href: '#/', class: 'brand', 'aria-label': 'Workspace' }, 'AK'),
    a('#/', 'workspace', 'Workspace'), a('#/sheets', 'sheets', 'Sheets'), a('#/gate', 'gate', 'Gate'),
    a('#/decisions', 'decisions', 'Decisions'), a('#/review', 'review', 'Review'));
}
function page(side, ...main) {
  const app = document.getElementById('app');
  app.replaceChildren(side, ...main);
}
function loading(side, what) {
  page(side, h('main', {}, h('div', { class: 'empty' }, h('span', { class: 'spin' }), ' ', what)));
}
function failed(side, err) {
  page(side, h('main', {}, h('div', { class: 'empty' }, h('b', {}, 'Could not load: '), String(err.message || err))));
}
const later = (label) => h('button', { type: 'button', class: 'btn', disabled: true,
  title: 'An agent job: the next milestone. Ask in the terminal for now.' }, label);

// ------------------------------------------------------------------ 1 · workspace

async function viewWorkspace() {
  loading(nav('workspace'), 'Reading the workspace…');
  const ws = await loadWorkspace();
  const decs = await loadDecisions();
  const draw = () => page(nav('workspace'), workspaceMain(ws, decs));
  draw();
  for (const p of ws.projects) loadProject(p.slug).then(draw).catch((e) => toast(p.slug + ': ' + e.message, true));
}

function workspaceMain(ws, decs) {
  const g = ws.gate;
  const moved = g ? Object.keys(g.projects).reduce((n, s) => n + movedOf(g, s).length, 0) : null;
  const dirty = ws.changed.length;
  const counts = { open: 0, waiting: 0, confirmed: 0, superseded: 0 };
  decs.forEach((d) => { counts[d.status] = (counts[d.status] || 0) + 1; });
  const open = decs.filter((d) => d.status === 'open');
  const runGate = (full) => async () => {
    toast(full ? 'Running the full gate (about 40 s)…' : 'Running the gate…');
    try { await job('/api/gate', { full }); refresh(); await viewWorkspace(); toast('The gate ran.'); }
    catch (e) { toast(e.message, true); }
  };
  const verdict = g ? (g.ok ? 'pass' : 'fail') : 'none';
  return h('main', {},
    h('header', { class: 'bar' },
      h('div', { class: 'row', style: { alignItems: 'baseline', gap: '14px' } },
        h('h1', {}, 'WORKSPACE'),
        h('span', { class: 'sub' }, ws.branch + ' @ ' + ws.head + ' · ' + (dirty ? dirty + ' changed' : 'clean'))),
      h('div', { class: 'row' }, later('New address'),
        h('button', { type: 'button', class: 'btn', onclick: runGate(true) }, 'Run full gate'),
        h('button', { type: 'button', class: 'btn dark', onclick: runGate(false) }, 'Run gate'))),
    h('div', { class: 'ws-body' },
      h('div', { class: 'ws-left' },
        h('section', { class: 'panel gatebar', 'aria-label': 'Gate status' },
          h('a', { href: '#/gate', class: 'verdict ' + verdict, style: { textDecoration: 'none', color: '#fff' } },
            h('span', { class: 'label', style: { color: '#fff' } }, 'GATE · ' + (g ? g.tier.toUpperCase() : '—')),
            h('b', {}, g ? (g.ok ? 'PASSED' : 'FAILED') : 'NOT RUN'),
            h('span', {}, g ? ((g.ok ? 'every oracle ran' : (g.failures.length + ' failed')) + ' · ' + (g.ran_at || '').slice(11, 16)) : 'run it to see the set')),
          gateCell('PYFLAKES', g && g.pyflakes.ran ? (g.pyflakes.ok ? 'clean' : 'dead code') : '—',
            g ? (g.pyflakes.ok ? 'no dead imports' : 'see the gate') : '', g && g.pyflakes.ok ? 'var(--green)' : null),
          gateCell('TWINS', g ? [String(g.twins.total), h('span', { style: { fontSize: '13px', fontWeight: 400, color: 'var(--muted)' } }, ' / ' + g.twins.ceiling + ' ceiling')] : '—',
            g ? h('div', { class: 'meter' }, h('div', { style: { width: Math.min(100, 100 * g.twins.total / g.twins.ceiling) + '%' } })) : ''),
          gateCell('TESTS', g ? (g.tests.ran ? (g.tests.ok ? 'passed' : 'FAILED') : 'not run') : '—',
            g ? (g.tests.summary || '') : '', g && g.tests.ran ? (g.tests.ok ? 'var(--green)' : 'var(--rust)') : 'var(--muted)'),
          gateCell('SHEETS MOVED', moved === null ? '—' : String(moved), 'against ' + (g ? g.base.split(' ')[0] : 'HEAD'))),
        h('div', { class: 'cards' }, ws.projects.map((p) => projectCard(p, g))),
        h('section', { class: 'panel commits', 'aria-label': 'Recent commits' },
          h('div', { class: 'panel-h' }, h('h2', {}, 'RECENT COMMITS'),
            h('span', { class: 'muted', style: { fontSize: '12px' } }, 'each commit is one change; a moved sheet names itself')),
          h('div', { class: 'scroll' }, ws.commits.map((c) => h('div', { class: 'commit' },
            h('span', { class: 'mono muted' }, c.sha), h('span', { class: 's', title: c.subject }, c.subject),
            h('span', { class: 'm', style: { color: c.moved && !/^none/.test(c.moved) ? 'var(--rust)' : 'var(--muted)' }, title: c.moved || '' },
              c.moved || 'no sheet moved')))))),
      h('aside', { class: 'panel waiting', 'aria-label': 'Waiting on you' },
        h('div', { class: 'panel-h', style: { display: 'block' } }, h('h2', {}, 'WAITING ON YOU'),
          h('div', { class: 'muted', style: { fontSize: '12px', marginTop: '4px' } }, counts.open + ' calls the agents made that only you can confirm')),
        h('div', { class: 'counts' },
          [['open', ''], ['waiting', 'var(--amber)'], ['confirmed', ''], ['superseded', '']].map(([k, c]) =>
            h('div', {}, h('b', { style: { color: c || 'inherit' } }, counts[k] || 0), h('small', {}, k)))),
        h('div', { class: 'scroll', style: { flexGrow: 1 } }, open.slice(0, 12).map((d) => h('a', { class: 'dq', href: '#/decisions/' + d.id },
          h('div', {}, h('span', { class: 'id' }, d.id), h('span', { class: 'where' }, (d.projects || []).join(' · '))),
          h('div', { class: 'q' }, d.title)))),
        h('a', { class: 'more', href: '#/decisions' }, 'All ' + counts.open + ' open decisions →'))));
}
function gateCell(label, v, small, color) {
  return h('div', { class: 'cell' }, h('span', { class: 'label', style: { fontSize: '12px' } }, label),
    h('span', { class: 'v', style: { color: color || 'inherit' } }, v), typeof small === 'string' ? h('small', {}, small) : small);
}
function projectCard(p, g) {
  const ix = S.projects[p.slug];
  const gp = g && g.projects[p.slug];
  const trace = gp ? (gp.trace.ok ? (movedOf(g, p.slug).length ? ['warn', 'moved'] : ['ok', 'trace ok']) : ['bad', 'no build']) : null;
  const findings = ix && ix.has_review ? ix.sheets.reduce((n, s) => n + s.open, 0) + ' of ' + ix.sheets.reduce((n, s) => n + s.findings, 0) : '—';
  const docs = ix ? ix.sheets.reduce((acc, s) => { acc[s.doc] = (acc[s.doc] || 0) + 1; return acc; }, {}) : {};
  const nSheets = ix ? Object.values(docs).join(' + ') : '…';
  const tb = ix ? ix.titleblock : [];
  const first = tb.length ? tb[0][1] : [];
  const code = tb.find((b) => b[0] === 'CODE');
  const zoning = code ? (code[1].find((l) => /^ZONING/.test(l)) || '').replace(/^ZONING:\s*/, '') : '';
  const units = first.map((l) => /(\d+) DWELLING UNIT/.exec(l)).find(Boolean);
  const bldgs = first.map((l) => /(\d+) DETACHED/.exec(l)).find(Boolean);
  const cap = (x) => x.toLowerCase().replace(/\b[a-z]/g, (c) => c.toUpperCase());
  const program = [units ? units[1] + ' unit' + (units[1] === '1' ? '' : 's') : null,
                   bldgs ? bldgs[1] + ' detached building' + (bldgs[1] === '1' ? '' : 's') : null,
                   zoning ? cap(zoning.replace(/\s+(\S+)$/, '')) + ' ' + zoning.split(/\s+/).pop() : null].filter(Boolean).join(' · ');
  const file = (re, label) => { const f = p.deliverables.find((x) => re.test(x)); return f ? h('a', { class: 'small', href: '/api/projects/' + p.slug + '/file/' + f }, label) : null; };
  return h('article', { class: 'panel', style: { display: 'flex', flexDirection: 'column' } },
    h('div', { class: 'card-h' },
      h('div', {}, h('h2', {}, ix ? ix.address : p.slug),
        h('div', { class: 'muted', style: { fontSize: '13px', marginTop: '2px' } }, ix ? program : 'reading the build…')),
      trace ? h('span', { class: 'tag ' + trace[0] }, trace[1]) : null),
    h('div', { class: 'stats' },
      stat('SHEETS', nSheets), stat('TRACE CALLS', gp ? fmtN(gp.trace.calls) : '—'), stat('OPEN FINDINGS', findings),
      stat('DIGEST', h('span', { class: 'mono', style: { fontSize: '13px' } }, (p.digest || '').slice(0, 8) + '…')),
      stat('SHEET TEXT', gp ? (gp.sheet_text.findings.length + ' overlaps') : '—', true),
      stat('DXF', gp ? (gp.dxf.ok ? 'exported' : 'FAILED') : '—', true)),
    h('div', { class: 'card-f' },
      h('a', { href: '#/sheets/' + p.slug, class: 'btn dark sm' }, 'Open sheets'),
      file(/-permit-set\.pdf$/, 'Permit set PDF'), file(/-zoning-site-plan\.pdf$/, 'Zoning sheet'), file(/\.dxf$/, 'DXF')));
}
const stat = (label, v, sm) => h('div', {}, h('div', { class: 'label' }, label), h('div', { class: 'v' + (sm ? ' sm' : '') }, v));

// ------------------------------------------------------------------ 2 · sheets

const V = { zoom: 'fit', tab: 'findings', sel: null };

async function viewSheets(slug, no) {
  loading(rail('sheets'), 'Reading the build…');
  const ws = await loadWorkspace();
  slug = slug || (ws.projects[0] && ws.projects[0].slug);
  if (!slug) return failed(rail('sheets'), new Error('no project in this workspace'));
  const ix = await loadProject(slug);
  no = no || ix.sheets[0].no;
  if (!ix.sheets.find((s) => s.no === no)) return failed(rail('sheets'), new Error(slug + ' draws no ' + no));
  const review = ix.has_review ? (await api('/api/projects/' + slug + '/review')).findings.filter((f) => f.sheet === no) : [];
  if (!review.find((f) => f.id === V.sel)) V.sel = review.length ? review[0].id : null;
  const sheet = ix.sheets.find((s) => s.no === no);
  const decs = api('/api/projects/' + slug + '/decisions/' + no);

  const img = h('img', { alt: 'Sheet ' + no + ', ' + sheet.title, src: '/api/projects/' + slug + '/sheet/' + no + '.png' });
  const wrap = h('div', { class: 'sheetwrap' }, img);
  const stage = h('div', { class: 'stage' },
    h('div', { class: 'empty', id: 'rendering', style: { position: 'absolute', inset: '0', textAlign: 'center', paddingTop: '120px' } },
      h('span', { class: 'spin' }), ' Rendering ' + projName(slug) + '… (one build, every sheet, then cached)'));
  stage.appendChild(wrap);
  const zoomLabel = h('span', { class: 'mono', style: { width: '48px', textAlign: 'center', fontSize: '12px' } }, 'fit');
  const fit = () => {
    if (!img.naturalWidth) return;
    const W = stage.clientWidth - 40, H = stage.clientHeight - 40;
    const k = V.zoom === 'fit' ? Math.min(W / img.naturalWidth, H / img.naturalHeight) : V.zoom;
    wrap.style.width = Math.round(img.naturalWidth * k) + 'px';
    wrap.style.height = Math.round(img.naturalHeight * k) + 'px';
    zoomLabel.textContent = V.zoom === 'fit' ? 'fit' : Math.round(k * 100) + '%';
  };
  const zoom = (d) => () => {
    const cur = V.zoom === 'fit' ? (wrap.clientWidth / img.naturalWidth) : V.zoom;
    V.zoom = Math.max(0.15, Math.min(2, cur * d)); fit();
  };
  img.addEventListener('load', () => { const r = document.getElementById('rendering'); if (r) r.remove(); fit(); });
  img.addEventListener('error', () => { const r = document.getElementById('rendering'); if (r) r.textContent = 'The render failed: run the gate to see why.'; });
  window.onresize = fit;

  // the finding pins: at the centre of the tile each finding names (review.py's 3 x 2 grid)
  const perTile = {};
  review.forEach((f) => {
    const t = tileOf(f.where);
    const k = t ? t.r + ',' + t.c : '1,1';
    const i = perTile[k] = (perTile[k] || 0) + 1;
    const x = t ? (t.c - 0.5) / 3 : 0.05, y = t ? (t.r - 0.5) / 2 : 0.05;
    wrap.appendChild(h('button', { type: 'button', class: 'pin' + (f.id === V.sel ? ' on' : f.status === 'open' ? ' open' : ''),
      style: { left: (x * 100) + '%', top: 'calc(' + (y * 100) + '% + ' + ((i - 1) * 28) + 'px)' },
      'aria-label': 'Finding ' + f.id, onclick: () => { V.sel = f.id; V.tab = 'findings'; viewSheets(slug, no); } }, f.id));
  });

  const g = ws.gate && ws.gate.projects[slug];
  const moved = movedOf(ws.gate, slug).find((m) => m.sheet === no);
  const overlaps = g ? g.sheet_text.findings.filter((f) => String(f).startsWith(no)).length : null;
  const groups = {};
  ix.sheets.forEach((s) => { (groups[DISCIPLINE[s.no[0]] || 'OTHER'] = groups[DISCIPLINE[s.no[0]] || 'OTHER'] || []).push(s); });

  page(rail('sheets'),
    h('aside', { class: 'index', 'aria-label': 'Sheet index' },
      h('div', { class: 'pick' }, h('label', { for: 'proj', class: 'label' }, 'PROJECT'),
        h('select', { id: 'proj', class: 'select', onchange: (e) => { location.hash = '#/sheets/' + e.target.value; } },
          ws.projects.map((p) => h('option', { value: p.slug, selected: p.slug === slug }, projName(p.slug))))),
      h('div', { class: 'scroll', style: { flexGrow: 1, padding: '6px 0' } },
        Object.entries(groups).map(([name, ss]) => [h('div', { class: 'group label' }, name),
          ss.map((s) => h('button', { type: 'button', class: 'sheet' + (s.no === no ? ' on' : ''), onclick: () => { location.hash = '#/sheets/' + slug + '/' + s.no; } },
            h('b', {}, s.no), h('span', {}, s.title), h('i', {}, s.open ? s.open + ' open' : (s.findings || ''))))]))),
    h('main', {},
      h('header', { class: 'viewer-bar' },
        h('div', { style: { minWidth: 0 } }, h('div', { class: 'label', style: { fontSize: '12px' } }, ix.address + ' · ' + sheet.scale),
          h('h1', {}, h('span', { style: { marginRight: '10px' } }, no), sheet.title.toUpperCase())),
        h('div', { class: 'row', style: { gap: '6px' } },
          h('button', { type: 'button', class: 'btn icon', 'aria-label': 'Zoom out', onclick: zoom(1 / 1.25) }, '−'), zoomLabel,
          h('button', { type: 'button', class: 'btn icon', 'aria-label': 'Zoom in', onclick: zoom(1.25) }, '+'),
          h('button', { type: 'button', class: 'btn sm', onclick: () => { V.zoom = 'fit'; fit(); } }, 'Fit'),
          h('span', { style: { width: '1px', height: '28px', background: 'var(--rule)', margin: '0 6px' } }),
          h('a', { class: 'btn sm', href: '#/gate' }, 'Compare to base'), later('Review this sheet'))),
      stage,
      h('footer', { class: 'viewer-foot' },
        h('span', {}, 'page ' + sheet.page + ' of ' + ix.sheets.filter((s) => s.doc === sheet.doc).length + (sheet.doc !== 'build_set' ? ' · ' + sheet.doc.replace(/^build_/, '').replace(/_/g, ' ') : '')),
        h('span', {}, moved ? 'MOVED against ' + ws.gate.base.split(' ')[0] : (g ? 'unchanged at the last gate' : 'no gate run yet')),
        h('span', { style: { flexGrow: 1 } }),
        h('span', {}, overlaps === null ? '' : overlaps + ' strings over one another'))),
    inspector(slug, no, review, decs, g, moved, overlaps));
  requestAnimationFrame(fit);
}
function tileOf(where) {
  const m = /tile r(\d)c(\d)/.exec(where || '');
  return m ? { r: Number(m[1]), c: Number(m[2]) } : null;
}
function inspector(slug, no, review, decsP, g, moved, overlaps) {
  const body = h('div', { class: 'scroll', style: { flexGrow: 1 } });
  const tab = (k, label, n) => h('button', { type: 'button', role: 'tab', class: V.tab === k ? 'on' : '',
    onclick: () => { V.tab = k; draw(); } }, label, n !== undefined ? h('span', {}, n) : null);
  const tabs = h('div', { class: 'tabs', role: 'tablist' });
  const draw = () => {
    tabs.replaceChildren(tab('findings', 'Findings', review.length), tab('decisions', 'Decisions'), tab('checks', 'Checks'));
    body.replaceChildren();
    if (V.tab === 'findings') {
      if (!review.length) { body.appendChild(h('div', { class: 'empty' }, 'No plan-review finding on ' + no + '.')); return; }
      const f = review.find((x) => x.id === V.sel) || review[0];
      body.appendChild(findingDetail(slug, f, true));
      body.appendChild(h('div', { class: 'label', style: { padding: '10px 18px 4px' } }, 'ALL ' + review.length + ' ON THIS SHEET'));
      review.forEach((x) => body.appendChild(h('button', { type: 'button', class: 'frow' + (x.id === f.id ? ' on' : ''),
        onclick: () => { V.sel = x.id; viewSheets(slug, no); } },
        h('span', { class: 'mono' }, x.id), h('span', {}, x.finding), h('span', { class: 'st st-' + x.status, style: { textAlign: 'right' } }, statusLabel(x.status)))));
    } else if (V.tab === 'decisions') {
      body.appendChild(h('div', { class: 'empty', style: { padding: '16px 18px' } }, h('span', { class: 'spin' }), ' Asking the ledger…'));
      decsP.then((d) => {
        if (V.tab !== 'decisions') return;
        body.replaceChildren(h('div', { style: { padding: '16px 18px' } },
          h('p', { class: 'muted', style: { margin: '0 0 12px', fontSize: '13px' } },
            d.modules.length ? 'Decisions about ' + d.modules.map((m) => m.split('/').pop()).join(', ') + ', the module' + (d.modules.length > 1 ? 's' : '') + ' that draw ' + no + '.' : 'No module names ' + no + '.'),
          d.decisions.length ? d.decisions.map((x) => h('a', { class: 'dcard', href: '#/decisions/' + x.id },
            h('div', { class: 'mono', style: { fontSize: '12px', marginBottom: '4px' } }, x.id + ' ', h('span', { class: 'st st-' + (x.status === 'waiting' ? 'wontfix' : x.status === 'confirmed' ? 'fixed' : 'open') }, x.status)),
            h('div', { style: { fontSize: '13px' } }, x.title))) : h('p', { class: 'muted' }, 'None.')));
      }).catch((e) => body.replaceChildren(h('div', { class: 'empty' }, e.message)));
    } else {
      const row = (name, v, cls) => h('div', { class: 'check' }, h('span', {}, name), h('b', { class: cls || '' }, v));
      body.appendChild(h('div', { style: { padding: '8px 18px' } },
        g ? [row('Trace', g.trace.ok ? (moved ? 'moved' : 'matches') : 'no build', g.trace.ok && !moved ? '' : 'bad'),
             row('Sheet text overlaps', String(overlaps), overlaps ? 'bad' : ''),
             row('DXF export', g.dxf.ok ? 'ok' : 'failed', g.dxf.ok ? '' : 'bad'),
             row('Vocabulary lost (the set)', g.vocab_lost.length ? g.vocab_lost.length + ' strings' : 'none', g.vocab_lost.length ? 'bad' : ''),
             row('Engine', g.engine.running + (g.engine.recorded !== g.engine.running ? ' (accepted under ' + g.engine.recorded + ')' : ''))]
          : h('p', { class: 'muted' }, 'Run the gate to see this sheet\'s checks.')));
    }
  };
  draw();
  return h('aside', { class: 'inspector', 'aria-label': 'Inspector' }, tabs, body);
}
const statusLabel = (s) => ({ wontfix: 'won’t fix' }[s] || s);

function findingDetail(slug, f, compact) {
  const act = (status, label, needNote) => h('button', { type: 'button', class: 'btn sm', onclick: async () => {
    let note = null;
    if (needNote) {
      note = (document.getElementById('fnote') || {}).value || '';
      if (!note.trim()) { toast('Say why in the note first.', true); return; }
    }
    try {
      const r = await api('/api/projects/' + slug + '/' + f.id + '/' + status, note ? { note } : {});
      toast(r.printed + ' · committed ' + r.head);
      refresh(); route();
    } catch (e) { toast(e.message, true); }
  } }, label);
  const sevCls = 'sev' + (f.severity === 'major' ? ' major' : '');
  return h('div', { class: compact ? 'detail' : 'rbody' },
    h('div', { class: 'row', style: { gap: '8px', marginBottom: '8px', flexWrap: 'wrap' } },
      h('span', { class: 'mono', style: { fontWeight: 500 } }, f.id), h('span', { class: sevCls }, f.severity),
      h('span', { class: 'muted', style: { fontSize: '11px' } }, f.category + (f.verdict ? ' · verifier: ' + f.verdict : '')),
      h('span', { style: { flexGrow: 1 } }), h('span', { class: 'st st-' + f.status }, statusLabel(f.status))),
    h('p', {}, f.finding),
    h('div', { class: 'label', style: { marginBottom: '4px' } }, 'EVIDENCE'), h('p', { class: 'ev' }, f.evidence),
    f.suggest ? [h('div', { class: 'label', style: { marginBottom: '4px' } }, 'SUGGESTED'), h('p', { style: { fontSize: '13px' } }, f.suggest)] : null,
    f.notes ? h('div', { class: 'note-box' }, h('div', { class: 'label', style: { marginBottom: '4px' } }, statusLabel(f.status).toUpperCase()), h('p', {}, f.notes)) : null,
    h('div', { class: 'row', style: { gap: '8px', flexWrap: 'wrap', marginTop: '6px' } },
      compact ? h('a', { class: 'btn sm', href: '#/review/' + slug + '/' + f.id }, 'Open in review') : null,
      f.status !== 'fixed' ? act('fixed', 'Mark fixed') : null,
      f.status !== 'open' ? act('open', 'Reopen') : null,
      !compact && f.status === 'open' ? act('wontfix', 'Won’t fix', true) : null,
      later('Ask Claude to fix')),
    !compact && f.status === 'open' ? h('input', { id: 'fnote', class: 'select', style: { width: '100%', marginTop: '6px' },
      placeholder: 'A note: why it will not be fixed (Won’t fix needs one)' }) : null,
    f.status !== 'fixed' ? h('p', { class: 'm2', style: { marginTop: '6px' } },
      'Mark fixed is refused until ' + f.sheet + ' has changed since the finding (sheet md5 ' + String(f.sheet_md5 || '').slice(0, 8) + ').') : null);
}

// ------------------------------------------------------------------ 3 · gate

const G = { mode: 'swipe', split: 0.5, pick: 0, busy: false };

async function viewGate() {
  loading(rail('gate'), 'Reading the last gate run…');
  const ws = await loadWorkspace(true);
  const g = ws.gate;
  const run = (full) => async () => {
    G.busy = true; viewGateDraw(ws, g, full ? 'full' : 'fast');
    try { await job('/api/gate', { full }); refresh(); G.busy = false; await viewGate(); }
    catch (e) { G.busy = false; toast(e.message, true); viewGateDraw(ws, g); }
  };
  G.run = run;
  viewGateDraw(ws, g);
}
function viewGateDraw(ws, g, running) {
  const moved = g ? Object.keys(g.projects).flatMap((s) => movedOf(g, s).map((m) => Object.assign({ slug: s }, m))) : [];
  const status = !g ? 'NOT RUN' : g.ok ? 'PASSED' : 'FAILED' + (moved.length ? ' · ' + moved.length + ' SHEET' + (moved.length > 1 ? 'S' : '') + ' MOVED' : '');
  const header = h('header', { class: 'bar' },
    h('div', { class: 'row', style: { alignItems: 'baseline', gap: '14px' } }, h('h1', {}, 'GATE'),
      h('span', { class: 'tag ' + (!g ? 'warn' : g.ok ? 'ok' : 'bad'), style: { fontWeight: 600 } }, running ? 'RUNNING ' + running.toUpperCase() : status),
      g ? h('span', { class: 'sub' }, g.tier + ' tier · base ' + g.base + ' · ' + (g.ran_at || '').replace('T', ' ')) : null),
    h('div', { class: 'row' },
      h('button', { type: 'button', class: 'btn', disabled: G.busy, onclick: G.run(true) }, 'Run full'),
      h('button', { type: 'button', class: 'btn dark', disabled: G.busy, onclick: G.run(false) }, G.busy ? [h('span', { class: 'spin' }), ' Running…'] : (g ? 'Run again' : 'Run gate'))));
  if (!g) return page(rail('gate'), h('main', {}, header, h('div', { class: 'empty' }, 'The gate has not run from this page yet. Run it: about 5 s for the fast tier, 40 s for the full one.')));
  const o = (name, v, st) => h('div', { class: 'orow ' + (st || '') }, h('span', { class: 'dot', 'aria-hidden': 'true' }), h('span', {}, name), h('span', { class: 'v' }, v));
  const blocks = Object.entries(g.projects).map(([slug, p]) => [
    h('div', { class: 'block' }, slug.toUpperCase()),
    o('Trace', p.trace.ok ? (movedOf(g, slug).length ? 'moved' : fmtN(p.trace.calls)) : 'no build', p.trace.ok && !movedOf(g, slug).length ? '' : 'bad'),
    o('Build output', p.stdout_diff ? p.stdout_diff.split('\n').filter((l) => /^[-+][^-+]/.test(l)).length + ' lines' : 'same', p.stdout_diff ? 'bad' : ''),
    o('Sheet text', String(p.sheet_text.findings.length), p.sheet_text.ok ? '' : 'bad'),
    o('DXF export', p.dxf.ok ? 'ok' : 'failed', p.dxf.ok ? '' : 'bad'),
    o('Vocabulary', p.vocab_lost.length ? p.vocab_lost.length + ' lost' : 'none lost', p.vocab_lost.length ? 'bad' : ''),
    o('Engine', p.engine.running + (p.engine.recorded !== p.engine.running ? ' ← ' + p.engine.recorded : ''), p.engine.recorded !== p.engine.running ? 'bad' : '')]);
  blocks.push([h('div', { class: 'block' }, 'WORKSPACE'),
    o('pyflakes', g.pyflakes.ok ? 'clean' : 'dead code', g.pyflakes.ok ? '' : 'bad'),
    o('Twins', g.twins.total + '/' + g.twins.ceiling, g.twins.ok ? '' : 'bad'),
    o('Tests', g.tests.ran ? (g.tests.ok ? 'passed' : 'failed') : 'full only', g.tests.ran ? (g.tests.ok ? '' : 'bad') : 'skip')]);
  const oracles = h('section', { class: 'oracles', 'aria-label': 'Oracles' }, blocks,
    g.failures.length ? h('div', { class: 'foot' }, h('b', {}, 'FAILURES'), h('ul', { style: { paddingLeft: '16px', margin: '6px 0 0' } }, g.failures.map((f) => h('li', {}, f)))) : null,
    h('div', { class: 'foot' }, 'Exit 0 passed, 1 failed, 2 could not run. A check that did not run is never green.'));
  page(rail('gate'), h('main', {}, header, h('div', { class: 'gate-body' }, oracles, compareView(moved), changedPanel(ws, g, moved))));
}
function compareView(moved) {
  if (!moved.length) return h('section', { class: 'compare', 'aria-label': 'Moved sheets' },
    h('div', { class: 'empty' }, 'No sheet moved against the base. Nothing to compare.'));
  const m = moved[Math.min(G.pick, moved.length - 1)];
  const src = (base) => '/api/projects/' + m.slug + '/sheet/' + m.sheet + (base ? '.base.png' : '.png?moved=1');
  const cmpBox = h('div', { class: 'cmp-stage' }, h('div', { class: 'empty' }, h('span', { class: 'spin' }), ' Rendering the sheet at the base and now…'));
  const foot = h('div', { class: 'compare-f' });
  const seg = (k, label) => h('button', { type: 'button', class: G.mode === k ? 'on' : '', onclick: () => { G.mode = k; drawCmp(); } }, label);
  const segs = h('div', { class: 'seg', role: 'group', 'aria-label': 'Compare mode' });
  let now, base, boxes = [];
  const drawCmp = () => {
    segs.replaceChildren(seg('swipe', 'Swipe'), seg('overlay', 'Overlay'), seg('side', 'Side by side'));
    if (!now || !base) return;
    const W = Math.max(300, cmpBox.clientWidth - 32);
    const k = Math.min(W / (G.mode === 'side' ? 2 * now.naturalWidth + 16 : now.naturalWidth), (cmpBox.clientHeight - 32) / now.naturalHeight, 1.2);
    const w = Math.round(now.naturalWidth * k), hgt = Math.round(now.naturalHeight * k);
    const boxEls = () => boxes.map((b) => h('div', { class: 'box', style: { left: b[0] * w + 'px', top: b[1] * hgt + 'px', width: (b[2] - b[0]) * w + 'px', height: (b[3] - b[1]) * hgt + 'px' } }));
    const imgEl = (s, alt) => h('img', { src: s, alt });
    let content;
    if (G.mode === 'side') {
      const one = (s, label, alt) => h('div', { class: 'cmp', style: { width: w + 'px', height: hgt + 'px' } }, imgEl(s, alt), boxEls(), h('span', { class: 'tagl', style: { left: '8px' } }, label));
      content = h('div', { class: 'sbs' }, one(src(true), 'BASE', m.sheet + ' at the base'), one(src(false), 'NOW', m.sheet + ' now'));
    } else if (G.mode === 'overlay') {
      content = h('div', { class: 'cmp', style: { width: w + 'px', height: hgt + 'px' } },
        imgEl(src(true), m.sheet + ' at the base'), h('img', { src: src(false), alt: m.sheet + ' now', style: { mixBlendMode: 'difference' } }), boxEls(),
        h('span', { class: 'tagl', style: { left: '8px' } }, 'DIFFERENCE: what changed shows light'));
    } else {
      const sx = Math.round(G.split * w);
      content = h('div', { class: 'cmp', style: { width: w + 'px', height: hgt + 'px' } },
        imgEl(src(false), m.sheet + ' now'),
        h('div', { class: 'clip', style: { width: (w - sx) + 'px' } }, h('img', { src: src(true), alt: m.sheet + ' at the base', style: { width: w + 'px', height: hgt + 'px' } })),
        h('div', { class: 'split', style: { left: sx + 'px' } }), boxEls(),
        h('span', { class: 'tagl', style: { left: '8px' } }, 'NOW'), h('span', { class: 'tagl', style: { right: '8px' } }, 'BASE'));
    }
    cmpBox.replaceChildren(content);
    foot.replaceChildren();
    add(foot, [
      G.mode === 'swipe' ? [h('label', { for: 'swipe' }, 'Swipe'), h('input', { id: 'swipe', type: 'range', min: 0, max: 1000, value: Math.round(G.split * 1000),
        oninput: (e) => { G.split = e.target.value / 1000; drawCmp(); } })] : h('span', { style: { flexGrow: 1 } }),
      h('span', {}, boxes.length + ' region' + (boxes.length === 1 ? '' : 's') + ' changed · trace records ' + fmtN(m.before) + ' → ' + fmtN(m.after) + (m.change !== 'changed' ? ' · ' + m.change : ''))]);
  };
  const load = (s) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('no render of ' + s)); i.src = s; });
  Promise.all([load(src(false)), load(src(true))]).then(([a, b]) => { now = a; base = b; boxes = diffBoxes(a, b); drawCmp(); })
    .catch((e) => cmpBox.replaceChildren(h('div', { class: 'empty' }, e.message)));
  window.onresize = drawCmp;
  drawCmp();
  return h('section', { class: 'compare', 'aria-label': 'Moved sheet' },
    h('div', { class: 'compare-h' },
      h('div', { class: 'pills', role: 'tablist', 'aria-label': 'Moved sheets' }, moved.map((x, i) =>
        h('button', { type: 'button', role: 'tab', class: i === G.pick ? 'on' : '', onclick: () => { G.pick = i; viewGateDraw(S.ws, S.ws.gate); } }, x.slug + ' · ' + x.sheet))),
      segs),
    cmpBox, foot);
}
function diffBoxes(a, b) {
  // changed regions: compare the two renders on a coarse grid, then merge touching cells
  const w = 240, hgt = Math.round(240 * a.naturalHeight / a.naturalWidth), cell = 4;
  const px = (img) => { const c = document.createElement('canvas'); c.width = w; c.height = hgt;
    const x = c.getContext('2d'); x.drawImage(img, 0, 0, w, hgt); return x.getImageData(0, 0, w, hgt).data; };
  let A, B;
  try { A = px(a); B = px(b); } catch (e) { return []; }
  const cols = Math.ceil(w / cell), rows = Math.ceil(hgt / cell), hit = new Uint8Array(cols * rows);
  for (let y = 0; y < hgt; y++) for (let x = 0; x < w; x++) {
    const i = (y * w + x) * 4;
    if (Math.abs(A[i] - B[i]) + Math.abs(A[i + 1] - B[i + 1]) + Math.abs(A[i + 2] - B[i + 2]) > 60) hit[((y / cell) | 0) * cols + ((x / cell) | 0)] = 1;
  }
  const seen = new Uint8Array(cols * rows), out = [];
  for (let s = 0; s < hit.length; s++) {
    if (!hit[s] || seen[s]) continue;
    let x0 = cols, y0 = rows, x1 = 0, y1 = 0; const stack = [s]; seen[s] = 1;
    while (stack.length) {
      const q = stack.pop(), cx = q % cols, cy = (q / cols) | 0;
      x0 = Math.min(x0, cx); y0 = Math.min(y0, cy); x1 = Math.max(x1, cx); y1 = Math.max(y1, cy);
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
        const nx = cx + dx, ny = cy + dy, n = ny * cols + nx;
        if (nx >= 0 && ny >= 0 && nx < cols && ny < rows && hit[n] && !seen[n]) { seen[n] = 1; stack.push(n); }
      }
    }
    out.push([x0 / cols, y0 / rows, (x1 + 1) / cols, (y1 + 1) / rows]);
  }
  return out.slice(0, 40);
}
function changedPanel(ws, g, moved) {
  const diffs = Object.entries(g.projects).filter(([, p]) => p.stdout_diff);
  const lost = Object.entries(g.projects).flatMap(([s, p]) => p.vocab_lost.map((v) => [s, v]));
  const tracked = ws.changed.filter((c) => c.state !== '??');
  const pick = new Set(tracked.map((c) => c.path));
  const bySlug = {};
  moved.forEach((m) => { (bySlug[m.slug] = bySlug[m.slug] || []).push(m.sheet); });
  const msg = h('textarea', { id: 'msg' },
    moved.length ? Object.entries(bySlug).map(([s, ss]) => s + ' ' + ss.join(', ')).join('; ') + ': \n\nSheets moved: ' + Object.entries(bySlug).map(([s, ss]) => s + ' ' + ss.join(', ')).join('; ') : '');
  const looked = h('input', { type: 'checkbox', id: 'looked' });
  let armed = false;
  const discardBtn = h('button', { type: 'button', class: 'btn', disabled: !tracked.length, onclick: async () => {
    if (!armed) { armed = true; discardBtn.textContent = 'Discard ' + pick.size + ' file' + (pick.size === 1 ? '' : 's') + ': this cannot be undone'; discardBtn.className = 'btn rust'; return; }
    try { const r = await api('/api/discard', { paths: [...pick] }); toast('Discarded: ' + r.discarded.join(', ')); refresh(); await viewGate(); }
    catch (e) { toast(e.message, true); }
  } }, 'Discard the change');
  const accept = async () => {
    if (!looked.checked) { toast('Look at every moved sheet, then say so.', true); return; }
    try {
      const r = await api('/api/accept', { message: msg.value, paths: [...pick], looked: true });
      toast('Committed ' + r.head + ': ' + r.committed.join(', ')); refresh(); await job('/api/gate', {}); await viewGate();
    } catch (e) { toast(e.message, true); }
  };
  return h('aside', { class: 'changed', 'aria-label': 'What changed' },
    h('section', {}, h('h2', {}, 'BUILD OUTPUT, BASE → NOW'),
      diffs.length ? diffs.map(([s, p]) => [h('div', { class: 'label', style: { margin: '4px 0' } }, s),
        h('pre', {}, p.stdout_diff.split('\n').filter((l) => /^[-+][^-+]/.test(l)).map((l) => h('div', { class: l[0] === '-' ? 'del' : 'add' }, l)))])
        : h('p', { class: 'muted', style: { margin: 0, fontSize: '13px' } }, 'Unchanged: every model check printed what it printed at the base.')),
    h('section', {}, h('h2', {}, 'PRINTED AT BASE, PRINTED NOWHERE NOW'),
      lost.length ? [h('div', { class: 'chips' }, lost.map(([s, v]) => h('span', { title: s }, v))),
        h('p', { class: 'muted', style: { fontSize: '12px', margin: '8px 0 0' } }, 'A lost citation or dimension is a question, not an error. Check each one is meant to go.')]
        : h('p', { class: 'muted', style: { margin: 0, fontSize: '13px' } }, 'Nothing: every citation and dimension the base printed is printed now.')),
    h('section', { style: { flexGrow: 1 } }, h('h2', {}, 'ACCEPT AND COMMIT'),
      tracked.length ? [
        h('label', { for: 'msg', style: { display: 'block' } }, 'The commit message names the sheets that moved'), msg,
        h('div', { class: 'label', style: { margin: '10px 0 4px' } }, 'FILES IN THE COMMIT (the digests gate accept writes are added)'),
        h('div', { class: 'files' }, tracked.map((c) => h('label', {}, h('input', { type: 'checkbox', checked: true,
          onchange: (e) => { if (e.target.checked) pick.add(c.path); else pick.delete(c.path); } }), c.state + ' ' + c.path))),
        h('label', { style: { marginTop: '10px' } }, looked, 'I looked at every moved sheet'),
        h('div', { class: 'row', style: { flexWrap: 'wrap', marginTop: '8px' } },
          h('button', { type: 'button', class: 'btn dark', onclick: accept }, moved.length ? 'Accept ' + moved.length + ' sheet' + (moved.length > 1 ? 's' : '') + ' and commit' : 'Commit'),
          discardBtn)]
        : h('p', { class: 'muted', style: { margin: 0, fontSize: '13px' } }, 'The working tree is clean: nothing to accept or commit.')));
}

// ------------------------------------------------------------------ 4 · decisions

const D = { filter: 'open', project: '', answers: {} };

async function viewDecisions(id) {
  loading(rail('decisions'), 'Reading the ledger…');
  const ws = await loadWorkspace();
  const all = await loadDecisions();
  const inProj = all.filter((d) => !D.project || (d.projects || []).includes(D.project) || (d.projects || []).includes('all'));
  const counts = {};
  inProj.forEach((d) => { counts[d.status] = (counts[d.status] || 0) + 1; });
  const list = inProj.filter((d) => d.status === D.filter);
  if (!id && list.length) id = list[0].id;
  const rec = id ? await api('/api/decisions/' + id).catch(() => null) : null;
  if (rec && rec.status !== D.filter && !list.find((d) => d.id === rec.id)) D.filter = rec.status;
  const shown = inProj.filter((d) => d.status === D.filter);
  const tab = (k, label) => h('button', { type: 'button', role: 'tab', class: D.filter === k ? 'on' : '', onclick: () => { D.filter = k; location.hash = '#/decisions'; viewDecisions(); } },
    label, h('span', {}, String(counts[k] || 0)));
  page(rail('decisions'),
    h('section', { class: 'dlist', 'aria-label': 'Decision list' },
      h('div', { class: 'bar' }, h('h1', {}, 'DECISIONS'),
        h('select', { class: 'select', 'aria-label': 'Project', onchange: (e) => { D.project = e.target.value; location.hash = '#/decisions'; viewDecisions(); } },
          h('option', { value: '' }, 'All projects'), ws.projects.map((p) => h('option', { value: p.slug, selected: D.project === p.slug }, projName(p.slug))))),
      h('div', { class: 'tabs', role: 'tablist' }, tab('open', 'Open'), tab('waiting', 'Waiting'), tab('confirmed', 'Confirmed'), tab('superseded', 'Superseded')),
      h('div', { class: 'scroll', style: { flexGrow: 1 } }, shown.length ? shown.map((d) => h('button', { type: 'button', class: 'drow' + (rec && d.id === rec.id ? ' on' : ''),
        onclick: () => { location.hash = '#/decisions/' + d.id; } },
        h('div', {}, h('span', { class: 'id' }, d.id), h('span', { class: 'meta' }, (d.projects || []).join(', ') + ' · ' + (d.date || '') + (d.waiting_on ? ' · on ' + d.waiting_on.split(/[(,]/)[0].trim() : ''))),
        h('div', { class: 't' }, d.title))) : h('div', { class: 'empty' }, 'None ' + D.filter + '.'))),
    rec ? decisionMain(ws, rec) : h('main', {}, h('div', { class: 'empty' }, 'Pick a decision.')));
}
function questions(ask) {
  return (ask || '').split(/(?<=\?)\s+/).map((q) => q.trim()).filter((q) => q.length > 2);
}
function decisionMain(ws, d) {
  const qs = questions(d.ask);
  const ans = D.answers[d.id] = D.answers[d.id] || {};
  const who = ws.designer || 'the designer';
  const quote = h('input', { id: 'quote', type: 'text' });
  const allKept = () => qs.every((_, i) => ans[i] === 'keep');
  const anyChange = () => qs.some((_, i) => ans[i] === 'change');
  const setQuote = () => {
    quote.value = who + ', ' + today() + ': ' + (!qs.length ? 'confirmed as drawn' : allKept()
      ? (qs.length > 1 ? 'keep all ' + qs.length + ' as drawn' : 'keep as drawn') : '');
  };
  const confirmBtn = h('button', { type: 'button', class: 'btn dark', disabled: qs.length > 0 && !allKept(),
    title: anyChange() ? 'A change is work, not a confirmation: hand it to Claude (the terminal, for now)' : (allKept() || !qs.length ? '' : 'Answer every question first'),
    onclick: async () => {
    if (anyChange()) { toast('A change is work, not a confirmation: hand it to Claude (the terminal, for now).', true); return; }
    try { const r = await api('/api/decisions/' + d.id + '/confirm', { quote: quote.value }); toast(d.id + ' confirmed · committed ' + r.head); refresh(); location.hash = '#/decisions'; await viewDecisions(); }
    catch (e) { toast(e.message, true); }
  } }, 'Confirm');
  const qEls = qs.map((q, i) => {
    const b = (v, label) => h('button', { type: 'button', class: v + (ans[i] === v ? ' on' : ''), 'aria-pressed': ans[i] === v ? 'true' : 'false',
      onclick: () => { ans[i] = v; route(); } }, label);
    return h('fieldset', { class: 'q' }, h('legend', {}, q), h('span', {}, q), h('div', { class: 'kc' }, b('keep', 'Keep'), b('change', 'Change')));
  });
  setQuote();
  const sheetsIn = (text) => [...new Set((text.match(/\b[A-Z]-\d{3}\b/g) || []))];
  const proj = (d.projects || []).find((p) => p !== 'all') || (ws.projects[0] && ws.projects[0].slug);
  const open = d.status === 'open' || d.status === 'waiting';
  return h('main', {},
    h('div', { class: 'dmain' },
      h('div', { class: 'dhead' },
        h('div', { class: 'row', style: { gap: '10px' } }, h('span', { class: 'mono', style: { fontWeight: 500 } }, d.id),
          h('span', { class: 'tag ' + (d.status === 'confirmed' ? 'ok' : d.status === 'waiting' ? 'warn' : 'bad'), style: { fontWeight: 600 } }, d.status.toUpperCase()),
          h('span', { class: 'muted', style: { fontSize: '12px' } }, (d.by === 'agent' ? 'the agent’s call' : 'the designer’s') + ' · ' + d.date + ' · ' + (d.projects || []).join(', '))),
        h('h2', {}, d.title)),
      h('div', { class: 'dgrid' },
        h('div', {},
          h('section', {}, h('h3', {}, 'WHAT WAS CHOSEN'), h('p', {}, d.decision)),
          d.status === 'waiting' && d.waiting_on ? h('section', {}, h('h3', {}, 'WAITING ON'), h('p', {}, d.waiting_on)) : null,
          d.confirmed ? h('section', {}, h('h3', {}, 'CONFIRMED'), h('p', {}, d.confirmed)) : null,
          open && qs.length ? h('section', { 'aria-label': 'Questions' }, h('h3', {}, 'ASKED OF YOU'), qEls) : null,
          (d.alternatives || []).length ? h('section', {}, h('h3', {}, 'ALTERNATIVES'), h('ul', {}, d.alternatives.map((a) => h('li', {}, a)))) : null,
          d.body ? h('section', {}, h('h3', {}, 'THE ACCOUNT'), h('div', { class: 'body-md' }, d.body.trim().replace(/\*\*|`/g, ''))) : null),
        h('aside', {},
          (d.if_reversed || []).length ? h('section', {}, h('h3', {}, 'IF REVERSED, THESE MOVE'), h('div', { class: 'moves' }, d.if_reversed.map((x) => h('div', {}, x)))) : null,
          (d.refs || []).length ? h('section', {}, h('h3', {}, 'REFS'), h('div', { class: 'moves' }, d.refs.map((x) => h('div', { class: 'mono', style: { fontSize: '12px' } }, x)))) : null,
          proj ? sheetsIn((d.if_reversed || []).join(' ') + ' ' + d.decision).slice(0, 6).map((no) =>
            h('a', { href: '#/sheets/' + proj + '/' + no, style: { display: 'block', fontWeight: 600, margin: '4px 0' } }, 'Open ' + no + ' →')) : null))),
    open ? h('footer', { class: 'dfoot' },
      h('div', {}, h('label', { for: 'quote', class: 'label' }, 'YOUR WORDS ', h('span', { style: { textTransform: 'none', letterSpacing: 0 } }, 'recorded on the decision as you write them')), quote),
      h('div', { class: 'row' }, later('Hand changes to Claude'), confirmBtn)) : null);
}

// ------------------------------------------------------------------ 5 · review

const R = { chip: 'all', slug: null };

async function viewReview(slug, id) {
  loading(rail('review'), 'Reading the plan review…');
  const ws = await loadWorkspace();
  const withReview = [];
  for (const p of ws.projects) if (p.has_review) withReview.push(p.slug);
  slug = slug || R.slug || withReview[0];
  if (!slug) return page(rail('review'), h('main', {}, h('div', { class: 'empty' }, 'No project has a plan review yet. The review-sheets skill makes one.')));
  R.slug = slug;
  const all = (await api('/api/projects/' + slug + '/review')).findings;
  const n = (fn) => all.filter(fn).length;
  const cats = {};
  all.forEach((f) => { cats[f.category] = (cats[f.category] || 0) + 1; });
  const catList = Object.entries(cats).sort((a, b) => b[1] - a[1]);
  const CC = ['#1A1C1E', '#5B5850', '#8A5A00', '#1E6B55', '#B83A14', '#A9A69E'];
  const keep = { all: () => true, open: (f) => f.status === 'open', major: (f) => f.severity === 'major', closed: (f) => f.status !== 'open' };
  const sheets = [...new Set(all.map((f) => f.sheet))];
  sheets.forEach((s) => { keep['sheet:' + s] = (f) => f.sheet === s; });
  if (!keep[R.chip]) R.chip = 'all';
  const rows = all.filter(keep[R.chip]);
  const f = all.find((x) => x.id === id) || rows[0] || all[0];
  const chip = (k, label) => h('button', { type: 'button', class: R.chip === k ? 'on' : '', onclick: () => { R.chip = k; viewReview(slug); } }, label);
  const t = f ? tileOf(f.where) : null;
  page(rail('review'), h('main', {},
    h('header', { class: 'bar' },
      h('div', { class: 'row', style: { alignItems: 'baseline', gap: '14px' } }, h('h1', {}, 'PLAN REVIEW'),
        h('span', { class: 'sub' }, projName(slug) + ' · ' + all.length + ' findings')),
      h('div', { class: 'row' },
        h('select', { class: 'select', 'aria-label': 'Project', onchange: (e) => { location.hash = '#/review/' + e.target.value; } },
          withReview.map((s) => h('option', { value: s, selected: s === slug }, projName(s)))),
        later('Review sheets…'))),
    h('div', { class: 'rstats' },
      h('div', {}, h('b', { style: { color: n(keep.open) ? 'var(--rust)' : 'inherit' } }, n(keep.open)), h('small', {}, 'open')),
      h('div', {}, h('b', {}, n((x) => x.status === 'fixed')), h('small', {}, 'fixed · ' + n((x) => x.status === 'fixed' && x.severity === 'major') + ' major')),
      h('div', {}, h('b', {}, n((x) => x.status === 'rejected')), h('small', {}, 'rejected')),
      h('div', {}, h('b', {}, n((x) => x.status === 'wontfix')), h('small', {}, 'won’t fix, with a reason')),
      h('div', {}, h('div', { class: 'catbar' }, catList.map(([c, k], i) => h('div', { title: c + ' ' + k, style: { width: (100 * k / all.length) + '%', background: CC[i % CC.length] } }))),
        h('small', {}, catList.map(([c, k]) => c + ' ' + k).join(' · ')))),
    h('div', { class: 'review-body' },
      h('section', { class: 'rtable', 'aria-label': 'Findings' },
        h('div', { class: 'rchips' }, chip('all', 'All ' + all.length), chip('open', 'Open ' + n(keep.open)), chip('major', 'Major ' + n(keep.major)),
          sheets.slice(0, 8).map((s) => chip('sheet:' + s, s)), chip('closed', 'Closed ' + n(keep.closed))),
        h('div', { class: 'rhead' }, ['ID', 'SHEET', 'CATEGORY', 'SEVERITY', 'STATUS', 'FINDING'].map((x) => h('span', {}, x))),
        h('div', { class: 'scroll', style: { flexGrow: 1 } }, rows.map((x) => h('button', { type: 'button', class: 'rrow' + (f && x.id === f.id ? ' on' : ''),
          onclick: () => { location.hash = '#/review/' + slug + '/' + x.id; } },
          h('span', { class: 'mono' }, x.id), h('span', {}, x.sheet), h('span', {}, x.category),
          h('span', { style: { color: x.severity === 'major' ? 'var(--rust)' : 'var(--ink2)', fontWeight: x.severity === 'major' ? 600 : 400 } }, x.severity),
          h('span', { class: 'st st-' + x.status }, statusLabel(x.status)), h('span', { title: x.finding }, x.finding))))),
      f ? h('aside', { class: 'rdetail', 'aria-label': 'Finding detail' },
        h('a', { class: 'crop', href: '#/sheets/' + slug + '/' + f.sheet, 'aria-label': 'Open ' + f.sheet + ' in the sheet viewer', style: cropStyle(slug, f.sheet, t) },
          h('span', {}, f.sheet + (t ? ' · tile r' + t.r + 'c' + t.c : ''))),
        findingDetail(slug, f, false)) : h('aside', { class: 'rdetail' }))));
}
function cropStyle(slug, sheet, t) {
  // the sheet render as a background, sized to show the tile a finding names (3 x 2 grid)
  const url = '/api/projects/' + slug + '/sheet/' + sheet + '.png';
  // at the sheet's own proportions (ARCH C, 4:3): three tiles across the 480 px panel
  if (!t) return { backgroundImage: 'url("' + url + '")', backgroundSize: 'contain', backgroundPosition: 'center' };
  const W = 480, bgW = 3 * W, bgH = bgW * 0.75, boxH = 300;
  const cx = (t.c - 0.5) * bgW / 3, cy = (t.r - 0.5) * bgH / 2;
  return { backgroundImage: 'url("' + url + '")', backgroundSize: bgW + 'px ' + bgH + 'px',
           backgroundPosition: (W / 2 - cx) + 'px ' + (boxH / 2 - cy) + 'px' };
}

// ------------------------------------------------------------------ the router

async function route() {
  const parts = location.hash.replace(/^#\/?/, '').split('/').filter(Boolean).map(decodeURIComponent);
  const side = parts[0] === undefined ? nav('workspace') : rail(parts[0]);
  try {
    if (!parts.length) return await viewWorkspace();
    if (parts[0] === 'sheets') return await viewSheets(parts[1], parts[2]);
    if (parts[0] === 'gate') return await viewGate();
    if (parts[0] === 'decisions') return await viewDecisions(parts[1]);
    if (parts[0] === 'review') return await viewReview(parts[1], parts[2]);
    location.hash = '#/';
  } catch (e) {
    failed(side, e);
  }
}
window.addEventListener('hashchange', route);
route();
