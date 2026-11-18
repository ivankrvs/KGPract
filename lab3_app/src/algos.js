/* Базовые растровые алгоритмы. plot(x,y[,a]) — вывод пикселя; rec — массив для записи строк расчёта (или null). */
const rnd = v => Math.floor(v + 0.5 + 1e-9);          // округление «половина вверх» с защитой от ошибки float

/* 1. Пошаговый алгоритм: y = k·x + b, шаг по большей проекции */
function stepLine(x0, y0, x1, y1, plot, rec) {
  const dx = x1 - x0, dy = y1 - y0;
  if (dx === 0 && dy === 0) { plot(x0, y0); rec && rec.push([0, x0, y0, x0, y0]); return; }
  if (Math.abs(dx) >= Math.abs(dy)) {
    const k = dy / dx, b = y0 - k * x0, s = dx > 0 ? 1 : -1;
    for (let x = x0, i = 0; x !== x1 + s; x += s, i++) { const y = k * x + b, r = rnd(y); plot(x, r); rec && rec.push([i, x, y, x, r]); }
  } else {
    const k = dx / dy, b = x0 - k * y0, s = dy > 0 ? 1 : -1;
    for (let y = y0, i = 0; y !== y1 + s; y += s, i++) { const x = k * y + b, r = rnd(x); plot(r, y); rec && rec.push([i, x, y, r, y]); }
  }
}
/* 2. ЦДА: приращения sx, sy за L = max(|dx|,|dy|) шагов */
function dda(x0, y0, x1, y1, plot, rec) {
  const dx = x1 - x0, dy = y1 - y0, L = Math.max(Math.abs(dx), Math.abs(dy));
  if (L === 0) { plot(x0, y0); rec && rec.push([0, x0, y0, x0, y0]); return; }
  const sx = dx / L, sy = dy / L; let x = x0, y = y0;
  for (let i = 0; i <= L; i++) { const rx = rnd(x), ry = rnd(y); plot(rx, ry); rec && rec.push([i, x, y, rx, ry]); x += sx; y += sy; }
}
/* 3. Брезенхем (отрезок), целочисленный, все октанты: d = 2·dy − dx */
function bres(x0, y0, x1, y1, plot, rec) {
  const steep = Math.abs(y1 - y0) > Math.abs(x1 - x0);
  if (steep) { [x0, y0] = [y0, x0]; [x1, y1] = [y1, x1]; }
  if (x0 > x1) { [x0, x1] = [x1, x0]; [y0, y1] = [y1, y0]; }
  const dx = x1 - x0, dy = Math.abs(y1 - y0), ys = y0 < y1 ? 1 : -1; let d = 2 * dy - dx, y = y0;
  for (let x = x0, i = 0; x <= x1; x++, i++) {
    const px = steep ? y : x, py = steep ? x : y; plot(px, py);
    rec && rec.push([i, px, py, d, d > 0 ? (ys > 0 ? '+1' : '−1') : '0']);
    if (d > 0) { y += ys; d -= 2 * dx; } d += 2 * dy;
  }
}
/* 4. Брезенхем (окружность), 8-кратная симметрия: d = 3 − 2R */
function bcirc(xc, yc, R, plot, rec) {
  let x = 0, y = R, d = 3 - 2 * R, i = 0;
  while (x <= y) {
    plot(xc + x, yc + y); plot(xc + y, yc + x); plot(xc - x, yc + y); plot(xc - y, yc + x);
    plot(xc + x, yc - y); plot(xc + y, yc - x); plot(xc - x, yc - y); plot(xc - y, yc - x);
    rec && rec.push([i++, x, y, d, d < 0 ? 'y' : 'y−1', '(' + (xc + x) + ', ' + (yc + y) + ')']);
    if (d < 0) d += 4 * x + 6; else { d += 4 * (x - y) + 10; y--; } x++;
  }
}
/* 5 (доп.). Сглаженная линия по алгоритму Ву: два пикселя на шаг, яркость = доля покрытия */
function wu(x0, y0, x1, y1, plot, rec) {
  const steep = Math.abs(y1 - y0) > Math.abs(x1 - x0);
  if (steep) { [x0, y0] = [y0, x0]; [x1, y1] = [y1, x1]; }
  if (x0 > x1) { [x0, x1] = [x1, x0]; [y0, y1] = [y1, y0]; }
  const dx = x1 - x0, g = dx === 0 ? 0 : (y1 - y0) / dx; let y = y0;
  for (let x = x0; x <= x1; x++) {
    const fl = Math.floor(y), f = y - fl, a1 = 1 - f, a2 = f;
    if (steep) { plot(fl, x, a1); plot(fl + 1, x, a2); } else { plot(x, fl, a1); plot(x, fl + 1, a2); }
    rec && rec.push([x, y, fl, a1, a2]); y += g;
  }
}
const ALG = {
  step: { name: 'Пошаговый алгоритм', run: stepLine, hdr: ['i', 'x (точн.)', 'y (точн.)', 'x', 'y'] },
  dda:  { name: 'Алгоритм ЦДА', run: dda, hdr: ['i', 'x (точн.)', 'y (точн.)', 'x', 'y'] },
  bres: { name: 'Алгоритм Брезенхема (отрезок)', run: bres, hdr: ['i', 'x', 'y', 'd', 'сдвиг по y'] },
  circ: { name: 'Алгоритм Брезенхема (окружность)', run: bcirc, circle: 1, hdr: ['i', 'x', 'y', 'd', 'шаг по y', 'точка I окт.'] },
  wu:   { name: 'Сглаженная линия (алгоритм Ву)', run: wu, hdr: ['x', 'y (точн.)', 'нижний y', 'I нижн.', 'I верх.'] }
};
/* Замер времени: среднее время одного вызова (мкс), минимум 150 мс суммарно */
function bench(run, args, minMs = 150) {
  let cnt = 0; const plot = () => { cnt++; };
  for (let i = 0; i < 30; i++) run(...args, plot, null);
  cnt = 0; let reps = 0; const t0 = performance.now(); let t;
  do { for (let i = 0; i < 20; i++) run(...args, plot, null); reps += 20; t = performance.now() - t0; } while (t < minMs);
  return { us: t * 1000 / reps, pixels: cnt / reps, reps };
}



module.exports = { stepLine, dda, bres, bcirc, wu, ALG, bench, rnd };
