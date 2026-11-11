# Controle de Viagens

Sistema web para registrar viagens a clientes e implantações, calcular a ajuda de custo do mês e gerar o relatório em PDF.

Feito com **Python + Streamlit**, dados no **Supabase (Postgres)** e PDF com **fpdf2**.

## Funcionalidades

- **Viagens**: cadastro com saída, destino, tipo (curta R$ 5,00, longa R$ 10,00, muito longa R$ 15,00) e motivo. Data e hora são gravadas automaticamente (horário de Brasília). Há indicadores do período, filtros por data e tipo, e edição/exclusão em pop-up.
- **Implantação**: cadastro com cliente, sistema, data e comissão. A lista tem filtro por período, total das comissões e edição/exclusão em pop-up.
- **Relatório em PDF (A4)** do período filtrado: resumo por tipo, detalhamento das viagens, implantações e o total a receber no mês (viagens + implantações + ajuda de custo fixa de R$ 100,00).

## Estrutura

```
app.py                  # ponto de entrada: layout, menu lateral e navegação
config.py               # constantes (valores por tipo, ajuda de custo, fuso, limites)
db.py                   # acesso ao Supabase (supabase-py)
relatorio.py            # geração do PDF (fpdf2)
formatos.py             # formatação brasileira de moeda e datas
ui.py                   # componentes visuais compartilhados
telas/viagens.py        # tela de viagens + pop-up de edição
telas/implantacao.py    # tela de implantação + pop-up de edição
telas/comum.py          # pop-up do relatório em PDF
styles.css              # design system (injetado no Streamlit)
.streamlit/config.toml  # tema do Streamlit
.streamlit/secrets.toml.example
supabase/migrations/    # SQL das tabelas, índices e RLS
```

## Requisitos

- Python 3.10 ou superior
- Uma conta e um projeto no [Supabase](https://supabase.com)

## Instalação

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Banco de dados (Supabase)

1. Crie um projeto no Supabase.
2. Aplique a migration `supabase/migrations/20261111120000_criar_viagens_e_implantacoes.sql`, de uma destas formas:
   - **SQL Editor**: abra *SQL Editor* no painel, cole o conteúdo do arquivo e clique em *Run*.
   - **Supabase CLI**:
     ```bash
     supabase login
     supabase link --project-ref SEU_PROJECT_REF
     supabase db push
     ```
3. A migration cria as tabelas `viagens` e `implantacoes`, os índices por data e habilita o RLS com as policies que o app usa.

## Credenciais

As chaves ficam somente em `.streamlit/secrets.toml`, nunca no código.

```bash
# Windows
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
# macOS / Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Preencha com os dados de *Project Settings > API* do Supabase:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "sua-chave-do-supabase"

# Opcional (cabeçalho do PDF)
NOME_USUARIO = "Seu nome"
EMPRESA = "Nome da empresa"
```

Se as credenciais não estiverem configuradas, o app mostra uma tela explicando o que falta.

No **Streamlit Community Cloud**, cole o mesmo conteúdo em *App settings > Secrets*.

## Execução

```bash
streamlit run app.py
```

O app abre em `http://localhost:8501`.

## Personalização

- **Valores por tipo, ajuda de custo e descrições dos cartões de tipo**: `config.py` (`TIPOS` e `AJUDA_CUSTO_MENSAL`). Os valores das viagens já gravadas não mudam; viagens editadas são recalculadas com o valor atual do tipo.
- **Fonte Inter no PDF (opcional)**: coloque `Inter-Regular.ttf` e `Inter-Bold.ttf` numa pasta `fonts/` na raiz do projeto. Sem esses arquivos o PDF usa Helvetica.

## Segurança

- O Streamlit roda no servidor, então a chave em `st.secrets` não é enviada ao navegador. Ainda assim, não publique o `secrets.toml` (ele já está no `.gitignore`).
- As policies da migration liberam leitura e escrita para os papéis `anon` e `authenticated`, porque o app não tem login próprio. Isso significa que **quem tiver a chave anon/publishable do projeto consegue ler e alterar esses dados pela API do Supabase**. Se essa chave for usada em outro lugar público, prefira:
  1. usar no `SUPABASE_KEY` a chave **secret / service_role** (ela ignora o RLS e nunca sai do servidor do Streamlit); e
  2. remover as policies para `anon` e `authenticated`, deixando o RLS habilitado sem policies (as tabelas ficam fechadas para a API pública):
     ```sql
     drop policy "viagens: leitura pelo app" on public.viagens;
     drop policy "viagens: inclusão pelo app" on public.viagens;
     drop policy "viagens: alteração pelo app" on public.viagens;
     drop policy "viagens: exclusão pelo app" on public.viagens;
     drop policy "implantacoes: leitura pelo app" on public.implantacoes;
     drop policy "implantacoes: inclusão pelo app" on public.implantacoes;
     drop policy "implantacoes: alteração pelo app" on public.implantacoes;
     drop policy "implantacoes: exclusão pelo app" on public.implantacoes;
     revoke all on public.viagens, public.implantacoes from anon, authenticated;
     ```
