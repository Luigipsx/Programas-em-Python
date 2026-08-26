# Pony com sqlite e mysql

## Exemplo 01

Execução: 

```uv run exemplo01_sqlite.py```

Ao executar esse arquivo, será criado (se já não existir) um arquivo do SQLite chamado **pessoas.db**.

## Exemplo 02

Execução:

```uv run --env-file .env exemplo02_mysql.py```

### Variáveis de ambiente (exemplo02)

Para se conectar ao Mysql, é preciso usar variáveis de ambiente, para que a senha e outras informações não fiquem armazenadas dentro do programa. Em vez de definir variáveis de ambiente no terminal, é possível criar um arquivo chamado ".env" com as variáveis definidas. Modifique os valores conforme sua necessidade de conexão a banco de dados:

```
DATABASE_NAME=info2026emi
DATABASE_HOST=10.10.34.100
DATABASE_USER=root
DATABASE_PASSWORD=root
DATABASE_PORT=3306
```

Portanto, lembre-se de:
<ol type="A">
<li>Alterar os valores das variáveis de ambiente dentro do arquivo .env</li>
<li>Adicionar ao .gitignore o arquivo .env, para que esse arquivo NÃO SEJA ENVIADO ao repositório (ele contém informações sensíveis)</li>