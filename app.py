"""Controle de Viagens: ponto de entrada.

Execute com:  streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Controle de Viagens",
    page_icon=":material/location_on:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import db  # noqa: E402
import ui  # noqa: E402
from telas import implantacao, viagens  # noqa: E402

PAGINAS = {
    "viagens": viagens.render,
    "implantacao": implantacao.render,
}


def main() -> None:
    ui.carregar_css(Path(__file__).with_name("styles.css"))

    credenciais_ok, mensagem = db.verificar_credenciais()
    if not credenciais_ok:
        ui.tela_configuracao(mensagem)
        st.stop()

    if st.session_state.get("pagina") not in PAGINAS:
        st.session_state.pagina = "viagens"
    ui.exibir_toasts()

    # Menu lateral próprio (coluna de 240px). No celular ele vira uma aba lateral
    # recolhível, aberta pelo botão da barra do topo (ver styles.css).
    col_menu, col_conteudo = st.columns([1, 5], gap="small")
    with col_menu:
        ui.menu_lateral()
    with col_conteudo:
        ui.barra_mobile()
        with st.container(key="conteudo"):
            abrir_dialogo = PAGINAS[st.session_state.pagina]()

    # Pop-ups são abertos fora das colunas para não aninhar colunas demais.
    if abrir_dialogo:
        abrir_dialogo()


main()
