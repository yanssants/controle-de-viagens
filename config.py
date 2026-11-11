"""Configurações e constantes do Controle de Viagens."""

from __future__ import annotations

from decimal import Decimal
from zoneinfo import ZoneInfo

APP_TITULO = "Controle de Viagens"
APP_SUBTITULO = "Ajuda de custo"

# Fuso usado para exibir e filtrar datas/horas.
FUSO = ZoneInfo("America/Sao_Paulo")

# Ajuda de custo fixa paga todo mês, somada no relatório em PDF.
AJUDA_CUSTO_MENSAL = Decimal("100.00")

# Valor padrão do campo "Local de saída".
SAIDA_PADRAO = "Escritório"

# Tipos de viagem. O valor de cada viagem vem daqui, não de um campo do formulário.
# As "dicas" aparecem nos cartões de seleção e podem ser ajustadas à regra da empresa.
TIPOS: dict[str, dict] = {
    "curta": {
        "rotulo": "Curta",
        "plural": "Curtas",
        "valor": Decimal("5.00"),
        "dica": "Bairros próximos",
        "cor": "#146C3A",
        "fundo": "#E7F5EC",
    },
    "longa": {
        "rotulo": "Longa",
        "plural": "Longas",
        "valor": Decimal("10.00"),
        "dica": "Outro lado da cidade",
        "cor": "#1D4ED8",
        "fundo": "#E6EEFB",
    },
    "muito_longa": {
        "rotulo": "Muito longa",
        "plural": "Muito longas",
        "valor": Decimal("15.00"),
        "dica": "Cidades vizinhas",
        "cor": "#9A4A07",
        "fundo": "#FDEEDC",
    },
}

VALORES_TIPO: dict[str, Decimal] = {chave: info["valor"] for chave, info in TIPOS.items()}

# Textos do cabeçalho do PDF. Podem ser sobrescritos em .streamlit/secrets.toml
# com as chaves NOME_USUARIO e EMPRESA.
NOME_USUARIO_PADRAO = "[nome do usuário]"
EMPRESA_PADRAO = "[empresa]"

# Limites de tamanho dos campos de texto.
MAX_LOCAL = 120
MAX_MOTIVO = 1000
MAX_CLIENTE = 120
MAX_SISTEMA = 120
