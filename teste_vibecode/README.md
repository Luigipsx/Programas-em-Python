# Festa IFC · Campus Blumenau

Aplicação em **Python + Streamlit** para planejar uma única festa: alimentos, porções, insumos doados, recebimentos e escalas de trabalho. Os dados são persistidos com classes ORM do SQLAlchemy, em SQLite localmente ou MySQL em produção.

## Executar localmente

Pré-requisitos: Python 3.12 (também aceita 3.13) e [uv](https://docs.astral.sh/uv/getting-started/installation/).

Na raiz do projeto:

```powershell
uv sync
Copy-Item .env.example .env
uv run python src/init_db.py
uv run streamlit run src/app.py
```

No Linux/macOS, use `cp .env.example .env` no lugar de `Copy-Item`. Se já houver um `.env` configurado, preserve-o.

Abra o endereço local informado pelo Streamlit, normalmente http://localhost:8501. O projeto entregue já contém um `.env` local com SQLite e nenhuma credencial real. `uv sync` cria `.venv/` e instala as versões de `uv.lock`; para exigir o arquivo de lock sem atualizá-lo, use `uv sync --locked`.

As tabelas também são criadas automaticamente na primeira inicialização. `src/init_db.py` permite criá-las antecipadamente; executá-lo novamente preserva os registros. Não há carga automática de dados fictícios.

## Como usar

1. Cadastre **Insumos**, incluindo embalagens, com sua unidade.
2. Cadastre **Alimentos**, preços e porções. Em **Composição de cada alimento**, associe os insumos e suas quantidades por porção. A página **Composições** também permite gerenciar todas as associações.
3. Cadastre **Doadores** e registre cada insumo doado separadamente em **Doações**. Edite a quantidade recebida conforme as entregas acontecem.
4. Cadastre **Participantes** e **Tarefas**. Em **Escalas de trabalho**, escolha a pessoa, a atividade e o período.
5. Acompanhe o **Painel**, os déficits por insumo e a receita bruta potencial. É possível baixar a tabela de planejamento em CSV.

Todas as entidades têm cadastro, consulta, edição e exclusão. Use a busca e os filtros acima das tabelas; no seletor **Cadastrar ou editar**, escolha **Novo registro** ou um registro existente. Os códigos apresentados distinguem nomes iguais; os relacionamentos são escolhidos por nome em seletores.

A exclusão requer marcar a confirmação e clicar em **Excluir definitivamente**. Registros utilizados em outros cadastros não podem ser excluídos; a mensagem indica os vínculos a remover. A interface recarrega os dados após cada alteração. Para consultar alterações feitas por outra sessão, use **Atualizar informações** na barra lateral.

## Regras de planejamento

Para cada insumo, separadamente:

```text
necessária = soma(quantidade por porção × porções planejadas de cada alimento)
sem compromisso = máximo(necessária − prometida, 0)
falta receber = máximo(necessária − recebida, 0)
excedente prometido = máximo(prometida − necessária, 0)
excedente recebido = máximo(recebida − necessária, 0)
```

O painel considera **todos os alimentos**, incluindo os marcados como indisponíveis, conforme a regra de cálculo do escopo. Para retirar a produção de um alimento do planejamento, ajuste suas porções para zero.

A receita bruta potencial é `soma(preço por porção × porções planejadas)`. É uma estimativa condicionada à venda de todas as porções. Não representa lucro; despesas da festa não são registradas, e os insumos doados não recebem custo de compra.

Situação calculada da doação:

| Condição | Situação |
| --- | --- |
| Recebida igual a zero | Pendente |
| Recebida maior que zero e menor que a prometida | Parcialmente recebida |
| Recebida maior ou igual à prometida, com recebimento positivo | Recebida |

Uma promessa de zero, ainda sem recebimento, fica pendente. O excedente de cada doação é `máximo(recebida − prometida, 0)`; ele aparece na tabela de doações. Os excedentes do painel comparam os totais com a necessidade de produção.

Outras regras:

- Nome e escolhas obrigatórias não podem ficar vazios. Descrições, observações, contato e local são opcionais.
- Preços aceitam duas casas decimais; quantidades, quatro. Use vírgula ou ponto decimal, sem separador de milhar. Valores com precisão excedente são rejeitados, sem arredondamento silencioso.
- Porções são inteiras e não negativas. Preços e quantidades não podem ser negativos; composição exige quantidade maior que zero. O limite por campo numérico é 999999999.
- Unidades disponíveis: kg, g, L, mL e unidade. Não há conversão automática.
- Não é permitido repetir o mesmo insumo na composição de um alimento.
- A unidade fica bloqueada enquanto houver qualquer composição ou doação associada.
- Um participante é independente de um doador; a mesma pessoa pode ter ambos os cadastros.
- Escalas precisam terminar após o início e não podem se sobrepor para a mesma pessoa, mesmo em tarefas diferentes. Períodos adjacentes são aceitos: 18h–20h e 20h–22h.
- Horários de escalas são locais de Blumenau, no fuso America/Sao_Paulo. Escalas que atravessam a meia-noite usam datas diferentes.

## Configuração do banco

O arquivo `.env` fica na raiz. Variáveis já existentes no ambiente têm prioridade; não é necessário alterar código para trocar de banco.

| Variável | Uso |
| --- | --- |
| `DB_BACKEND` | `sqlite` (padrão) ou `mysql` |
| `SQLITE_PATH` | Arquivo SQLite; padrão `data/festa.db`. Caminhos relativos partem da raiz do projeto |
| `MYSQL_HOST` | Host do MySQL |
| `MYSQL_PORT` | Porta; padrão `3306` |
| `MYSQL_DATABASE` | Banco previamente criado no servidor |
| `MYSQL_USER` | Usuário de acesso |
| `MYSQL_PASSWORD` | Senha; nunca inclua uma senha real no Git |
| `MYSQL_SSL_CA` | Caminho opcional do certificado CA para TLS verificado |

### SQLite

```dotenv
DB_BACKEND=sqlite
SQLITE_PATH=data/festa.db
```

O diretório e o arquivo são criados automaticamente. As chaves estrangeiras são habilitadas em cada conexão. As escritas usam `BEGIN IMMEDIATE` para que a validação e a gravação de escalas sejam serializadas entre sessões.

Os valores exatos são tratados como `Decimal` em Python. No SQLite, preços ficam armazenados em centavos inteiros e quantidades em inteiros multiplicados por 10000. O tipo SQLAlchemy faz a conversão automaticamente, sem utilizar `float`. Consultas SQL externas devem respeitar essas escalas.

### MySQL

Use MySQL 8.0.16 ou posterior, com InnoDB. Configure um servidor externo e crie o banco antes da primeira execução, por exemplo:

```sql
CREATE DATABASE festa_ifc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Crie pelo painel do provedor um usuário para esse banco com permissões de leitura, inserção, atualização, exclusão e criação inicial das tabelas. Configure rede, certificados e acesso conforme o provedor.

```dotenv
DB_BACKEND=mysql
MYSQL_HOST=mysql.example.com
MYSQL_PORT=3306
MYSQL_DATABASE=festa_ifc
MYSQL_USER=festa_app
MYSQL_PASSWORD=senha_ficticia_substitua
MYSQL_SSL_CA=/caminho/para/ca.pem
```

A senha de exemplo é fictícia. Se o provedor não exigir um arquivo CA, omita `MYSQL_SSL_CA`; se informado, a aplicação habilita validação do certificado e do hostname. O certificado precisa existir no ambiente de execução.

O driver é PyMySQL. A URL é construída por `URL.create`, aceitando caracteres especiais nas credenciais. Os mesmos modelos usam `NUMERIC(16, 2)` para preços e `NUMERIC(16, 4)` para quantidades em MySQL. Chaves estrangeiras usam `RESTRICT`. Bloqueios de linha no participante serializam as validações de escala no servidor; erros de concorrência provocam rollback e uma mensagem para tentar novamente.

Reinicie o processo Streamlit após trocar a configuração, porque a fábrica de sessões é armazenada em cache. Trocar de banco **não transfere os registros** do banco anterior.

## Streamlit Community Cloud

A publicação é uma etapa posterior: esta entrega não cria repositório remoto, não provisiona MySQL e não publica o sistema.

1. Hospede o MySQL externamente e obtenha os parâmetros de conexão. Configure a rede do provedor para permitir conexões da aplicação.
2. Envie o projeto a um repositório GitHub, incluindo `pyproject.toml`, `uv.lock`, `src/` e `.streamlit/config.toml`. Não envie `.env`, bancos locais ou `.streamlit/secrets.toml`.
3. Em [Streamlit Community Cloud](https://share.streamlit.io/), crie o aplicativo selecionando repositório, branch e o arquivo de entrada **src/app.py**. Selecione Python **3.12**.
4. Em **Advanced settings → Secrets** (ou nas configurações do aplicativo), cole o conteúdo de `.streamlit/secrets.example.toml` e substitua os valores fictícios. Mantenha as chaves no topo do TOML, sem seção `[mysql]`:

```toml
DB_BACKEND = "mysql"
MYSQL_HOST = "mysql.example.com"
MYSQL_PORT = "3306"
MYSQL_DATABASE = "festa_ifc"
MYSQL_USER = "festa_app"
MYSQL_PASSWORD = "substitua_pela_senha_real"
```

O Streamlit disponibiliza segredos TOML de primeiro nível como variáveis de ambiente, que esta aplicação já lê. Consulte a [documentação de segredos](https://docs.streamlit.io/develop/concepts/connections/secrets-management) e as [instruções de Secrets no Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

5. Publique. A inicialização cria as tabelas no banco configurado. O Community Cloud reconhece `uv.lock` como arquivo de dependências; consulte a [documentação de dependências](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
6. Verifique o cadastro e a persistência após reiniciar a aplicação.

Utilize o MySQL externo para persistência em produção. O arquivo SQLite local do servidor de hospedagem não é uma estratégia de armazenamento durável para essa implantação.

## Estrutura

```text
.
├── instrucoes.txt
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
├── .gitignore
├── README.md
├── .streamlit/
│   ├── config.toml
│   └── secrets.example.toml
└── src/
    ├── app.py
    ├── init_db.py
    ├── festa/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── database.py
    │   ├── errors.py
    │   ├── models.py
    │   ├── validation.py
    │   ├── services.py
    │   ├── planning.py
    │   └── ui/
    │       ├── __init__.py
    │       ├── common.py
    │       ├── catalogs.py
    │       ├── relations.py
    │       └── dashboard.py
    └── tests/
        ├── conftest.py
        ├── test_config.py
        ├── test_domain.py
        └── test_ui.py
```

`.env`, `.venv/` e `data/festa.db` são locais e ignorados pelo Git. Todo o código Python, inclusive os testes, está em `src/`.

A camada de serviços concentra as operações transacionais e validações; os modelos mapeiam as oito entidades; o planejamento usa dados simples. A interface mantém somente filtros, identificadores e valores dos formulários. Cada operação abre e fecha sua própria sessão; nenhuma sessão SQLAlchemy é guardada no estado da interface.

## Verificações

```powershell
uv run pytest
```

Os testes usam bancos SQLite temporários e cobrem cálculos com múltiplos alimentos/doadores, unidades distintas, déficits e excedentes, situações das doações, precisão monetária, persistência entre conexões, integridade referencial, rollback, restrições de unidade, duplicidade de composição, conflitos e limites de escala e duas gravações concorrentes.

Os testes de interface usam `streamlit.testing.v1.AppTest` para abrir as páginas, cadastrar/editar/excluir um alimento, exigir confirmação, registrar composições/doações/escalas e verificar bloqueios. A configuração e a compilação dos modelos para MySQL também são verificadas. Esses testes não substituem a validação de conexão com um servidor MySQL real no ambiente de produção.

## Limitações

- Uma única festa; sem autenticação, autorização por perfil ou trilha de auditoria. Quem tiver acesso ao aplicativo pode consultar e alterar os dados.
- Sem registro de vendas realizadas, pagamentos on-line, emissão fiscal, cálculo de lucro ou controle de despesas.
- Sem conversões de unidade, reserva de estoque ou movimentações individuais de entrega; cada doação mantém seu total recebido.
- Não há migrações automáticas: `create_all` cria tabelas ausentes, mas não altera estruturas existentes. Evoluções dos modelos exigirão uma migração planejada.
- A edição não tem controle de versão do registro; duas edições válidas do mesmo cadastro podem terminar com a última gravação prevalecendo. As regras de conflito de horários são verificadas dentro da transação.
- Backup e operação do banco de produção são responsabilidade da organização. O sistema não cria um servidor MySQL.
