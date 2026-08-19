import mysql.connector # biblioteca para trabalhar com MySQL
import sys # bibliotecas do sistema operacional
import os

# variáveis de ambiente: configurar no TERMINAL
HOST = os.getenv("DATABASE_HOST", "localhost") 
USER = os.getenv("DATABASE_USER", "root") 
PASSWORD = os.getenv("DATABASE_PASSWORD", "root") 
PORT = os.getenv("DATABASE_PORT", "3306")

# nomes das tabelas: ALTERAR o sufixo
TABELA_PESSOAS = "tbl_pessoas_hylson"
TABELA_CELULARES = "tbl_celulares_hylson"

DATABASE_NAME = "ifcblu2026" # nome do banco de dados utilizado

# definições da classe
class Pessoa:
    def __init__(self, id : int, nome : str, email : str):
        self.id = id
        self.nome = nome
        self.email = email
    def __str__(self):
        return f"(id:{self.id}), nome: {self.nome}, email: {self.email}"

# ------------------------------------
# tentar conectar-se ao banco de dados
# ------------------------------------
try:
    print(f'''Vou tentar conectar em:
    servidor: {HOST}, 
    usuário: {USER},
    senha: {PASSWORD},
    port: {PORT}''')

    conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        port=PORT
    )

    # criar um cursor para executar comandos SQL
    cursor = conn.cursor()

    # selecionar o banco de dados
    cursor.execute(f"USE {DATABASE_NAME}")      

    print("Banco de dados conectado :-)")
except Exception as erro:
     print(f"Não foi possível se conectar ao banco de dados: {erro}")
        # finaliza o programa
     sys.exit("Programa finalizado, verifique o erro")
    
# -----------------------
# tentar criar as tabelas
# -----------------------
try:
    cursor.execute(f'''
            CREATE TABLE {TABELA_PESSOAS} (
            id INT NOT NULL AUTO_INCREMENT,
            nome varchar(255) NOT NULL,
            email varchar(255) NOT NULL,
            PRIMARY KEY (id)
            );
    ''')
    
    # confirmar as alterações
    conn.commit()

    print("Tabelas criadas :-)")
except Exception as erro:
    print(f"Não foi possível criar as tabelas: {erro}")

# ----------------------------------------------------
# popular as tabelas (colocar alguns dados de exemplo)
# ----------------------------------------------------

# cadastrar duas pessoas
cursor.execute(f"INSERT INTO {TABELA_PESSOAS} VALUES (NULL, %s, %s)",
                ("João da Silva", "jo@gmail.com"))

cursor.execute(f"INSERT INTO {TABELA_PESSOAS} VALUES (NULL, %s, %s)",
                                ("Maria Oliveira", "maliv@gmail.com"))

# confirmar as alterações
conn.commit()

print("Pessoas incluídas com sucesso")

# -----------------
# listar as pessoas
# -----------------

# executar o comando SQL para selecionar todas as pessoas
cursor.execute(f'SELECT id, nome, email FROM {TABELA_PESSOAS}')

# obter os resultados da consulta
pessoas = cursor.fetchall()

# construção de uma lista de objetos em uma linha só!
pessoas_em_objetos = [Pessoa(*p) for p in pessoas]

for p in pessoas_em_objetos: 
    print(p)

print("Programa finalizado com sucesso")

''' Roteiro (use o PowerShell)

a) verifique se o "uv" está instalado, digite: uv

Se não estiver:
a1) Execute:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
a2) Feche o terminal e abra outro
a3) Teste a execução, digitando: uv

b) crie um projeto do "uv": uv init meuprojeto

c) entre na pasta: cd meuprojeto

d) adicione a biblioteca do mysql: uv add mysql-connector-python

e) baixe a biblioteca: uv sync

f) configure as variáveis de ambiente:

$env:DATABASE_HOST="aaaaaaa"
$env:DATABASE_USER="bbbbbb"
$env:DATABASE_PASSWORD="ccccccc"
$env:DATABASE_PORT="ddddddd"

Visualize e confira se as variáveis foram criadas:
echo $env:DATABASE_HOST
echo $env:DATABASE_USER
echo $env:DATABASE_PASSWORD
echo $env:DATABASE_PORT

g) execute o programa: uv run principal.py
'''
