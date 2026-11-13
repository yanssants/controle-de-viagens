"""Componentes visuais compartilhados (HTML/CSS do design system) e utilidades de interface."""

from __future__ import annotations

import html
from decimal import Decimal
from pathlib import Path

import streamlit as st

from config import AJUDA_CUSTO_MENSAL, APP_SUBTITULO, APP_TITULO, TIPOS
from formatos import brl, plural
from relatorio import resumo_por_tipo

# Ícones em traço (estilo Lucide, stroke 2, 18px)
_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="{t}" height="{t}" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">{p}</svg>'
)
_PATHS = {
    "localizacao": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "relogio": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "alerta": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
}


def icone(nome: str, tamanho: int = 18) -> str:
    return _SVG.format(t=tamanho, p=_PATHS[nome])


def esc(texto) -> str:
    return html.escape(str(texto), quote=True)


def html_(conteudo: str) -> None:
    st.markdown(conteudo, unsafe_allow_html=True)


# --------------------------------------------------------------------------- base


def carregar_css(caminho: Path) -> None:
    html_(f"<style>{caminho.read_text(encoding='utf-8')}</style>")


def agendar_toast(mensagem: str) -> None:
    """Guarda a mensagem para exibir no próximo rerun (sobrevive a st.rerun e a callbacks)."""
    st.session_state.setdefault("_toasts", []).append(mensagem)


def exibir_toasts() -> None:
    for mensagem in st.session_state.pop("_toasts", []):
        st.toast(mensagem, icon=":material/check_circle:")


def tela_configuracao(mensagem: str) -> None:
    with st.container(key="aviso-configuracao"):
        html_(f'<h1 class="cv-h1">{esc(APP_TITULO)}</h1>')
        st.error(f"{mensagem} Veja o README.md para configurar a conexão com o Supabase.")
        st.code(
            'SUPABASE_URL = "https://SEU-PROJETO.supabase.co"\nSUPABASE_KEY = "SUA-CHAVE"',
            language="toml",
        )


# --------------------------------------------------------------------------- menu lateral


def _ir_para(pagina: str) -> None:
    st.session_state.pagina = pagina
    st.session_state.menu_aberto = False  # no celular, fecha o menu ao navegar


def _alternar_menu() -> None:
    st.session_state.menu_aberto = not st.session_state.get("menu_aberto", False)


def _logo_html() -> str:
    return (
        '<div class="cv-logo">'
        f'<div class="cv-logo-icone">{icone("localizacao", 20)}</div>'
        f'<div><div class="cv-logo-titulo">{esc(APP_TITULO)}</div>'
        f'<div class="cv-logo-sub">{esc(APP_SUBTITULO)}</div></div></div>'
    )


def barra_mobile() -> None:
    """Barra do topo exibida só no celular, com o botão que abre o menu lateral."""
    with st.container(key="barra-mobile", horizontal=True, vertical_alignment="center"):
        st.button(
            "",
            key="btn-menu-abrir",
            icon=":material/menu:",
            help="Abrir menu",
            on_click=_alternar_menu,
        )
        html_(_logo_html())


def menu_lateral() -> None:
    """Menu lateral fixo no desktop; no celular vira uma aba lateral recolhível.

    No celular o menu fica escondido à esquerda e desliza para dentro quando aberto pelo
    botão da barra do topo; o botão "X" dentro do menu o recolhe de novo. A chave do
    container dos itens indica o estado (menu-itens-aberto / menu-itens-fechado) e o CSS
    usa isso só no mobile; no desktop o menu fica sempre visível.
    """
    pagina = st.session_state.get("pagina", "viagens")
    aberto = st.session_state.get("menu_aberto", False)
    with st.container(key="menu-lateral"):
        with st.container(key="menu-topo", horizontal=True, vertical_alignment="center"):
            html_(_logo_html())
            st.button(
                "",
                key="btn-menu-alternar",
                icon=":material/chevron_left:",
                help="Recolher menu",
                on_click=_alternar_menu,
            )
        with st.container(key=f"menu-itens-{'aberto' if aberto else 'fechado'}"):
            for chave, rotulo in (("viagens", "Viagens"), ("implantacao", "Implantação")):
                st.button(
                    rotulo,
                    key=f"nav-{chave}",
                    type="primary" if pagina == chave else "secondary",
                    width="stretch",
                    on_click=_ir_para,
                    args=(chave,),
                )
            linhas = "".join(_linha_card(info["rotulo"], brl(info["valor"])) for info in TIPOS.values())
            html_(
                '<div class="cv-card-menu"><div class="cv-card-titulo">Tabela de valores</div>'
                f"{linhas}</div>"
                '<div class="cv-card-menu"><div class="cv-card-titulo">Ajuda de custo mensal</div>'
                f'{_linha_card("Valor fixo", brl(AJUDA_CUSTO_MENSAL))}</div>'
            )


def _linha_card(rotulo: str, valor: str) -> str:
    return (
        f'<div class="cv-card-linha"><span>{esc(rotulo)}</span>'
        f'<span class="cv-pontos"></span><strong>{esc(valor)}</strong></div>'
    )


# --------------------------------------------------------------------------- textos


def titulo_pagina(titulo: str, subtitulo: str = "") -> None:
    sub = f'<p class="cv-sub">{esc(subtitulo)}</p>' if subtitulo else ""
    html_(f'<h1 class="cv-h1">{esc(titulo)}</h1>{sub}')


def titulo_secao(titulo: str, subtitulo: str = "") -> None:
    sub = f'<p class="cv-sub-secao">{esc(subtitulo)}</p>' if subtitulo else ""
    html_(f'<h2 class="cv-h2">{esc(titulo)}</h2>{sub}')


def subtitulo_dialogo(texto: str) -> None:
    html_(f'<p class="cv-sub-dialogo">{esc(texto)}</p>')


def chip_data(texto: str) -> str:
    return f'<span class="cv-chip-data">{icone("relogio", 15)}<span>{esc(texto)}</span></span>'


def chip_tipo(tipo: str) -> str:
    info = TIPOS.get(tipo, {"rotulo": tipo, "cor": "#3A404C", "fundo": "#F1F3F6"})
    return (
        f'<span class="cv-chip" style="color:{info["cor"]};background:{info["fundo"]}">'
        f'{esc(info["rotulo"])}</span>'
    )


def aviso(texto: str) -> None:
    html_(f'<div class="cv-aviso" role="alert">{icone("alerta", 18)}<span>{esc(texto)}</span></div>')


def rotulo_cartao_tipo(tipo: str) -> str:
    """Texto do cartão de seleção do tipo: nome e valor (cada um em um parágrafo)."""
    info = TIPOS[tipo]
    return f"{info['rotulo']}\n\n{brl(info['valor'])}"


def rotulo_tipo(tipo: str) -> str:
    return "Todos os tipos" if tipo == "todos" else TIPOS[tipo]["rotulo"]


# --------------------------------------------------------------------------- cards de resumo


def cards_kpi(viagens: list[dict]) -> None:
    resumo = resumo_por_tipo(viagens)
    total = sum((v["valor"] for v in viagens), Decimal("0"))
    qtd_total = len(viagens)
    cards = [
        '<div class="cv-kpi"><div class="cv-kpi-rotulo">Total de viagens</div>'
        f'<div class="cv-kpi-numero">{qtd_total}</div>'
        '<div class="cv-kpi-detalhe">no período filtrado</div></div>'
    ]
    for tipo, info in TIPOS.items():
        item = resumo[tipo]
        cards.append(
            '<div class="cv-kpi">'
            f'<div class="cv-kpi-rotulo"><span class="cv-ponto" style="background:{info["cor"]}"></span>'
            f'{esc(info["plural"])}</div>'
            f'<div class="cv-kpi-numero">{item["quantidade"]}</div>'
            f'<div class="cv-kpi-detalhe">{esc(brl(item["valor"]))}</div></div>'
        )
    cards.append(
        '<div class="cv-kpi cv-kpi-total"><div class="cv-kpi-rotulo">Total das viagens</div>'
        f'<div class="cv-kpi-numero">{esc(brl(total))}</div>'
        f'<div class="cv-kpi-detalhe">{qtd_total} {plural(qtd_total, "viagem", "viagens")}</div></div>'
    )
    html_(f'<div class="cv-kpis" role="list">{"".join(cards)}</div>')


# --------------------------------------------------------------------------- tabela


def th(texto: str, direita: bool = False) -> str:
    classe = "cv-th cv-num" if direita else "cv-th"
    return f'<div class="{classe}">{esc(texto)}</div>'


def td(conteudo_html: str, classe: str = "") -> str:
    return f'<div class="cv-td {classe}">{conteudo_html}</div>'


def rodape_tabela(rotulo: str, valor) -> None:
    html_(
        f'<div class="cv-tfoot"><span>{esc(rotulo)}</span>'
        f"<strong>{esc(brl(valor))}</strong></div>"
    )


def tabela_vazia(texto: str) -> None:
    html_(f'<div class="cv-vazio">{esc(texto)}</div>')
