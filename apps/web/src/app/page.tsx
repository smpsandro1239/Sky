import Link from "next/link";

const destinations = [
  { name: "Lisboa", country: "Portugal", detail: "Cultura, gastronomia e escapadinhas" },
  { name: "Madeira", country: "Portugal", detail: "Natureza, mar e montanha" },
  { name: "Roma", country: "Itália", detail: "História em cada rua" },
];

export default function HomePage() {
  return (
    <main>
      <header className="topbar">
        <Link className="brand" href="/">SKY<span>.</span></Link>
        <span className="tagline">A tua próxima viagem começa aqui</span>
      </header>
      <section className="hero">
        <p className="eyebrow">DESCOBRE · COMPARA · VIAJA</p>
        <h1>O mundo é teu.<br /><span>Encontra o teu próximo destino.</span></h1>
        <p className="intro">Uma nova forma de descobrir destinos, organizar ideias e preparar viagens — tudo num só lugar.</p>
        <div className="search-panel">
          <div className="fields">
            {["Destino", "Partida", "Datas"].map((label, index) => (
              <label key={label}>{label}<input disabled placeholder={["Para onde queres ir?", "De onde partes?", "Quando queres viajar?"][index]} /></label>
            ))}
          </div>
          <p className="notice">A pesquisa de viagens está em desenvolvimento. Os campos serão ativados após a integração da API e dos fornecedores.</p>
        </div>
        <section className="destinations">
          <p className="eyebrow">INSPIRAÇÃO PARA COMEÇAR</p>
          <h2>Destinos em destaque</h2>
          <div className="cards">
            {destinations.map((destination) => (
              <article className="destination" key={destination.name}>
                <h3>{destination.name}</h3>
                <p>{destination.country} · {destination.detail}</p>
              </article>
            ))}
          </div>
        </section>
      </section>
      <footer>SKY Travel Platform · Fundação técnica em desenvolvimento · 2026</footer>
    </main>
  );
}
