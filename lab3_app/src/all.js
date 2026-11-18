const { stepLine, dda, bres, bcirc, wu, ALG, bench } = require('./algos.js'); const fs = require('fs');
const pts = (f, ...a) => { const s = new Set(); f(...a, (x, y) => s.add(x + ',' + y), null); return s; };
let seed = 12345; const R = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296; const ri = () => Math.floor(R() * 81) - 40;
let dSD = 0, dSB = 0, ends = 0, cnt = 0, maxErr = 0; const ne = (P, Q) => [...P].filter(p => !Q.has(p)).length + [...Q].filter(p => !P.has(p)).length;
for (let t = 0; t < 2000; t++) { const a = [ri(), ri(), ri(), ri()], S = pts(stepLine, ...a), D = pts(dda, ...a), B = pts(bres, ...a);
  if (ne(S, D)) dSD++; if (ne(S, B)) dSB++; if (!B.has(a[0] + ',' + a[1]) || !B.has(a[2] + ',' + a[3])) ends++;
  const [x0, y0, x1, y1] = a, dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy) || 1;
  for (const p of B) { const [x, y] = p.split(',').map(Number); maxErr = Math.max(maxErr, Math.abs(dy * (x - x0) - dx * (y - y0)) / L); }
  if (B.size !== Math.max(Math.abs(dx), Math.abs(dy)) + 1) cnt++; }
let worst = 0; for (let r = 1; r <= 60; r++) for (const p of pts(bcirc, 0, 0, r)) { const [x, y] = p.split(',').map(Number); worst = Math.max(worst, Math.abs(Math.hypot(x, y) - r)); }
console.log('TEST2000', { dSD, dSB, ends, cnt, maxErr: maxErr.toFixed(3), circ: worst.toFixed(3) });
seed = 777; let bad = 0, dl = 0;
for (let t = 0; t < 3000; t++) { const a = [ri(), ri(), ri(), ri()], S = pts(stepLine, ...a), B = pts(bres, ...a), [x0, y0, x1, y1] = a, dx = x1 - x0, dy = y1 - y0; let d = 0;
  for (const P of [S, B]) for (const p of P) if (!(P === S ? B : S).has(p)) { d = 1; const [x, y] = p.split(',').map(Number);
    const e = Math.abs(dx) >= Math.abs(dy) ? Math.abs(y0 + dy * (x - x0) / dx - y) : Math.abs(x0 + dx * (y - y0) / dy - x); if (Math.abs(e - 0.5) > 1e-9) bad++; } dl += d; }
console.log('TIES3000', { dl, bad });
const med = (run, a) => { const v = []; let px = 0; for (let i = 0; i < 5; i++) { const b = bench(run, a, 100); v.push(b.us); px = b.pixels } v.sort((x, y) => x - y); return { us: v[2], pixels: px } };
const rows = []; for (const L of [10, 100, 1000, 10000]) { const a = [0, 0, L, Math.round(L * 0.6)], r = { L }; for (const k of ['step', 'dda', 'bres', 'wu']) r[k] = med(ALG[k].run, a).us; rows.push(r); }
const crow = []; for (const Rr of [10, 100, 1000, 5000]) { const b = med(bcirc, [0, 0, Rr]); crow.push({ R: Rr, us: b.us, px: b.pixels }); }
const ex = {}, mk = (f, ...a) => { const rec = [], px = new Map(); f(...a, (x, y, al = 1) => { const k = x + ',' + y, o = px.get(k); if (!o || o.a < al) px.set(k, { x, y, a: al }); }, rec); return { rec, px: [...px.values()].filter(p => p.a > 0.005) }; };
ex.line = [2, 1, 11, 6]; ex.step = mk(stepLine, 2, 1, 11, 6); ex.dda = mk(dda, 2, 1, 11, 6); ex.bres = mk(bres, 2, 1, 11, 6); ex.wu = mk(wu, 2, 1, 11, 6); ex.circ = mk(bcirc, 0, 0, 7);
fs.writeFileSync('out/data.json', JSON.stringify({ rows, crow, ex }));
console.log(rows.map(r => [r.L, ...['step', 'dda', 'bres', 'wu'].map(k => +r[k].toFixed(3))].join(' ')).join(' | ')); console.log(crow.map(c => [c.R, +c.us.toFixed(3), c.px].join(' ')).join(' | '));
