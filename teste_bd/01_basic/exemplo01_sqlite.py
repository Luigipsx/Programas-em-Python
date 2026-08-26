# importações
from pony.orm import *
import os # comandos do sistema operacional

# criando variável de acesso ao pony
db = Database()

# definição da classe: 
# é preciso herdar da classe Entity
class Pessoa(db.Entity):
    nome = Required(str)   # atributo string obrigatório
    email = Required(str, 100)  # atributo string obrigatório com máximo de 100 caracteres
    telefone = Optional(str, nullable=True) # atributo opcional
    cpf = Required(str, 11) 

# usando o banco de dados SQLite
db.bind(provider='sqlite', filename='pessoas.db', create_db=True)

# innformando que deve criar as tabelas, caso não existam
db.generate_mapping(create_tables=True)

# solicitando para mostrar os comandos SQL que vão sendo executados
set_sql_debug(True)

# iniciando uma sessão
with db_session:

    # criando uma pessoa
    jo = Pessoa(nome='João da Silva', email='josilva@gmail.com', cpf='000000000')

    # salvando
    commit()

    # exibindo os dados
    print(jo.nome, jo.email)
    
    # existe um ID?
    print(jo.id)

'''
Exercícios:

1) Confira os outros tipos de dados em:
https://docs.ponyorm.org/entities.html#attribute-data-types

2) Pergunte em alguma IA porque o comando "print(jo.id)" funciona neste código,
já que não existe o campo "id" declarado na classe

3) Descomente a linha 22 e execute novamente o programa, para ver
os códigos SQL que estão sendo executados

4) Abra o arquivo "pessoas.db" no DBeaver e visualize a tabela e os dados

'''