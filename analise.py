"""Projeto M13 — execute a partir da pasta do projeto: python analise.py."""
import matplotlib
matplotlib.use("Agg")

# Célula 1
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from visualizacoes import br, boxplot_precos, barras_desconto, treemap_desconto

# No Jupyter, display renderiza as tabelas. No script, o fallback imprime os dados.
try:
    from IPython.display import display
except ImportError:
    if "display" not in globals():
        def display(objeto):
            print(objeto.to_string() if isinstance(objeto, pd.DataFrame) else objeto)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", 70)
pd.set_option("display.float_format", br)
GRAFICOS = Path("graficos")
RESULTADOS = Path("resultados")
GRAFICOS.mkdir(exist_ok=True)
RESULTADOS.mkdir(exist_ok=True)

# Célula 2
arquivo = Path("MODULO7_PROJETOFINAL_BASE_SUPERMERCADO.csv")
if not arquivo.exists():
    candidatos = sorted(Path(".").glob("*SUPERMERCADO*.csv*"))
    if len(candidatos) != 1:
        raise FileNotFoundError("Coloque o CSV do supermercado na pasta do notebook.")
    arquivo = candidatos[0]

df = pd.read_csv(arquivo, sep=",", encoding="utf-8")
colunas_esperadas = {"title", "Marca", "Preco_Normal", "Preco_Desconto", "Preco_Anterior", "Desconto", "Categoria"}
if not colunas_esperadas.issubset(df.columns):
    raise ValueError("O CSV não contém as colunas esperadas; confira o delimitador.")
colunas_numericas = ["Preco_Normal", "Preco_Desconto", "Preco_Anterior", "Desconto"]
df[colunas_numericas] = df[colunas_numericas].apply(pd.to_numeric, errors="raise")
print(f"Base carregada: {len(df)} registros, {df.shape[1]} colunas e {df['Categoria'].nunique()} categorias.")
display(df.head(10))

# Célula 3
verificacao = pd.DataFrame({
    "verificacao": ["Registros", "Categorias", "Marcas", "Células ausentes", "Duplicatas além da primeira",
                    "Preço normal zero", "Desconto zero", "Desconto positivo"],
    "quantidade": [len(df), df["Categoria"].nunique(), df["Marca"].nunique(), int(df.isna().sum().sum()),
                   int(df.duplicated().sum()), int(df["Preco_Normal"].eq(0).sum()),
                   int(df["Desconto"].eq(0).sum()), int(df["Desconto"].gt(0).sum())]
})
display(verificacao)

# Célula 4
medias = df.groupby("Categoria")["Preco_Normal"].mean().sort_values(ascending=False)
display(medias.to_frame("media_preco_normal"))

# Célula 5
medianas = df.groupby("Categoria")["Preco_Normal"].median()
resumo = pd.concat([medias.rename("media"), medianas.rename("mediana")], axis=1)
resumo["media_menos_mediana"] = resumo["media"] - resumo["mediana"]
resumo["comparacao"] = np.select(
    [resumo["media"] > resumo["mediana"], resumo["media"] < resumo["mediana"]],
    ["Média acima da mediana", "Média abaixo da mediana"],
    default="Média igual à mediana",
)
display(resumo)

# Célula 6
desvios = df.groupby("Categoria")["Preco_Normal"].std(ddof=1).rename("desvio_padrao")
estatisticas = resumo.join(desvios)
estatisticas["quantidade"] = df.groupby("Categoria").size()
estatisticas = estatisticas.sort_values("desvio_padrao", ascending=False)
categoria_maior_desvio = estatisticas["desvio_padrao"].idxmax()
display(estatisticas[["quantidade", "media", "mediana", "desvio_padrao", "comparacao"]])
print(f"Maior desvio padrão: {categoria_maior_desvio} = {br(desvios.max())}.")
estatisticas.to_csv(RESULTADOS / "estatisticas_por_categoria.csv", encoding="utf-8-sig")

# Célula 7
precos_categoria = df.loc[df["Categoria"].eq(categoria_maior_desvio), "Preco_Normal"]
fig_boxplot = boxplot_precos(
    precos_categoria, categoria_maior_desvio, GRAFICOS / "01_boxplot_lacteos.png"
)
plt.show()

# Célula 8
q1, q3 = precos_categoria.quantile([0.25, 0.75])
iqr = q3 - q1
limite_inferior = q1 - 1.5 * iqr
limite_superior = q3 + 1.5 * iqr
mascara_outlier = (df["Categoria"].eq(categoria_maior_desvio) &
                  ((df["Preco_Normal"] < limite_inferior) | (df["Preco_Normal"] > limite_superior)))
outliers = df.loc[mascara_outlier, ["title", "Marca", "Categoria", "Preco_Normal"]].copy()
outliers.insert(0, "registro_base", outliers.index + 1)
outliers = outliers.sort_values("Preco_Normal", ascending=False, kind="stable")
dentro = precos_categoria.between(limite_inferior, limite_superior)
limites = pd.DataFrame({"medida": ["Q1", "Mediana", "Q3", "IQR", "Limite inferior", "Limite superior",
                                        "Bigode inferior", "Bigode superior"],
                        "valor": [q1, precos_categoria.median(), q3, iqr, limite_inferior, limite_superior,
                                  precos_categoria[dentro].min(), precos_categoria[dentro].max()]})
display(limites)
print(f"Outliers: {len(outliers)} de {len(precos_categoria)} registros ({br(100*len(outliers)/len(precos_categoria))}%).")
with pd.option_context("display.max_rows", None):
    display(outliers.reset_index(drop=True))
outliers.to_csv(RESULTADOS / "outliers_lacteos.csv", index=False, encoding="utf-8-sig")

# Célula 9
descontos_categoria = df.groupby("Categoria").agg(
    quantidade=("Desconto", "size"),
    desconto_medio=("Desconto", "mean"),
    com_desconto=("Desconto", lambda valores: int(valores.gt(0).sum())),
).sort_values("desconto_medio", ascending=False)
display(descontos_categoria)
fig_barras = barras_desconto(descontos_categoria, GRAFICOS / "02_desconto_por_categoria.png")
plt.show()
descontos_categoria.to_csv(RESULTADOS / "desconto_por_categoria.csv", encoding="utf-8-sig")

# Célula 10
descontos_marca = df.groupby(["Categoria", "Marca"], as_index=False).agg(
    quantidade=("Desconto", "size"),
    desconto_medio=("Desconto", "mean"),
    com_desconto=("Desconto", lambda valores: int(valores.gt(0).sum())),
)
display(descontos_marca.sort_values("desconto_medio", ascending=False).head(10))
fig_mapa = treemap_desconto(
    descontos_marca, descontos_categoria,
    GRAFICOS / "03_mapa_categoria_marca.png",
    GRAFICOS / "03_mapa_interativo.html",
)
plt.show()
descontos_marca.to_csv(RESULTADOS / "desconto_por_categoria_marca.csv", index=False, encoding="utf-8-sig")
print("Mapa interativo salvo em graficos/03_mapa_interativo.html. Abra esse arquivo no navegador.")
# No Jupyter, a célula abaixo incorpora o mesmo HTML; o arquivo funciona também offline.
try:
    from IPython.display import IFrame
    display(IFrame(src="graficos/03_mapa_interativo.html", width="100%", height=1050))
except ImportError:
    pass

# Célula 11
sensibilidade = df.loc[df["Preco_Normal"].gt(0)].groupby("Categoria")["Preco_Normal"].agg(
    quantidade="size", media="mean", mediana="median", desvio_padrao="std"
).sort_values("desvio_padrao", ascending=False)
sensibilidade["comparacao"] = np.where(sensibilidade["media"] > sensibilidade["mediana"],
                                     "Média acima da mediana", "Média abaixo ou igual à mediana")
display(sensibilidade)
sensibilidade.to_csv(RESULTADOS / "sensibilidade_preco_normal_positivo.csv", encoding="utf-8-sig")
