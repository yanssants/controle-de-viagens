"""Partes usadas pelas duas telas: pop-up do relatório em PDF e campos de período."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

import db
import ui
from config import AJUDA_CUSTO_MENSAL, EMPRESA_PADRAO, NOME_USUARIO_PADRAO
from formatos import brl, data_br
from relatorio import gerar_relatorio_pdf

DATA_MIN = date(2000, 1, 1)
DATA_MAX = date(2100, 12, 31)


def _segredo(chave: str, padrao: str) -> str:
    try:
        return str(st.secrets.get(chave) or padrao)
    except Exception:
        return padrao


def periodo_valido(inicio: date | None, fim: date | None) -> bool:
    return bool(inicio and fim and inicio <= fim)


@st.dialog("Relatório em PDF")
def dialogo_relatorio(inicio: date, fim: date) -> None:
    if not periodo_valido(inicio, fim):
        st.error("Escolha um período válido: a data inicial deve ser anterior ou igual à final.")
        return
    ui.subtitulo_dialogo(f"Período de {data_br(inicio)} a {data_br(fim)}")
    try:
        viagens = db.listar_viagens(inicio, fim)
        implantacoes = db.listar_implantacoes(inicio, fim)
    except db.ErroBanco as erro:
        st.error(str(erro))
        return

    total_viagens = sum((v["valor"] for v in viagens), Decimal("0"))
    total_impl = sum((i["comissao"] for i in implantacoes), Decimal("0"))
    total = total_viagens + total_impl + AJUDA_CUSTO_MENSAL
    linhas = [
        (f"Viagens ({len(viagens)})", brl(total_viagens)),
        (f"Implantações ({len(implantacoes)})", brl(total_impl)),
        ("Ajuda de custo fixa mensal", brl(AJUDA_CUSTO_MENSAL)),
    ]
    corpo = "".join(
        f'<div class="cv-card-linha"><span>{ui.esc(r)}</span><span class="cv-pontos"></span>'
        f"<strong>{ui.esc(v)}</strong></div>"
        for r, v in linhas
    )
    ui.html_(
        f'<div class="cv-card-menu cv-resumo-relatorio">{corpo}'
        f'<div class="cv-card-linha cv-total-receber"><span>Total a receber no mês</span>'
        f'<span class="cv-pontos"></span><strong>{ui.esc(brl(total))}</strong></div></div>'
    )

    pdf = gerar_relatorio_pdf(
        inicio,
        fim,
        viagens,
        implantacoes,
        _segredo("NOME_USUARIO", NOME_USUARIO_PADRAO),
        _segredo("EMPRESA", EMPRESA_PADRAO),
    )
    st.download_button(
        "Baixar PDF",
        data=pdf,
        file_name=f"relatorio-viagens_{inicio:%Y-%m-%d}_a_{fim:%Y-%m-%d}.pdf",
        mime="application/pdf",
        type="primary",
        icon=":material/download:",
        width="stretch",
        on_click="ignore",
        key="btn-baixar-pdf",
    )
