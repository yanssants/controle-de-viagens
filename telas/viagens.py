"""Tela Viagens: resumo do período, registro de viagem e lista com edição/exclusão."""

from __future__ import annotations

import uuid

import streamlit as st

import db
import ui
from config import MAX_LOCAL, MAX_MOTIVO, SAIDA_PADRAO, TIPOS
from formatos import agora, brl, data_br, data_hora_br, hoje, primeiro_dia_do_mes
from telas.comum import DATA_MAX, DATA_MIN, dialogo_relatorio, periodo_valido

# Larguras: Data, Saída, Destino, Tipo, Motivo, Valor, Editar, Excluir
LARGURAS = [1.35, 1.3, 1.45, 1.15, 2.6, 1.0, 0.42, 0.42]
OPCOES_TIPO = list(TIPOS)


def _validar(saida: str, destino: str, tipo: str | None, motivo: str) -> list[str]:
    erros = []
    if not saida:
        erros.append("Informe o local de saída.")
    if not destino:
        erros.append("Informe o local de destino.")
    if tipo not in TIPOS:
        erros.append("Selecione o tipo de viagem.")
    if not motivo:
        erros.append("Informe o motivo da viagem.")
    return erros


# --------------------------------------------------------------------------- formulário


def _iniciar_estado() -> None:
    ss = st.session_state
    ss.setdefault("nv_saida", SAIDA_PADRAO)
    ss.setdefault("nv_destino", "")
    ss.setdefault("nv_motivo", "")
    ss.setdefault("fv_de", primeiro_dia_do_mes())
    ss.setdefault("fv_ate", hoje())
    ss.setdefault("fv_tipo", "todos")


def _limpar_formulario() -> None:
    ss = st.session_state
    ss.nv_saida = SAIDA_PADRAO
    ss.nv_destino = ""
    ss.nv_motivo = ""
    ss["radio-tipo-nova"] = None
    ss.pop("nv_erros", None)


def _registrar() -> None:
    ss = st.session_state
    saida = ss.nv_saida.strip()
    destino = ss.nv_destino.strip()
    motivo = ss.nv_motivo.strip()
    tipo = ss.get("radio-tipo-nova")
    erros = _validar(saida, destino, tipo, motivo)
    if erros:
        ss.nv_erros = erros
        return
    try:
        db.criar_viagem(saida, destino, tipo, motivo)
    except db.ErroBanco as erro:
        ss.nv_erros = [str(erro)]
        return
    _limpar_formulario()
    ui.agendar_toast(f"Viagem registrada: {destino} ({brl(TIPOS[tipo]['valor'])}).")


def _formulario() -> None:
    with st.container(key="secao-nova-viagem"):
        ui.titulo_secao("Registrar nova viagem", "O valor é definido pelo tipo de viagem.")
        c1, c2 = st.columns(2)
        c1.text_input("Local de saída", key="nv_saida", max_chars=MAX_LOCAL)
        c2.text_input(
            "Local de destino",
            key="nv_destino",
            max_chars=MAX_LOCAL,
            placeholder="Ex.: Cliente Alfa, Campinas",
        )
        st.radio(
            "Tipo de viagem",
            OPCOES_TIPO,
            index=None,
            horizontal=True,
            format_func=ui.rotulo_cartao_tipo,
            key="radio-tipo-nova",
        )
        st.text_area(
            "Motivo da viagem",
            key="nv_motivo",
            max_chars=MAX_MOTIVO,
            height=110,
            placeholder="Descreva o objetivo da visita",
        )
        if st.session_state.get("nv_erros"):
            st.error("\n\n".join(st.session_state.nv_erros))

        c_chip, c_limpar, c_registrar = st.columns([3, 1, 1.35], vertical_alignment="center")
        with c_chip:
            ui.html_(
                ui.chip_data(
                    "Data e hora gravadas automaticamente ao registrar "
                    f"(agora: {data_hora_br(agora(), ' às ')})"
                )
            )
        c_limpar.button("Limpar", key="btn-limpar-viagem", on_click=_limpar_formulario, width="stretch")
        c_registrar.button(
            "Registrar viagem",
            key="btn-registrar-viagem",
            type="primary",
            icon=":material/check:",
            on_click=_registrar,
            width="stretch",
        )


# --------------------------------------------------------------------------- pop-up de edição


@st.dialog("Editar viagem", width="medium")
def dialogo_viagem(viagem: dict, nonce: str, confirmar_exclusao: bool = False) -> None:
    prefixo = f"ev-{nonce}-"
    chave_confirmar = prefixo + "confirmar"
    st.session_state.setdefault(chave_confirmar, confirmar_exclusao)

    ui.subtitulo_dialogo("Altere os dados da viagem. A data de registro não pode ser editada.")
    ui.html_(ui.chip_data(f"Registrada em {data_hora_br(viagem['criado_em'], ' às ')}"))

    c1, c2 = st.columns(2)
    saida = c1.text_input("Local de saída", value=viagem["saida"], key=prefixo + "saida", max_chars=MAX_LOCAL)
    destino = c2.text_input(
        "Local de destino", value=viagem["destino"], key=prefixo + "destino", max_chars=MAX_LOCAL
    )
    tipo = st.radio(
        "Tipo de viagem",
        OPCOES_TIPO,
        index=OPCOES_TIPO.index(viagem["tipo"]) if viagem["tipo"] in TIPOS else None,
        horizontal=True,
        format_func=ui.rotulo_cartao_tipo,
        key=f"radio-tipo-{nonce}",
    )
    motivo = st.text_area(
        "Motivo da viagem", value=viagem["motivo"], key=prefixo + "motivo", max_chars=MAX_MOTIVO, height=110
    )

    if st.session_state[chave_confirmar]:
        ui.aviso(
            f"Excluir a viagem para {viagem['destino']} de {data_br(viagem['criado_em'])}? "
            "Esta ação não pode ser desfeita."
        )
        with st.container(key=f"dlg-rodape-{nonce}"):
            _, c_voltar, c_confirmar = st.columns([2, 1, 1.3])
            c_voltar.button(
                "Cancelar",
                key=prefixo + "voltar",
                width="stretch",
                on_click=lambda: st.session_state.__setitem__(chave_confirmar, False),
            )
            if c_confirmar.button(
                "Excluir viagem",
                key=prefixo + "btn-confirmar-exclusao",
                icon=":material/delete:",
                width="stretch",
            ):
                try:
                    db.excluir_viagem(viagem["id"])
                except db.ErroBanco as erro:
                    st.error(str(erro))
                    return
                ui.agendar_toast("Viagem excluída.")
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
            saida, destino, motivo = saida.strip(), destino.strip(), motivo.strip()
            erros = _validar(saida, destino, tipo, motivo)
            if erros:
                st.error("\n\n".join(erros))
                return
            try:
                db.atualizar_viagem(viagem["id"], saida, destino, tipo, motivo)
            except db.ErroBanco as erro:
                st.error(str(erro))
                return
            ui.agendar_toast("Viagem atualizada.")
            st.rerun()


# --------------------------------------------------------------------------- lista


def _lista(viagens_periodo: list[dict], periodo_ok: bool):
    """Desenha a lista e devolve a ação de abrir um pop-up (ou None)."""
    abrir = None
    with st.container(key="secao-lista-viagens"):
        ui.titulo_secao("Viagens registradas")
        f1, f2, f3 = st.columns([1, 1, 1.3])
        f1.date_input("De", key="fv_de", format="DD/MM/YYYY", min_value=DATA_MIN, max_value=DATA_MAX)
        f2.date_input("Até", key="fv_ate", format="DD/MM/YYYY", min_value=DATA_MIN, max_value=DATA_MAX)
        f3.selectbox("Tipo", ["todos", *OPCOES_TIPO], key="fv_tipo", format_func=ui.rotulo_tipo)

        if not periodo_ok:
            st.warning("A data inicial deve ser anterior ou igual à data final.")
            return None

        filtro = st.session_state.fv_tipo
        viagens = [v for v in viagens_periodo if filtro == "todos" or v["tipo"] == filtro]

        with st.container(key="tabela-viagens"):
            with st.container(key="thead-viagens"):
                cols = st.columns(LARGURAS, vertical_alignment="center")
                for col, (texto, direita) in zip(
                    cols,
                    [("Data", False), ("Saída", False), ("Destino", False), ("Tipo", False),
                     ("Motivo", False), ("Valor", True), ("Ações", False)],
                ):
                    col.markdown(ui.th(texto, direita), unsafe_allow_html=True)

            if not viagens:
                ui.tabela_vazia("Nenhuma viagem encontrada para os filtros escolhidos.")
            for v in viagens:
                with st.container(key=f"tr-viagem-{v['id']}"):
                    cols = st.columns(LARGURAS, vertical_alignment="center")
                    celulas = [
                        ui.td(
                            f"{data_br(v['criado_em'])}"
                            f'<span class="cv-td-sub">{v["criado_em"]:%H:%M}</span>'
                        ),
                        ui.td(ui.esc(v["saida"])),
                        ui.td(ui.esc(v["destino"])),
                        ui.td(ui.chip_tipo(v["tipo"])),
                        ui.td(ui.esc(v["motivo"]), "cv-motivo"),
                        ui.td(ui.esc(brl(v["valor"])), "cv-num"),
                    ]
                    for col, celula in zip(cols, celulas):
                        col.markdown(celula, unsafe_allow_html=True)
                    if cols[6].button(":material/edit:", key=f"ico-editar-viagem-{v['id']}", help="Editar viagem"):
                        abrir = lambda v=v: dialogo_viagem(v, uuid.uuid4().hex)
                    if cols[7].button(":material/delete:", key=f"ico-excluir-viagem-{v['id']}", help="Excluir viagem"):
                        abrir = lambda v=v: dialogo_viagem(v, uuid.uuid4().hex, confirmar_exclusao=True)

            total = sum((v["valor"] for v in viagens), start=0)
            ui.rodape_tabela("Total das viagens do período", total)
    return abrir


# --------------------------------------------------------------------------- tela


def render():
    _iniciar_estado()
    ss = st.session_state
    abrir = None

    c_titulo, c_botao = st.columns([4, 1.4], vertical_alignment="bottom")
    with c_titulo:
        ui.titulo_pagina("Minhas viagens a clientes", "Registre cada deslocamento e acompanhe o total do período.")
    if c_botao.button(
        "Gerar relatório PDF", key="btn-relatorio-viagens", type="primary", icon=":material/download:", width="stretch"
    ):
        de, ate = ss.fv_de, ss.fv_ate
        abrir = lambda: dialogo_relatorio(de, ate)

    periodo_ok = periodo_valido(ss.fv_de, ss.fv_ate)
    viagens: list[dict] = []
    if periodo_ok:
        try:
            viagens = db.listar_viagens(ss.fv_de, ss.fv_ate)
        except db.ErroBanco as erro:
            st.error(str(erro))

    ui.cards_kpi(viagens)
    _formulario()
    abrir = _lista(viagens, periodo_ok) or abrir
    return abrir
