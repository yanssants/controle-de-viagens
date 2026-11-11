"""Acesso ao Supabase (Postgres) via supabase-py.

As credenciais vêm de st.secrets (SUPABASE_URL e SUPABASE_KEY) e nunca ficam no código.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import streamlit as st

from config import FUSO, VALORES_TIPO


class ErroBanco(RuntimeError):
    """Falha ao ler ou gravar no Supabase, com mensagem pronta para o usuário."""


# --------------------------------------------------------------------------- conexão


def verificar_credenciais() -> tuple[bool, str]:
    try:
        url = st.secrets.get("SUPABASE_URL")
        chave = st.secrets.get("SUPABASE_KEY")
    except Exception:
        return False, "O arquivo .streamlit/secrets.toml não foi encontrado."
    if not url or not chave:
        return False, "Defina SUPABASE_URL e SUPABASE_KEY em .streamlit/secrets.toml."
    return True, ""


@st.cache_resource(show_spinner=False)
def _cliente():
    from supabase import create_client

    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def _executar(montar_consulta, acao: str):
    try:
        return montar_consulta(_cliente()).execute()
    except ErroBanco:
        raise
    except Exception as exc:  # erros de rede, de RLS, de validação do Postgres etc.
        raise ErroBanco(f"Não foi possível {acao}. Detalhe: {exc}") from exc


def _utc_iso(momento: datetime) -> str:
    return momento.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _limites_do_periodo(inicio: date, fim: date) -> tuple[str, str]:
    """Do início do dia `inicio` até o início do dia seguinte a `fim`, no fuso de São Paulo."""
    de = datetime.combine(inicio, time.min, FUSO)
    ate = datetime.combine(fim + timedelta(days=1), time.min, FUSO)
    return _utc_iso(de), _utc_iso(ate)


# --------------------------------------------------------------------------- viagens


def _viagem(linha: dict) -> dict:
    return {
        "id": linha["id"],
        "criado_em": datetime.fromisoformat(linha["criado_em"]).astimezone(FUSO),
        "saida": linha["saida"],
        "destino": linha["destino"],
        "tipo": linha["tipo"],
        "valor": Decimal(str(linha["valor"])),
        "motivo": linha["motivo"],
    }


@st.cache_data(ttl=60, show_spinner=False)
def _buscar_viagens(de_iso: str, ate_iso: str) -> list[dict]:
    resposta = _executar(
        lambda c: c.table("viagens")
        .select("*")
        .gte("criado_em", de_iso)
        .lt("criado_em", ate_iso)
        .order("criado_em", desc=True),
        "carregar as viagens",
    )
    return resposta.data or []


def listar_viagens(inicio: date, fim: date) -> list[dict]:
    return [_viagem(linha) for linha in _buscar_viagens(*_limites_do_periodo(inicio, fim))]


def criar_viagem(saida: str, destino: str, tipo: str, motivo: str) -> None:
    # criado_em fica com o default now() do banco: a data/hora é gravada no momento do registro.
    dados = {
        "saida": saida,
        "destino": destino,
        "tipo": tipo,
        "valor": float(VALORES_TIPO[tipo]),
        "motivo": motivo,
    }
    _executar(lambda c: c.table("viagens").insert(dados), "registrar a viagem")
    _buscar_viagens.clear()


def atualizar_viagem(viagem_id: int, saida: str, destino: str, tipo: str, motivo: str) -> None:
    dados = {
        "saida": saida,
        "destino": destino,
        "tipo": tipo,
        "valor": float(VALORES_TIPO[tipo]),
        "motivo": motivo,
    }
    _executar(lambda c: c.table("viagens").update(dados).eq("id", viagem_id), "salvar a viagem")
    _buscar_viagens.clear()


def excluir_viagem(viagem_id: int) -> None:
    _executar(lambda c: c.table("viagens").delete().eq("id", viagem_id), "excluir a viagem")
    _buscar_viagens.clear()


# --------------------------------------------------------------------------- implantações


def _implantacao(linha: dict) -> dict:
    return {
        "id": linha["id"],
        "criado_em": datetime.fromisoformat(linha["criado_em"]).astimezone(FUSO),
        "cliente": linha["cliente"],
        "sistema": linha["sistema"],
        "data_implantacao": date.fromisoformat(linha["data_implantacao"]),
        "comissao": Decimal(str(linha["comissao"])),
    }


@st.cache_data(ttl=60, show_spinner=False)
def _buscar_implantacoes(de_iso: str, ate_iso: str) -> list[dict]:
    resposta = _executar(
        lambda c: c.table("implantacoes")
        .select("*")
        .gte("data_implantacao", de_iso)
        .lte("data_implantacao", ate_iso)
        .order("data_implantacao", desc=True)
        .order("id", desc=True),
        "carregar as implantações",
    )
    return resposta.data or []


def listar_implantacoes(inicio: date, fim: date) -> list[dict]:
    linhas = _buscar_implantacoes(inicio.isoformat(), fim.isoformat())
    return [_implantacao(linha) for linha in linhas]


def criar_implantacao(cliente: str, sistema: str, data_implantacao: date, comissao: Decimal) -> None:
    dados = {
        "cliente": cliente,
        "sistema": sistema,
        "data_implantacao": data_implantacao.isoformat(),
        "comissao": float(comissao),
    }
    _executar(lambda c: c.table("implantacoes").insert(dados), "registrar a implantação")
    _buscar_implantacoes.clear()


def atualizar_implantacao(
    implantacao_id: int, cliente: str, sistema: str, data_implantacao: date, comissao: Decimal
) -> None:
    dados = {
        "cliente": cliente,
        "sistema": sistema,
        "data_implantacao": data_implantacao.isoformat(),
        "comissao": float(comissao),
    }
    _executar(
        lambda c: c.table("implantacoes").update(dados).eq("id", implantacao_id),
        "salvar a implantação",
    )
    _buscar_implantacoes.clear()


def excluir_implantacao(implantacao_id: int) -> None:
    _executar(
        lambda c: c.table("implantacoes").delete().eq("id", implantacao_id),
        "excluir a implantação",
    )
    _buscar_implantacoes.clear()
