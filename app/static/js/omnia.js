// Gedeelde hulpfuncties voor de demopagina's.

const Omnia = {
  esc: (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c])),
  tijd: (iso) => iso.slice(11, 19),

  async acties() {
    return (await fetch("/api/acties")).json();
  },

  // Stuurt een klantbericht (tekst en/of foto). Geeft de foutmelding terug, of null.
  async stuur(tekst, foto = null) {
    if (!tekst.trim() && !foto) return null;
    const data = new FormData();
    data.append("tekst", tekst);
    if (foto) data.append("foto", foto);
    const r = await fetch("/api/bericht", {method: "POST", body: data});
    if (r.ok) return null;
    try { return (await r.json()).detail; } catch { return "Versturen mislukt."; }
  },

  async reset() {
    await fetch("/api/reset", {method: "POST"});
  },

  // Koppelt elke melding in de gewone rij aan haar foto en AI-uitvoer.
  meldingen(acties) {
    return acties.filter((a) => a.soort === "gewone_rij").map((rij) => {
      const erna = acties.filter((a) => a.id > rij.id && a.klant === rij.klant);
      const volgendeRij = erna.find((a) => a.soort === "gewone_rij");
      const binnen = (a) => !volgendeRij || a.id < volgendeRij.id;
      const bericht = acties.filter((a) => a.soort === "bericht_in" && a.id < rij.id && a.klant === rij.klant).at(-1);
      return {
        rij,
        foto_url: bericht?.foto_url,
        ai: erna.find((a) => a.soort === "ai_uitvoer" && binnen(a)),
        fout: erna.find((a) => a.soort === "ai_fout" && binnen(a)),
      };
    });
  },

  // Nette samenvatting van een melding voor planner en demoscherm.
  meldingHtml(m) {
    const e = Omnia.esc;
    const foto = m.foto_url ? `<a href="${e(m.foto_url)}" target="_blank" rel="noopener"><img class="melding-foto" src="${e(m.foto_url)}" alt="Foto van de klant"></a>` : "";
    const kop = `<div class="melding-kop"><strong>${Omnia.tijd(m.rij.tijd)}</strong>`;
    if (m.ai) {
      const a = m.ai;
      const veld = (naam, waarde) => `<div><dt>${naam}</dt><dd class="${waarde ? "" : "leeg"}">${waarde ? e(waarde) : "niet te lezen"}</dd></div>`;
      return `<div class="melding">${foto}<div class="melding-inhoud">
        ${kop}<span class="badge ${a.spoed ? "badge-spoed" : "badge-rustig"}">${a.spoed ? "Spoed (voorstel)" : "Geen spoed"}</span></div>
        <dl class="velden">${veld("Merk", a.merk)}${veld("Type", a.type)}${veld("Foutcode", a.foutcode)}</dl>
        <p class="melding-klacht">${e(a.klacht || m.rij.tekst || "")}</p>
        <p class="melding-reden">${e(a.spoed_reden)}</p>
      </div></div>`;
    }
    if (m.fout) {
      return `<div class="melding">${foto}<div class="melding-inhoud">${kop}<span class="badge badge-spoed">AI niet gelukt</span></div>
        <p class="melding-klacht">“${e(m.rij.tekst)}”</p><p class="melding-reden">${e(m.fout.fout)} · Bel de klant zelf.</p></div></div>`;
    }
    return `<div class="melding">${foto}<div class="melding-inhoud">${kop}<span class="badge badge-bezig">AI leest uit…</span></div>
      <p class="melding-klacht">“${e(m.rij.tekst)}”</p></div></div>`;
  },
};
