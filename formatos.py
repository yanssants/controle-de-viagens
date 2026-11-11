"""Formatação no padrão brasileiro (R$ 1.234,56 e dd/mm/aaaa) e utilidades de data."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from config import FUSO

CENTAVOS = Decimal("0.01")
VALOR_MAXIMO = Decimal("99999999.99")  # limite de numeric(10,2)
_MILHAR = re.compile(r"^\d{1,3}(\.\d{3})+$")


def para_decimal(valor) -> Decimal:
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor if valor is not None else 0))
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def numero_br(valor) -> str:
    """1234.5 -> '1.234,50'"""
    d = para_decimal(valor)
    texto = f"{abs(d):,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"-{texto}" if d < 0 else texto


def brl(valor) -> str:
    """1234.5 -> 'R$ 1.234,50'"""
    d = para_decimal(valor)
    return f"-R$ {numero_br(abs(d))}" if d < 0 else f"R$ {numero_br(d)}"


def data_br(valor: date | datetime) -> str:
    if isinstance(valor, datetime):
        valor = valor.astimezone(FUSO)
    return valor.strftime("%d/%m/%Y")


def data_hora_br(valor: datetime, separador: str = " ") -> str:
    return valor.astimezone(FUSO).strftime(f"%d/%m/%Y{separador}%H:%M")


def agora() -> datetime:
    return datetime.now(FUSO)


def hoje() -> date:
    return agora().date()


def primeiro_dia_do_mes(referencia: date | None = None) -> date:
    return (referencia or hoje()).replace(day=1)


def ler_valor(texto: str) -> Decimal:
    """Converte '1.234,56', '1234,56', '1234.56' ou 'R$ 50' em Decimal.

    Levanta ValueError com uma mensagem pronta para o usuário.
    """
    s = (texto or "").strip().replace("R$", "").replace(" ", "").replace(" ", "")
    if not s:
        raise ValueError("Informe a comissão.")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif _MILHAR.match(s):
        s = s.replace(".", "")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError("Comissão inválida. Use o formato 1.234,56.") from None
    if not d.is_finite():
        raise ValueError("Comissão inválida. Use o formato 1.234,56.")
    if d < 0:
        raise ValueError("A comissão não pode ser negativa.")
    if d > VALOR_MAXIMO:
        raise ValueError("A comissão é maior que o valor máximo permitido.")
    return para_decimal(d)


def plural(quantidade: int, singular: str, plural_: str) -> str:
    return singular if quantidade == 1 else plural_
