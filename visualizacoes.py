"""Gráficos do projeto M13: Matplotlib e um treemap HTML sem dependências web."""
from pathlib import Path
import html
import json
import textwrap

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors, patches
from matplotlib.ticker import FuncFormatter
import numpy as np


ROTULOS = {
    "belleza-y-cuidado-personal": "Beleza e cuidado pessoal",
    "comidas-preparadas": "Comidas preparadas",
    "congelados": "Congelados",
    "frutas": "Frutas",
    "instantaneos-y-sopas": "Instantâneos e sopas",
    "lacteos": "Lácteos",
    "verduras": "Verduras",
}
NAVY = "#142B45"
TEAL = "#087F8C"
RED = "#C7553C"
GRAY = "#53677B"
BG = "#F6F8FB"


def br(valor, casas=2):
    """Número com separadores brasileiros, sem alterar o valor usado no cálculo."""
    return f"{valor:,.{casas}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def configurar():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.edgecolor": "#D1DAE4",
        "axes.labelcolor": GRAY, "xtick.color": GRAY, "ytick.color": NAVY,
        "text.color": NAVY, "figure.facecolor": BG, "axes.facecolor": BG,
        "savefig.facecolor": BG,
    })


def boxplot_precos(precos, categoria, destino):
    """Boxplot de Tukey; os 43 pontos são deslocados apenas no eixo vertical."""
    configurar()
    q1, q3 = precos.quantile([0.25, 0.75])
    mediana, media = precos.median(), precos.mean()
    iqr = q3 - q1
    li, ls = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    atipicos = precos[(precos < li) | (precos > ls)]
    fig = plt.figure(figsize=(14, 8), dpi=150)
    fig.text(.065, .942, "M13  /  DISTRIBUIÇÃO DOS PREÇOS", fontsize=10, weight="bold", color=TEAL)
    fig.text(.065, .885, f"{ROTULOS[categoria]}: {len(atipicos)} registros classificados como outliers",
             fontsize=23, weight="bold")
    fig.text(.065, .837, f"{len(precos)} registros · Preco_Normal original, incluindo {(precos == 0).sum()} zeros · critério: 1,5 × IQR",
             fontsize=12, color=GRAY)
    ax = fig.add_axes([.09, .32, .84, .42])
    ax.boxplot(precos, vert=False, positions=[0], widths=.35,
               patch_artist=True, showfliers=False, whis=1.5,
               boxprops={"facecolor": "#C0E3E5", "edgecolor": TEAL, "linewidth": 1.8},
               medianprops={"color": NAVY, "linewidth": 2.6},
               whiskerprops={"color": TEAL, "linewidth": 1.7},
               capprops={"color": TEAL, "linewidth": 1.7})
    # O deslocamento determinístico separa preços repetidos sem mudar o eixo de preços.
    deslocamento = np.random.default_rng(13).uniform(-.24, .24, len(atipicos))
    ax.scatter(atipicos, deslocamento, s=33, color=RED, edgecolors="white", linewidths=.6,
               zorder=4, label="Outliers (um ponto por registro)")
    ax.scatter([media], [0], marker="D", s=64, color=NAVY, edgecolors="white",
               zorder=5, label="Média")
    ax.axvline(ls, color=RED, ls="--", linewidth=1.3, alpha=.75)
    ax.text(ls + 260, .49, f"Limite superior\n{br(ls, 0)}", color=RED, fontsize=11, va="top")
    ax.set_ylim(-.65, .65)
    ax.set_xlim(-500, precos.max() * 1.055)
    ax.set_yticks([])
    ax.set_xticks(np.arange(0, 20001, 2500))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v, 0)))
    ax.set_xlabel("Preço normal · unidade monetária original da base", labelpad=13)
    ax.grid(axis="x", color="#DFE5EC", linewidth=.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, fontsize=10)
    fig.text(.09, .207, f"Média  {br(media)}", fontsize=15, weight="bold")
    fig.text(.39, .207, f"Mediana  {br(mediana)}", fontsize=15, weight="bold")
    fig.text(.70, .207, f"Outliers  {br(len(atipicos)/len(precos)*100)}%", fontsize=15, weight="bold")
    fig.text(.09, .148, f"Q1 = {br(q1, 0)}  ·  Q3 = {br(q3, 0)}  ·  IQR = {br(iqr, 0)}  ·  bigode superior = {br(precos[precos <= ls].max(), 0)}",
             fontsize=11, color=GRAY)
    fig.text(.065, .065, "Preços altos alongam a cauda à direita. Packs e leites em pó aparecem entre os outliers;\n"
             "ser um outlier estatístico não significa ser um erro. Pontos separados verticalmente para mostrar repetições.",
             fontsize=10, color=GRAY, linespacing=1.5)
    fig.savefig(destino, dpi=180)
    return fig


def barras_desconto(tabela, destino):
    configurar()
    tabela = tabela.sort_values("desconto_medio", ascending=False, kind="stable")
    fig = plt.figure(figsize=(14, 8), dpi=150)
    fig.text(.065, .942, "M13  /  COMPARAÇÃO ENTRE CATEGORIAS", fontsize=10, weight="bold", color=TEAL)
    fig.text(.065, .885, "Congelados tem o maior desconto médio", fontsize=26, weight="bold")
    fig.text(.065, .837, "Média simples da coluna Desconto, incluindo os valores zero de cada categoria", fontsize=12, color=GRAY)
    ax = fig.add_axes([.265, .20, .61, .565])
    y = np.arange(len(tabela))
    valores = tabela.desconto_medio.to_numpy()
    ax.barh(y, valores, height=.58, color=[TEAL] + ["#92B9C4"] * (len(tabela)-1))
    ax.set_yticks(y, [ROTULOS[c] for c in tabela.index], fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, max(valores) * 1.25)
    ax.set_xticks([0, 40, 80, 120, 160])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v, 0)))
    ax.tick_params(axis="y", length=0, pad=12)
    for i, (valor, quantidade) in enumerate(zip(valores, tabela.quantidade)):
        if valor == 0:
            ax.scatter(0, i, color="#92B9C4", s=24, clip_on=False)
        ax.text(valor + 2.8, i, br(valor), va="center", fontsize=12, weight="bold")
        ax.text(ax.get_xlim()[1] + 5, i, f"n = {quantidade}", va="center", fontsize=10, color=GRAY)
    ax.set_xlabel("Desconto médio · unidade monetária original da base", labelpad=14)
    ax.grid(axis="x", color="#DFE5EC", linewidth=.8)
    ax.set_axisbelow(True)
    fig.text(.065, .078, "Desconto é um valor monetário absoluto, não uma porcentagem. n = quantidade de registros.\n"
             "Zero na coluna Desconto indica ausência de desconto registrado; não comprova ausência de qualquer promoção.",
             fontsize=10, color=GRAY, linespacing=1.5)
    fig.savefig(destino, dpi=180)
    return fig


def dividir_retangulos(itens, x, y, largura, altura):
    """Treemap binário: cada área é proporcional a quantidade, sem somar médias."""
    if len(itens) == 1:
        return [{**itens[0], "x": x, "y": y, "w": largura, "h": altura}]
    total = sum(i["quantidade"] for i in itens)
    acumulado = np.cumsum([i["quantidade"] for i in itens])[:-1]
    corte = int(np.argmin(np.abs(acumulado - total / 2))) + 1
    proporcao = sum(i["quantidade"] for i in itens[:corte]) / total
    if largura >= altura:
        a = dividir_retangulos(itens[:corte], x, y, largura * proporcao, altura)
        b = dividir_retangulos(itens[corte:], x + largura * proporcao, y, largura * (1-proporcao), altura)
    else:
        a = dividir_retangulos(itens[:corte], x, y, largura, altura * proporcao)
        b = dividir_retangulos(itens[corte:], x, y + altura * proporcao, largura, altura * (1-proporcao))
    return a + b


def _folhas(tabela, x, y, largura, altura, vmax):
    itens = tabela.sort_values(["quantidade", "Marca"], ascending=[False, True]).to_dict("records")
    folhas = dividir_retangulos(itens, x, y, largura, altura)
    cmap = plt.get_cmap("YlGnBu")
    for folha in folhas:
        rgba = cmap(folha["desconto_medio"] / vmax if vmax else 0)
        folha["cor"] = colors.to_hex(rgba)
        folha["cor_texto"] = "#142B45" if folha["desconto_medio"] < vmax*.53 else "#FFFFFF"
    return folhas


def montar_cenas(mapa, categorias):
    """A mesma geometria alimenta a imagem estática e o HTML interativo."""
    largura, altura = 1440, 830
    vmax = float(mapa.desconto_medio.max())
    pais = categorias.reset_index().sort_values("quantidade", ascending=False).to_dict("records")
    pais = dividir_retangulos(pais, 0, 0, largura, altura)
    visao = []
    for p in pais:
        titulo = ROTULOS[p["Categoria"]]
        cabecalho = 50 if p["w"] < 230 else 39
        folhas = _folhas(mapa[mapa.Categoria.eq(p["Categoria"])], p["x"]+5, p["y"]+cabecalho,
                         p["w"]-10, p["h"]-cabecalho-5, vmax)
        visao.append({**p, "titulo": titulo, "cabecalho": cabecalho, "folhas": folhas})
    cenas = {"Todas": visao}
    for p in pais:
        cenas[p["Categoria"]] = [{**p, "x": 0, "y": 0, "w": largura, "h": altura,
                                 "titulo": ROTULOS[p["Categoria"]], "cabecalho": 39,
                                 "folhas": _folhas(mapa[mapa.Categoria.eq(p["Categoria"])],
                                                   5, 39, largura-10, altura-44, vmax)}]
    return cenas, vmax


def _linhas_marca(folha):
    if folha["w"] < 52 or folha["h"] < 35:
        return []
    capacidade = max(7, int(folha["w"] / 8))
    linhas = textwrap.wrap(folha["Marca"], width=capacidade,
                          break_long_words=False, break_on_hyphens=False)
    # Nomes longos ficam no detalhe interativo, evitando palavras cortadas no PNG.
    if any(len(linha) > capacidade for linha in linhas) or len(linhas) > 2:
        return []
    if folha["h"] > 65 and folha["w"] > 85:
        linhas.append(br(folha["desconto_medio"]))
    return linhas


def _svg(cena):
    partes = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 830" role="img" aria-label="Mapa de categorias e marcas">']
    for p in cena:
        x,y,w,h = [p[k] for k in ("x","y","w","h")]
        partes.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="3" fill="#E3EBF2" stroke="white" stroke-width="3"/>')
        titulo = textwrap.wrap(p["titulo"], width=max(12, int(w/8.8)))
        for j, linha in enumerate(titulo[:2]):
            partes.append(f'<text x="{x+10:.3f}" y="{y+21+17*j:.3f}" fill="{NAVY}" font-size="15" font-weight="700">{html.escape(linha)}</text>')
        for f in p["folhas"]:
            dica = (f'{p["titulo"]} ({p["Categoria"]}) | {f["Marca"]} | '
                    f'Desconto médio: {br(f["desconto_medio"])} | Registros: {f["quantidade"]} | '
                    f'Com desconto registrado: {f["com_desconto"]}')
            dados = html.escape(json.dumps({"categoria":p["titulo"], "marca":f["Marca"],
                     "media":br(f["desconto_medio"]), "n":f["quantidade"], "ofertas":f["com_desconto"]}, ensure_ascii=False), quote=True)
            partes.append(f'<g class="marca" tabindex="0" data-info="{dados}" aria-label="{html.escape(dica, quote=True)}">')
            partes.append(f'<title>{html.escape(dica)}</title>')
            partes.append(f'<rect x="{f["x"]:.3f}" y="{f["y"]:.3f}" width="{f["w"]:.3f}" height="{f["h"]:.3f}" fill="{f["cor"]}" stroke="white" stroke-width="1.4"/>')
            linhas = _linhas_marca(f)
            for j, linha in enumerate(linhas):
                ty = f["y"]+f["h"]/2 + (j-(len(linhas)-1)/2)*16 + 4
                partes.append(f'<text pointer-events="none" x="{f["x"]+f["w"]/2:.3f}" y="{ty:.3f}" text-anchor="middle" fill="{f["cor_texto"]}" font-size="13">{html.escape(linha)}</text>')
            partes.append('</g>')
    partes.append('</svg>')
    return ''.join(partes)


def treemap_desconto(mapa, categorias, destino_png, destino_html):
    configurar()
    cenas, vmax = montar_cenas(mapa, categorias)
    fig = plt.figure(figsize=(16, 11), dpi=150)
    fig.text(.05,.952,"M13  /  CATEGORIA → MARCA",fontsize=10,weight="bold",color=TEAL)
    fig.text(.05,.91,"Desconto médio por categoria e marca",fontsize=27,weight="bold")
    fig.text(.05,.873,"Área = quantidade de registros  ·  Cor = desconto médio do grupo  ·  Valores zero incluídos",fontsize=12,color=GRAY)
    ax = fig.add_axes([.05,.145,.90,.665])
    ax.set_xlim(0,1440); ax.set_ylim(830,0); ax.axis("off")
    for p in cenas["Todas"]:
        ax.add_patch(patches.Rectangle((p["x"],p["y"]),p["w"],p["h"],facecolor="#E3EBF2",edgecolor="white",linewidth=2))
        titulo = textwrap.wrap(p["titulo"], width=max(12,int(p["w"]/8.8)))
        for j, linha in enumerate(titulo[:2]):
            ax.text(p["x"]+10,p["y"]+22+j*17,linha,fontsize=10.5,weight="bold")
        for f in p["folhas"]:
            ax.add_patch(patches.Rectangle((f["x"],f["y"]),f["w"],f["h"],facecolor=f["cor"],edgecolor="white",linewidth=.7))
            linhas = _linhas_marca(f)
            for j, linha in enumerate(linhas):
                ty=f["y"]+f["h"]/2+(j-(len(linhas)-1)/2)*16
                ax.text(f["x"]+f["w"]/2,ty,linha,ha="center",va="center",fontsize=8.4,color=f["cor_texto"],clip_on=True)
    cax = fig.add_axes([.655,.829,.27,.016])
    sm=plt.cm.ScalarMappable(norm=colors.Normalize(0,vmax),cmap="YlGnBu")
    cb=fig.colorbar(sm,cax=cax,orientation="horizontal",ticks=[0,250,500,750,vmax])
    cb.outline.set_visible(False); cb.ax.tick_params(labelsize=9)
    cb.ax.xaxis.set_major_formatter(FuncFormatter(lambda v,_:br(v,0)))
    fig.text(.05,.832,f"{int(categorias.quantidade.sum()):,} registros  ·  {len(categorias)} categorias  ·  {len(mapa)} combinações".replace(",","."),fontsize=11,color=GRAY)
    fig.text(.05,.083,"O tamanho representa registros da base, não volume de vendas. As médias não são somadas.\n"
             "Na versão HTML, passe o mouse ou toque nas marcas e filtre uma categoria para ampliar os detalhes.\n"
             "Unidade monetária original da base; rótulos pequenos foram omitidos apenas na visão geral.",fontsize=10,color=GRAY,linespacing=1.5)
    fig.savefig(destino_png,dpi=180)
    opcoes=''.join(f'<option value="{html.escape(k,quote=True)}">{html.escape("Todas as categorias" if k=="Todas" else ROTULOS[k])}</option>' for k in cenas)
    secoes=''.join(f'<section data-cena="{html.escape(k,quote=True)}" {"" if k=="Todas" else "hidden"}>{_svg(v)}</section>' for k,v in cenas.items())
    documento='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>M13 — Mapa de descontos</title>
<style>*{box-sizing:border-box}body{margin:0;background:#F6F8FB;color:#142B45;font:16px system-ui,Arial,sans-serif}main{max-width:1550px;margin:auto;padding:30px 32px 22px}h1{font-size:32px;margin:8px 0 10px}p{color:#53677B;margin:10px 0;line-height:1.5}.eyebrow{color:#087F8C;font-size:12px;font-weight:750;letter-spacing:1px}.controls{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:22px 0 10px}select,button{font:inherit;padding:9px 12px;border:1px solid #BFCBD7;border-radius:6px;background:white;color:#142B45;cursor:pointer}.legend{margin-left:auto;min-width:280px}.gradient{height:12px;background:linear-gradient(to right,#FFFFD9,#C7E9B4,#41B6C4,#225EA8,#081D58);border-radius:3px}.scale{display:flex;justify-content:space-between;font-size:12px;color:#53677B;margin-top:5px}svg{width:100%;height:auto;display:block}.marca{cursor:pointer;outline:none}.marca:hover rect,.marca:focus rect{stroke:#C7553C;stroke-width:3}.detail{background:white;border:1px solid #D8E1E9;padding:14px 16px;border-radius:8px;min-height:55px;margin:12px 0}.note{font-size:13px}section[hidden]{display:none}@media(max-width:700px){main{padding:18px 12px}h1{font-size:25px}.legend{margin-left:0;width:100%}}</style></head><body><main>
<div class="eyebrow">PROJETO M13 / FUNDAMENTOS DA DESCOBERTA DE DADOS</div><h1>Desconto médio por categoria e marca</h1>
<p>Área = quantidade de registros · Cor = desconto médio do grupo · Valores zero incluídos</p>
<div class="controls"><label for="categoria">Categoria:</label><select id="categoria">__OPCOES__</select><button id="reset">Ver todas</button><div class="legend"><div class="gradient"></div><div class="scale"><span>0</span><span>Desconto médio</span><span>__MAX__</span></div></div></div>
<div id="detalhe" class="detail" aria-live="polite">Passe o mouse, toque ou use Tab sobre uma marca para ver a média e a quantidade de registros.</div>
__SECOES__
<p class="note">__N__ registros · 7 categorias · 156 marcas · 167 combinações de categoria e marca. Unidade monetária original da base; desconto não é porcentagem. O número de registros não representa volume de vendas.</p>
<p class="note">As médias incluem todos os registros de cada grupo, inclusive Desconto = 0. Grupos pequenos podem apresentar médias altas com poucos registros. Os zeros permanecem visíveis, pois a área usa a contagem, não o desconto.</p></main>
<script>
const seletor=document.getElementById('categoria'), detalhe=document.getElementById('detalhe');
function mudarCategoria(){document.querySelectorAll('[data-cena]').forEach(s=>{s.hidden=s.dataset.cena!==seletor.value});detalhe.textContent='Passe o mouse, toque ou use Tab sobre uma marca para ver a média e a quantidade de registros.';}
seletor.addEventListener('change',mudarCategoria);
document.getElementById('reset').addEventListener('click',()=>{seletor.value='Todas';mudarCategoria();});
document.querySelectorAll('.marca').forEach(g=>{function mostrar(){const d=JSON.parse(g.dataset.info);detalhe.textContent=d.categoria+' → '+d.marca+' | Desconto médio: '+d.media+' | Registros: '+d.n+' | Com desconto registrado: '+d.ofertas;}g.addEventListener('mouseenter',mostrar);g.addEventListener('focus',mostrar);g.addEventListener('click',mostrar);});
</script></body></html>'''
    documento=documento.replace('__OPCOES__',opcoes).replace('__SECOES__',secoes).replace('__MAX__',br(vmax,0)).replace('__N__',br(categorias.quantidade.sum(),0))
    Path(destino_html).write_text(documento,encoding="utf-8")
    return fig
