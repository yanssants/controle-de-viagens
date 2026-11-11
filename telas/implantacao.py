"""Tela Implantação: registro de implantações e lista com edição/exclusão."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import streamlit as st

import db
import ui
from config import MAX_CLIENTE, MAX_SISTEMA
from formatos import brl, data_br, hoje, ler_valor, numero_br, primeiro_dia_do_mes
from telas.comum import DATA_MAX, DATA_MIN, dialogo_relatorio, periodo_valido

# Larguras: Data da implantação, Cliente, Comissão, Editar, Excluir
LARGURAS = [1.4, 3.6, 1.3, 0.42, 0.42]


def _validar(cliente: str, sistema: str, data_impl: date | None, comissao_texto: str):
    """Devolve (erros, comissão em Decimal ou None)."""
    erros = []
    if not cliente:
        erros.append("Informe o cliente.")
    if not sistema:
        erros.append("Informe o sistema.")
    if not data_impl:
        erros.append("Informe a data da implantação.")
    comissao = None
    try:
        comissao = ler_valor(comissao_texto)
    except ValueError as erro:
        erros.append(str(erro))
    return erros, comissao


# --------------------------------------------------------------------------- formulário


def _iniciar_estado() -> None:
    ss = st.session_state
    ss.setdefault("ni_cliente", "")
    ss.setdefault("ni_sistema", "")
    ss.setdefault("ni_data", hoje())
    ss.setdefault("ni_comissao", "")
    ss.setdefault("fi_de", primeiro_dia_do_mes())
    ss.setdefault("fi_ate", hoje())


def _limpar_formulario() -> None:
    ss = st.session_state
    ss.ni_cliente = ""
    ss.ni_sistema = ""
    ss.ni_data = hoje()
    ss.ni_comissao = ""
    ss.pop("ni_erros", None)


def _registrar() -> None:
    ss = st.session_state
    cliente = ss.ni_cliente.strip()
    sistema = ss.ni_sistema.strip()
    erros, comissao = _validar(cliente, sistema, ss.ni_data, ss.ni_comissao)
    if erros:
        ss.ni_erros = erros
        return
    try:
        db.criar_implantacao(cliente, sistema, ss.ni_data, comissao)
    except db.ErroBanco as erro:
        ss.ni_erros = [str(erro)]
        return
    _limpar_formulario()
    ui.agendar_toast(f"Implantação registrada: {cliente} ({brl(comissao)}).")


def _formulario() -> None:
    with st.container(key="secao-nova-implantacao"):
        ui.titulo_secao("Registrar nova implantação")
        c1, c2 = st.columns(2)
        c1.text_input("Cliente", key="ni_cliente", max_chars=MAX_CLIENTE, placeholder="Nome do cliente")
        c2.text_input("Sistema", key="ni_sistema", max_chars=MAX_SISTEMA, placeholder="Sistema implantado")
        c3, c4 = st.columns(2)
        c3.date_input(
            "Data da implantação", key="ni_data", format="DD/MM/YYYY", min_value=DATA_MIN, max_value=DATA_MAX
        )
        c4.text_input("Comissão (R$)", key="ni_comissao", placeholder="0,00")
        if st.session_state.get("ni_erros"):
            st.error("\n\n".join(st.session_state.ni_erros))

        _, c_limpar, c_registrar = st.columns([3, 1, 1.5])
        c_limpar.button("Limpar", key="btn-limpar-implantacao", on_click=_limpar_formulario, width="stretch")
        c_registrar.button(
            "Registrar implantação",
            key="btn-registrar-implantacao",
            type="primary",
            icon=":material/check:",
            on_click=_registrar,
            width="stretch",
        )


# --------------------------------------------------------------------------- pop-up de edição


@st.dialog("Editar implantação", width="medium")
def dialogo_implantacao(impl: dict, nonce: str, confirmar_exclusao: bool = False) -> None:
    prefixo = f"ei-{nonce}-"
    chave_confirmar = prefixo + "confirmar"
    st.session_state.setdefault(chave_confirmar, confirmar_exclusao)

    ui.subtitulo_dialogo(f"Registrada em {data_br(impl['criado_em'])}")
    c1, c2 = st.columns(2)
    cliente = c1.text_input("Cliente", value=impl["cliente"], key=prefixo + "cliente", max_chars=MAX_CLIENTE)
    sistema = c2.text_input("Sistema", value=impl["sistema"], key=prefixo + "sistema", max_chars=MAX_SISTEMA)
    c3, c4 = st.columns(2)
    data_impl = c3.date_input(
        "Data da implantação",
        value=impl["data_implantacao"],
        key=prefixo + "data",
        format="DD/MM/YYYY",
        min_value=DATA_MIN,
        max_value=DATA_MAX,
    )
    comissao_texto = c4.text_input("Comissão (R$)", value=numero_br(impl["comissao"]), key=prefixo + "comissao")

    if st.session_state[chave_confirmar]:
        ui.aviso(
            f"Excluir a implantação de {impl['cliente']} ({data_br(impl['data_implantacao'])})? "
            "Esta ação não pode ser desfeita."
        )
        with st.container(key=f"dlg-rodape-{nonce}"):
            _, c_voltar, c_confirmar = st.columns([2, 1, 1.4])
            c_voltar.button(
                "Cancelar",
                key=prefixo + "voltar",
                width="stretch",
                on_click=lambda: st.session_state.__setitem__(chave_confirmar, False),
            )
            if c_confirmar.button(
                "Excluir implantação",
                key=prefixo + "btn-confirmar-exclusao",
                icon=":material/delete:",
                width="stretch",
            ):
                try:
                    db.excluir_implantacao(impl["id"])
                except db.ErroBanco as erro:
                    st.error(str(erro))
                    return
                ui.agendar_toast("Implantação excluída.")
                st.rerun()
        return

    with st.container(key=f"dlg-rodape-{nonce}"):
        c_excluir, _, c_cancelar, c_salvar = st.columns([1, 1, 1, 1.4])
        c_excluir.button(
            "Excluir",
            key=prefixo + "btn-excluir",
            icon=":material/delete:",
            width="stretch",
            on_click=lambda: st.session_state.__setitem__(chave_confirmar, True),
        )
        if c_cancelar.button("Cancelar", key=prefixo + "cancelar", width="stretch"):
            st.rerun()
        if c_salvar.button("Salvar alterações", key=prefixo + "salvar", type="primary", width="stretch"):
            cliente, sistema = cliente.strip(), sistema.strip()
            erros, comissao = _validar(cliente, sistema, data_impl, comissao_texto)
            if erros:
                st.error("\n\n".join(erros))
                return
            try:
                db.atualizar_implantacao(impl["id"], cliente, sistema, data_impl, comissao)
            except db.ErroBanco as erro:
                st.error(str(erro))
                return
            ui.agendar_toast("Implantação atualizada.")
            st.rerun()


# --------------------------------------------------------------------------- lista


def _lista(implantacoes: list[dict], periodo_ok: bool):
    abrir = None
    with st.container(key="secao-lista-implantacoes"):
        ui.titulo_secao("Implantações realizadas")
        f1, f2, _ = st.columns([1, 1, 1.3])
        f1.date_input("De", key="fi_de", format="DD/MM/YYYY", min_value=DATA_MIN, max_value=DATA_MAX)
        f2.date_input("Até", key="fi_ate", format="DD/MM/YYYY", min_value=DATA_MIN, max_value=DATA_MAX)

        if not periodo_ok:
            st.warning("A data inicial deve ser anterior ou igual à data final.")
            return None

        with st.container(key="tabela-implantacoes"):
            with st.container(key="thead-implantacoes"):
                cols = st.columns(LARGURAS, vertical_alignment="center")
                for col, (texto, direita) in zip(
                    cols, [("Data da implantação", False), ("Cliente", False), ("Comissão", True), ("Ações", False)]
                ):
                    col.markdown(ui.th(texto, direita), unsafe_allow_html=True)

            if not implantacoes:
                ui.tabela_vazia("Nenhuma implantação encontrada no período.")
            for impl in implantacoes:
                with st.container(key=f"tr-implantacao-{impl['id']}"):
                    cols = st.columns(LARGURAS, vertical_alignment="center")
                    cols[0].markdown(ui.td(data_br(impl["data_implantacao"])), unsafe_allow_html=True)
                    cols[1].markdown(
                        ui.td(f'{ui.esc(impl["cliente"])}<span class="cv-td-sub">{ui.esc(impl["sistema"])}</span>'),
                        unsafe_allow_html=True,
                    )
                    cols[2].markdown(ui.td(ui.esc(brl(impl["comissao"])), "cv-num"), unsafe_allow_html=True)
                    if cols[3].button(
                        ":material/edit:", key=f"ico-editar-implantacao-{impl['id']}", help="Editar implantação"
                    ):
                        abrir = lambda i=impl: dialogo_implantacao(i, uuid.uuid4().hex)
                    if cols[4].button(
                        ":material/delete:", key=f"ico-excluir-implantacao-{impl['id']}", help="Excluir implantação"
                    ):
                        abrir = lambda i=impl: dialogo_implantacao(i, uuid.uuid4().hex, confirmar_exclusao=True)

            total = sum((i["comissao"] for i in implantacoes), Decimal("0"))
            ui.rodape_tabela("Total das comissões do período", total)
    return abrir


# --------------------------------------------------------------------------- tela


def render():
    _iniciar_estado()
    ss = st.session_state
    abrir = None

    c_titulo, c_botao = st.columns([4, 1.4], vertical_alignment="bottom")
    with c_titulo:
        ui.titulo_pagina("Implantações", "Registre as implantações realizadas e as comissões recebidas.")
    if c_botao.button(
        "Gerar relatório PDF",
        key="btn-relatorio-implantacoes",
        type="primary",
        icon=":material/download:",
        width="stretch",
    ):
        de, ate = ss.fi_de, ss.fi_ate
        abrir = lambda: dialogo_relatorio(de, ate)

    periodo_ok = periodo_valido(ss.fi_de, ss.fi_ate)
    implantacoes: list[dict] = []
    if periodo_ok:
        try:
            implantacoes = db.listar_implantacoes(ss.fi_de, ss.fi_ate)
        except db.ErroBanco as erro:
            st.error(str(erro))

    _formulario()
    abrir = _lista(implantacoes, periodo_ok) or abrir
    return abrir
