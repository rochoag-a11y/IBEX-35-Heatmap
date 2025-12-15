// Carga de datos y treemap estilo FINVIZ
(async function () {
  const container = document.getElementById('treemap');
  const W = container.clientWidth, H = container.clientHeight;

  // Cargar datos (generados a diario por GitHub Actions)
  const data = await fetch('data/ibex35.json', { cache: 'no-store' }).then(r => r.json());

  // D3 treemap
  const root = d3.hierarchy({children: data})
    .sum(d => d.size)               // tamaño del rectángulo = capitalización/peso
    .sort((a,b) => b.value - a.value);

  d3.treemap()
    .size([W, H])
    .padding(2)
    .round(true)
    (root);

  // Color por variación diaria (%)
  const color = d => {
    const ch = d.data.change;
    // verde→positivo | rojo→negativo | gris→casi plano
    if (ch > 0.15) {
      const t = Math.min(ch/5, 1);
      return `rgb(${20},${Math.round(140+115*t)},${60})`;
    } else if (ch < -0.15) {
      const t = Math.min(Math.abs(ch)/5, 1);
      return `rgb(${Math.round(180+60*t)},${60},${60})`;
    } else {
      return `rgb(140,140,140)`;
    }
  };

  // Render tiles
  for (const node of root.leaves()) {
    const el = document.createElement('div');
    el.className = 'tile';
    el.style.left = `${node.x0}px`;
    el.style.top = `${node.y0}px`;
    el.style.width = `${node.x1 - node.x0}px`;
    el.style.height = `${node.y1 - node.y0}px`;
    el.style.background = color(node);

    // Etiqueta: ticker y variación
    const label = document.createElement('div');
    label.className = 'label';
    const tick = node.data.ticker || node.data.symbol || node.data.name;
    label.innerHTML = `${tick}<small>${node.data.change > 0 ? '+' : ''}${node.data.change.toFixed(2)}%</small>`;
    el.appendChild(label);

    container.appendChild(el);
  }

  // Mini-leyenda
  const legend = document.createElement('div');
  legend.className = 'legend';
  const pos = document.createElement('span'); pos.style.background = 'rgb(20,255,60)';
  const flat = document.createElement('span'); flat.style.background = 'rgb(140,140,140)';
  const neg = document.createElement('span'); neg.style.background = 'rgb(255,60,60)';
  legend.append(pos, flat, neg);
  container.appendChild(legend);
