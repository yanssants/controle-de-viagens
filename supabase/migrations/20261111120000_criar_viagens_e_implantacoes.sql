-- Controle de Viagens: tabelas de viagens e implantações, índices e RLS.

-- ---------------------------------------------------------------- tabelas
create table public.viagens (
  id bigint generated always as identity primary key,
  criado_em timestamptz not null default now(),
  saida text not null default 'Escritório',
  destino text not null,
  tipo text not null check (tipo in ('curta','longa','muito_longa')),
  valor numeric(10,2) not null,
  motivo text not null
);

create table public.implantacoes (
  id bigint generated always as identity primary key,
  criado_em timestamptz not null default now(),
  cliente text not null,
  sistema text not null,
  data_implantacao date not null,
  comissao numeric(10,2) not null check (comissao >= 0)
);

comment on table public.viagens is 'Viagens a clientes. O valor é calculado pelo app a partir do tipo (5, 10 ou 15).';
comment on table public.implantacoes is 'Implantações realizadas e a comissão recebida por cada uma.';

-- ---------------------------------------------------------------- índices
-- As listas e o relatório filtram por período e ordenam pela data mais recente.
create index viagens_criado_em_idx on public.viagens (criado_em desc);
create index implantacoes_data_implantacao_idx on public.implantacoes (data_implantacao desc, id desc);

-- ---------------------------------------------------------------- RLS
alter table public.viagens enable row level security;
alter table public.implantacoes enable row level security;

-- O app não tem login próprio: ele roda no servidor do Streamlit e acessa o
-- Supabase com a chave guardada em st.secrets. As policies abaixo liberam
-- leitura e escrita para os papéis usados pelas chaves do projeto (anon e
-- authenticated). Veja a seção "Segurança" do README para restringir o acesso.

create policy "viagens: leitura pelo app"
  on public.viagens for select
  to anon, authenticated
  using (true);

create policy "viagens: inclusão pelo app"
  on public.viagens for insert
  to anon, authenticated
  with check (true);

create policy "viagens: alteração pelo app"
  on public.viagens for update
  to anon, authenticated
  using (true)
  with check (true);

create policy "viagens: exclusão pelo app"
  on public.viagens for delete
  to anon, authenticated
  using (true);

create policy "implantacoes: leitura pelo app"
  on public.implantacoes for select
  to anon, authenticated
  using (true);

create policy "implantacoes: inclusão pelo app"
  on public.implantacoes for insert
  to anon, authenticated
  with check (true);

create policy "implantacoes: alteração pelo app"
  on public.implantacoes for update
  to anon, authenticated
  using (true)
  with check (true);

create policy "implantacoes: exclusão pelo app"
  on public.implantacoes for delete
  to anon, authenticated
  using (true);

-- ---------------------------------------------------------------- privilégios
-- Somente o necessário para o app (colunas identity dispensam grant de sequência).
grant select, insert, update, delete on public.viagens to anon, authenticated;
grant select, insert, update, delete on public.implantacoes to anon, authenticated;
