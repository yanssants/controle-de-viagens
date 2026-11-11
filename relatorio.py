"""Relatório mensal em PDF (A4) gerado com fpdf2."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

from config import AJUDA_CUSTO_MENSAL, TIPOS
from formatos import agora, brl, data_br, data_hora_br, para_decimal, plural

# Cores do design system (RGB)
AZUL = (29, 78, 216)
AZUL_ANEL = (220, 230, 251)
TEXTO = (22, 24, 29)
TEXTO_2 = (58, 64, 76)
MUTED = (91, 98, 112)
BORDA = (227, 230, 235)
BORDA_INPUT = (201, 206, 214)
SUPERFICIE_MUTED = (241, 243, 246)
BRANCO = (255, 255, 255)

PASTA_FONTES = Path(__file__).with_name("fonts")


def _rgb(hexa: str) -> tuple[int, int, int]:
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i : i + 2], 16) for i in (0, 2, 4))


def resumo_por_tipo(viagens: list[dict]) -> dict[str, dict]:
    """{'curta': {'quantidade': 3, 'valor': Decimal('15.00')}, ...}"""
    resumo = {tipo: {"quantidade": 0, "valor": Decimal("0")} for tipo in TIPOS}
    for v in viagens:
        item = resumo.setdefault(v["tipo"], {"quantidade": 0, "valor": Decimal("0")})
        item["quantidade"] += 1
        item["valor"] += v["valor"]
    return resumo


class _PDF(FPDF):
    def __init__(self, gerado_em: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.gerado_em = gerado_em
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=18)
        self.fonte, self.unicode = self._registrar_fontes()

    def _registrar_fontes(self) -> tuple[str, bool]:
        """Usa Inter se os arquivos .ttf estiverem em ./fonts; senão, Helvetica."""
        regular = PASTA_FONTES / "Inter-Regular.ttf"
        negrito = PASTA_FONTES / "Inter-Bold.ttf"
        if regular.exists() and negrito.exists():
            self.add_font("Inter", "", str(regular))
            self.add_font("Inter", "B", str(negrito))
            return "Inter", True
        return "Helvetica", False

    def t(self, texto) -> str:
        """Fontes padrão do PDF só aceitam latin-1: troca caracteres fora dele."""
        texto = str(texto)
        if self.unicode:
            return texto
        texto = texto.replace("—", "-").replace("–", "-").replace("…", "...")
        return texto.encode("latin-1", "replace").decode("latin-1")

    def fonte_(self, tamanho: float, negrito: bool = False, cor=TEXTO) -> None:
        self.set_font(self.fonte, "B" if negrito else "", tamanho)
        self.set_text_color(*cor)

    @property
    def largura_util(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def garantir_espaco(self, altura: float) -> None:
        if self.get_y() + altura > self.page_break_trigger:
            self.add_page()

    def titulo_secao(self, texto: str) -> None:
        self.garantir_espaco(24)
        self.fonte_(11.5, True)
        self.cell(0, 7, self.t(texto), new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def footer(self) -> None:
        self.set_y(-12)
        self.fonte_(8, cor=MUTED)
        self.cell(0, 5, self.t(f"Gerado em {self.gerado_em}"), align="L")
        self.set_x(self.l_margin)
        self.cell(0, 5, self.t(f"Página {self.page_no()} de {{nb}}"), align="R")


def _cabecalho(pdf: _PDF, inicio: date, fim: date, nome_usuario: str, empresa: str) -> None:
    pdf.fonte_(20, True)
    pdf.cell(0, 10, pdf.t("Viagens a clientes"), new_x="LMARGIN", new_y="NEXT")
    pdf.fonte_(10, cor=TEXTO_2)
    pdf.cell(0, 6, pdf.t(f"Período: {data_br(inicio)} a {data_br(fim)}"), new_x="LMARGIN", new_y="NEXT")
    pdf.fonte_(10, cor=MUTED)
    pdf.cell(0, 6, pdf.t(f"{nome_usuario} · {empresa}"), new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 3
    pdf.set_draw_color(*AZUL)
    pdf.set_line_width(0.8)
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.set_line_width(0.2)
    pdf.set_y(y + 7)


def _cards_resumo(pdf: _PDF, viagens: list[dict]) -> Decimal:
    resumo = resumo_por_tipo(viagens)
    total = sum((item["valor"] for item in resumo.values()), Decimal("0"))

    espaco, altura = 4.0, 24.0
    largura = (pdf.largura_util - 3 * espaco) / 4
    pdf.garantir_espaco(altura + 4)
    y = pdf.get_y()

    for i, (tipo, info) in enumerate(TIPOS.items()):
        x = pdf.l_margin + i * (largura + espaco)
        item = resumo[tipo]
        pdf.set_fill_color(*BRANCO)
        pdf.set_draw_color(*BORDA)
        pdf.rect(x, y, largura, altura, style="DF", round_corners=True, corner_radius=2.5)
        pdf.set_xy(x + 4, y + 3.5)
        pdf.fonte_(8.5, cor=MUTED)
        pdf.cell(largura - 8, 4, pdf.t(info["plural"]))
        pdf.set_xy(x + 4, y + 9)
        pdf.fonte_(13, True, _rgb(info["cor"]))
        qtd = item["quantidade"]
        pdf.cell(largura - 8, 6, pdf.t(f"{qtd} {plural(qtd, 'viagem', 'viagens')}"))
        pdf.set_xy(x + 4, y + 16)
        pdf.fonte_(9.5, True, TEXTO_2)
        pdf.cell(largura - 8, 5, pdf.t(brl(item["valor"])))

    x = pdf.l_margin + 3 * (largura + espaco)
    pdf.set_fill_color(*AZUL)
    pdf.set_draw_color(*AZUL)
    pdf.rect(x, y, largura, altura, style="DF", round_corners=True, corner_radius=2.5)
    pdf.set_xy(x + 4, y + 3.5)
    pdf.fonte_(8.5, cor=AZUL_ANEL)
    pdf.cell(largura - 8, 4, pdf.t("Total das viagens"))
    pdf.set_xy(x + 4, y + 9)
    pdf.fonte_(13, True, BRANCO)
    pdf.cell(largura - 8, 6, pdf.t(brl(total)))
    pdf.set_xy(x + 4, y + 16)
    pdf.fonte_(9.5, cor=AZUL_ANEL)
    pdf.cell(largura - 8, 5, pdf.t(f"{len(viagens)} {plural(len(viagens), 'viagem', 'viagens')}"))

    pdf.set_y(y + altura + 8)
    return total


def _tabela(pdf: _PDF, cabecalhos, larguras, alinhamentos, linhas, rotulo_total, total) -> None:
    pdf.fonte_(9, cor=TEXTO)
    pdf.set_draw_color(*BORDA)
    pdf.set_fill_color(*BRANCO)
    pdf.set_line_width(0.2)
    estilo_cabecalho = FontFace(emphasis="BOLD", color=TEXTO_2, fill_color=SUPERFICIE_MUTED)
    estilo_total = FontFace(emphasis="BOLD", color=TEXTO, fill_color=SUPERFICIE_MUTED)
    estilo_valor_total = FontFace(emphasis="BOLD", color=AZUL, fill_color=SUPERFICIE_MUTED)

    with pdf.table(
        width=pdf.largura_util,
        col_widths=larguras,
        text_align=alinhamentos,
        line_height=5,
        padding=(2, 2),
        headings_style=estilo_cabecalho,
        borders_layout="HORIZONTAL_LINES",
    ) as tabela:
        linha = tabela.row()
        for cabecalho in cabecalhos:
            linha.cell(pdf.t(cabecalho))
        for dados in linhas:
            linha = tabela.row()
            for celula in dados:
                if isinstance(celula, tuple):  # (texto, FontFace)
                    linha.cell(pdf.t(celula[0]), style=celula[1])
                else:
                    linha.cell(pdf.t(celula))
        linha = tabela.row()
        linha.cell(pdf.t(rotulo_total), colspan=len(cabecalhos) - 1, align="RIGHT", style=estilo_total)
        linha.cell(pdf.t(brl(total)), align="RIGHT", style=estilo_valor_total)
    pdf.ln(8)


def _tabela_viagens(pdf: _PDF, viagens: list[dict], total: Decimal) -> None:
    pdf.titulo_secao("Detalhamento das viagens")
    if not viagens:
        pdf.fonte_(9.5, cor=MUTED)
        pdf.cell(0, 6, pdf.t("Nenhuma viagem registrada no período."), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return
    linhas = []
    for n, v in enumerate(sorted(viagens, key=lambda x: x["criado_em"]), start=1):
        info = TIPOS.get(v["tipo"], {"rotulo": v["tipo"], "cor": "#3A404C"})
        linhas.append(
            [
                str(n),
                data_hora_br(v["criado_em"]),
                v["saida"],
                v["destino"],
                (info["rotulo"], FontFace(emphasis="BOLD", color=_rgb(info["cor"]))),
                v["motivo"],
                brl(v["valor"]),
            ]
        )
    _tabela(
        pdf,
        ["#", "Data/hora", "Saída", "Destino", "Tipo", "Motivo", "Valor"],
        (8, 25, 27, 30, 21, 47, 22),
        ("LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "RIGHT"),
        linhas,
        "Valor total das viagens",
        total,
    )


def _tabela_implantacoes(pdf: _PDF, implantacoes: list[dict]) -> Decimal:
    total = sum((i["comissao"] for i in implantacoes), Decimal("0"))
    pdf.titulo_secao("Implantações realizadas")
    if not implantacoes:
        pdf.fonte_(9.5, cor=MUTED)
        pdf.cell(0, 6, pdf.t("Nenhuma implantação registrada no período."), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return total
    ordenadas = sorted(implantacoes, key=lambda x: (x["data_implantacao"], x["id"]))
    linhas = [
        [str(n), data_br(i["data_implantacao"]), i["cliente"], i["sistema"], brl(i["comissao"])]
        for n, i in enumerate(ordenadas, start=1)
    ]
    _tabela(
        pdf,
        ["#", "Data da implantação", "Cliente", "Sistema", "Comissão"],
        (8, 32, 55, 57, 28),
        ("LEFT", "LEFT", "LEFT", "LEFT", "RIGHT"),
        linhas,
        "Valor total das implantações",
        total,
    )
    return total


def _bloco_totais(pdf: _PDF, total_viagens: Decimal, total_implantacoes: Decimal) -> None:
    total_geral = total_viagens + total_implantacoes + AJUDA_CUSTO_MENSAL
    largura = 100.0
    altura_linha = 8.0
    pdf.garantir_espaco(altura_linha * 4 + 20)
    pdf.titulo_secao("Totais do mês")
    x = pdf.w - pdf.r_margin - largura
    y = pdf.get_y()

    pdf.set_fill_color(*BRANCO)
    pdf.set_draw_color(*BORDA)
    pdf.rect(x, y, largura, altura_linha * 3 + 4, style="DF", round_corners=True, corner_radius=2.5)
    pdf.set_y(y + 2)
    for rotulo, valor in (
        ("Viagens", total_viagens),
        ("Implantações", total_implantacoes),
        ("Ajuda de custo fixa mensal", AJUDA_CUSTO_MENSAL),
    ):
        pdf.set_x(x + 5)
        pdf.fonte_(10, cor=TEXTO_2)
        pdf.cell(largura - 45, altura_linha, pdf.t(rotulo))
        pdf.fonte_(10, True, TEXTO)
        pdf.cell(35, altura_linha, pdf.t(brl(valor)), align="R", new_x="LMARGIN", new_y="NEXT")

    y_total = y + altura_linha * 3 + 7
    pdf.set_fill_color(*AZUL)
    pdf.set_draw_color(*AZUL)
    pdf.rect(x, y_total, largura, 13, style="DF", round_corners=True, corner_radius=2.5)
    pdf.set_xy(x + 5, y_total + 2.5)
    pdf.fonte_(11, True, BRANCO)
    pdf.cell(largura - 45, 8, pdf.t("Total a receber no mês"))
    pdf.fonte_(13, True, BRANCO)
    pdf.cell(35, 8, pdf.t(brl(total_geral)), align="R")
    pdf.set_y(y_total + 18)


def gerar_relatorio_pdf(
    inicio: date,
    fim: date,
    viagens: list[dict],
    implantacoes: list[dict],
    nome_usuario: str,
    empresa: str,
) -> bytes:
    pdf = _PDF(gerado_em=data_hora_br(agora(), " às "))
    pdf.set_title("Viagens a clientes")
    pdf.set_author(pdf.t(nome_usuario))
    pdf.add_page()

    _cabecalho(pdf, inicio, fim, nome_usuario, empresa)
    pdf.titulo_secao("Resumo por tipo de viagem")
    total_viagens = _cards_resumo(pdf, viagens)
    _tabela_viagens(pdf, viagens, total_viagens)
    total_implantacoes = _tabela_implantacoes(pdf, implantacoes)
    _bloco_totais(pdf, para_decimal(total_viagens), para_decimal(total_implantacoes))

    return bytes(pdf.output())
