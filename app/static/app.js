const LANG = document.documentElement.lang === 'en' ? 'en' : 'id';
const T = {
  id: {
    names: { kex: 'Key exchange PQ', cert: 'Sertifikat', ssh: 'SSH', tls: 'Versi TLS' },
    levels: { crit: 'KRITIS', high: 'PERHATIAN', info: 'CATATAN', good: 'BAIK' },
    status: { 'SIAP PQC': 'siap PQC', 'SEBAGIAN': 'sebagian siap', 'BELUM SIAP': 'belum siap', '-': '–' },
    locale: 'id-ID', inRange: 'dalam rujukan', below: 'di bawah nilai rujukan', critical: 'kritis',
    title: 'Hasil pemeriksaan kesiapan PQC', sub: 'Diperiksa dari luar, read&#8209;only', sample: 'CONTOH',
    host: 'Host', ip: 'Alamat IP', time: 'Waktu pemeriksaan', failed: 'Tidak dapat diperiksa',
    caption: 'Hasil', head: ['Pemeriksaan', 'Hasil', 'Nilai rujukan', 'Nilai', 'Flag', 'Bobot'],
    total: s => `Skor komposit, status ${s}`,
    legend: 'Nilai 0–100 per pemeriksaan. L: di bawah nilai rujukan. !: kritis. Skor komposit = rata-rata tertimbang dengan bobot.',
    how: 'Cara menghitung', howHref: '/metodologi#skor', conclusion: 'Kesimpulan', tech: 'Rincian teknis',
    end: d => `Akhir hasil · durasi ${d} detik`, read: 'Cara membaca hasil ini', readHref: '#membaca',
    samplePdf: 'Lihat laporan PDF-nya', pdf: 'Unduh PDF',
    batchHead: ['Host', 'Skor', 'Grade'], batchFail: 'gagal', avg: a => `Rata-rata ${a}.`, allPdf: 'Unduh semua sebagai PDF',
    needTarget: 'Isi minimal satu target.', tooMany: 'Maksimal 4 target per pemeriksaan.', needCheck: 'Pilih minimal satu panel pemeriksaan.',
    scanning: (n, s) => `Memeriksa ${n} target… ${s} detik`, done: s => `Selesai dalam ${s} detik.`,
    badCode: 'Kode akses salah. Minta kode lewat WhatsApp di bawah.', server: c => `Server membalas ${c}. Coba lagi.`,
    offline: 'Tidak terhubung ke server. Periksa koneksi lalu coba lagi.',
    wa: 'Halo MiraeStudio, saya ingin kode akses SecScan PQC untuk memeriksa: ',
  },
  en: {
    names: { kex: 'PQ key exchange', cert: 'Certificate', ssh: 'SSH', tls: 'TLS versions' },
    levels: { crit: 'CRITICAL', high: 'ATTENTION', info: 'NOTE', good: 'GOOD' },
    status: { 'SIAP PQC': 'PQC-ready', 'SEBAGIAN': 'partly ready', 'BELUM SIAP': 'not ready', '-': '–' },
    locale: 'en-GB', inRange: 'within reference', below: 'below the reference value', critical: 'critical',
    title: 'PQC readiness result', sub: 'Checked from outside, read&#8209;only', sample: 'SAMPLE',
    host: 'Host', ip: 'IP address', time: 'Checked at', failed: 'Could not be checked',
    caption: 'Results', head: ['Check', 'Result', 'Reference value', 'Score', 'Flag', 'Weight'],
    total: s => `Composite score, ${s}`,
    legend: 'Score 0–100 per check. L: below the reference value. !: critical. Composite score = weighted average using the weights.',
    how: 'How it is scored', howHref: '/en/methodology#score', conclusion: 'Conclusion', tech: 'Technical details',
    end: d => `End of result · took ${d} s`, read: 'How to read this result', readHref: '#reading',
    samplePdf: 'See its PDF report', pdf: 'Download PDF',
    batchHead: ['Host', 'Score', 'Grade'], batchFail: 'failed', avg: a => `Average ${a}.`, allPdf: 'Download all as PDF',
    needTarget: 'Enter at least one target.', tooMany: 'At most 4 targets per check.', needCheck: 'Pick at least one check.',
    scanning: (n, s) => `Checking ${n} target${n > 1 ? 's' : ''}… ${s} s`, done: s => `Done in ${s} s.`,
    badCode: 'Wrong access code. Ask for one on WhatsApp below.', server: c => `The server answered ${c}. Try again.`,
    offline: 'Cannot reach the server. Check your connection and try again.',
    wa: 'Hi MiraeStudio, I would like a SecScan PQC access code to check: ',
  },
}[LANG];

const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const ORDER = ['kex', 'cert', 'ssh', 'tls'];
const when = iso => new Date(iso).toLocaleString(T.locale, { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Jakarta' }) + ' WIB';

function flag(pct) {
  if (pct >= 100) return `<span class="ok" aria-label="${T.inRange}"></span>`;
  if (pct >= 50) return `<span class="L" title="${T.below}">L</span>`;
  return `<span class="crit" title="${T.critical}">!</span>`;
}

function sheet(r, { no, sample, anchors, pdf }) {
  const host = esc((r.host || r.target) + (r.port && r.port !== 443 ? ':' + r.port : ''));
  const head = `<div class="sheet-head">
      <div><div class="sheet-title">${T.title}</div><div class="sheet-sub">${T.sub}</div></div>
      <div class="sheet-no">No. ${esc(no)}${sample ? `<br><span class="sample-tag">${T.sample}</span>` : ''}</div>
    </div>`;
  if (r.error) {
    return `<article class="sheet">${head}
      <dl class="patient"><div><dt>${T.host}</dt><dd>${host}</dd></div></dl>
      <p class="sheet-error">${T.failed}: ${esc(r.error)}.</p></article>`;
  }
  const comps = ORDER.map(k => r.components.find(c => c.key === k)).filter(Boolean);
  const rows = comps.map((c, i) => `<tr${anchors ? ` id="row-${c.key}"` : ''} class="${c.pct < 100 ? 'out' : ''}" style="--i:${i}">
      <td class="name">${T.names[c.key]}</td>
      <td class="val">${esc(c.result)}</td>
      <td class="ref">${esc(c.ref)}</td>
      <td class="num" data-label="${T.head[3]}">${c.pct}</td>
      <td class="flag">${flag(c.pct)}</td>
      <td class="num" data-label="${T.head[5]}">${c.max}</td>
    </tr>`).join('');
  const findings = r.findings.map(f => `<li><span class="lvl lvl-${f.level}">${T.levels[f.level]}</span>
      <div><b>${esc(f.title)}</b><p>${esc(f.text)}</p></div></li>`).join('');
  const tech = r.details.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join('');
  const th = T.head.map((h, i) => `<th scope="col"${i === 3 || i === 5 ? ' class="num"' : ''}>${h}</th>`).join('');
  return `<article class="sheet">${head}
    <dl class="patient">
      <div><dt>${T.host}</dt><dd>${host}</dd></div>
      <div><dt>${T.ip}</dt><dd>${esc(r.ip)}</dd></div>
      <div><dt>${T.time}</dt><dd>${esc(when(r.scanned_at))}</dd></div>
    </dl>
    <table class="results">
      <caption>${T.caption}</caption>
      <thead><tr>${th}</tr></thead>
      <tbody>${rows}</tbody>
      <tfoot><tr style="--i:${comps.length}"><td colspan="6"><div class="total">
        <span>${esc(T.total(T.status[r.pqc_status] || r.pqc_status))}</span>
        <span class="score">${r.score}<span class="mono" style="font-size:16px">/100</span></span>
        <span class="grade" aria-label="Grade ${r.grade}">${r.grade}</span></div></td></tr></tfoot>
    </table>
    <p class="legend">${T.legend} <a href="${T.howHref}">${T.how}</a></p>
    ${findings ? `<section class="conclusion" style="--i:${comps.length + 1}"><h3>${T.conclusion}</h3><ol>${findings}</ol></section>` : ''}
    <details class="tech"><summary>${T.tech}</summary><table>${tech}</table></details>
    <div class="sheet-foot"><span>${T.end(r.duration)}</span><span>${sample ? `<a href="${T.readHref}">${T.read}</a> · ` : ''}<a class="pdf" href="${pdf}">${sample ? T.samplePdf : T.pdf}</a></span></div>
  </article>`;
}

function render(data) {
  const pdf = `/api/report/${data.id}.pdf?lang=${LANG}`;
  const code = data.id.slice(0, 8).toUpperCase();
  let html = '';
  if (data.results.length > 1) {
    const rows = data.results.map(r => `<tr><td class="mono">${esc(r.host || r.target)}</td><td class="mono">${r.error ? '–' : r.score}</td><td class="mono">${r.error ? T.batchFail : r.grade}</td></tr>`).join('');
    html += `<div class="batch"><table><thead><tr>${T.batchHead.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>
      <p class="legend">${T.avg(data.summary.avg)} <a href="${pdf}">${T.allPdf}</a></p></div>`;
  }
  html += data.results.map((r, i) => sheet(r, { no: `${code}-${i + 1}`, anchors: false, pdf })).join('');
  const box = $('#sheets');
  box.classList.remove('printing');
  box.innerHTML = html;
  void box.offsetWidth;
  box.classList.add('printing');
}

const box = $('#sheets');
box.innerHTML = sheet(JSON.parse($('#sample').textContent), { no: box.dataset.sampleNo, sample: true, anchors: true, pdf: box.dataset.samplePdf });
try { $('#pw').value = localStorage.getItem('scanpw') || ''; } catch (_) {}
$('#ask').href = 'https://wa.me/6289503386642?text=' + encodeURIComponent(T.wa);

$('#slip').addEventListener('submit', async e => {
  e.preventDefault();
  const targets = $('#targets').value.split(/[\n,]+/).map(t => t.trim()).filter(Boolean);
  const checks = [...document.querySelectorAll('input[name=check]:checked')].map(i => i.value);
  const status = $('#status');
  const fail = msg => { status.className = 'status err'; status.textContent = msg; };
  status.className = 'status';
  if (!targets.length) return fail(T.needTarget);
  if (targets.length > 4) return fail(T.tooMany);
  if (!checks.length) return fail(T.needCheck);
  $('#go').disabled = true;
  const t0 = Date.now();
  const secs = () => Math.round((Date.now() - t0) / 1000);
  const tick = () => status.textContent = T.scanning(targets.length, secs());
  tick();
  const timer = setInterval(tick, 500);
  try {
    const res = await fetch('/api/scan', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Scan-Password': $('#pw').value }, body: JSON.stringify({ targets, checks, lang: LANG }) });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) throw new Error(T.badCode);
    if (!res.ok) throw new Error(data.detail || T.server(res.status));
    try { localStorage.setItem('scanpw', $('#pw').value); } catch (_) {}
    render(data);
    status.textContent = T.done(secs());
    box.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
  } catch (err) {
    fail(err.message === 'Failed to fetch' ? T.offline : err.message);
  } finally {
    clearInterval(timer);
    $('#go').disabled = false;
  }
});
