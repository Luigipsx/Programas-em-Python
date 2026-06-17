from datetime import date
class Cliente:
    def __init__(self, nome, data_nascimento, cpf):
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf
    def __str__(self):
        return f'''
Nome do cliente: {self.nome}
Data de nascimento: {self.data_nascimento}
CPF: {self.cpf}
'''
    
class Prato:
    def __init__(self, nome, ingredientes, modo_preparo, preco):
        self.nome = nome
        self.ingredientes = ingredientes
        self.modo_preparo = modo_preparo
        self.preco = preco
    def __str__(self):
        return f'''
Nome do prato: {self.nome}
Ingredientes: {self.ingredientes}
Modo de preparo: {self.modo_preparo}
Preço: {self.nome}
'''

class Pedido:
    def __init__(self, data_pedido, percentual_desconto, valor_final, cliente, pratos):
        self.data_pedido = data_pedido
        self.percentual_desconto = percentual_desconto
        self.valor_final = valor_final
        self.cliente = cliente
        self.pratos = pratos
    def __str__(self):
        return f'''
Data: {self.data_pedido}
Percentual de desconto: 0.95
Valor final: {i * 0.95}
Cliente: {self.cliente}
Pratos: {self.pratos}
'''

c1 = Cliente("João", date(2024, 5, 2), "123456-78")

Ingredientes1 = ["ingrediente1", "ingrediente2", "ingrediente3", "ingrediente4", "ingrediente5", "ingrediente6"]
p1 = Prato("Macarrão", Ingredientes1, "coloque na panela e ligue o fogo", 5.50)
Ingredientes2 = ["ingrediente1", "ingrediente2", "ingrediente3", "ingrediente4", "ingrediente5", "ingrediente6"]
p2 = Prato("Macarrão", Ingredientes2, "coloque na panela e ligue o fogo", 6.50)
Ingredientes3 = ["ingrediente1", "ingrediente2", "ingrediente3", "ingrediente4", "ingrediente5", "ingrediente6"]
p3 = Prato("Macarrão", Ingredientes3, "coloque na panela e ligue o fogo", 7.50)
Ingredientes4 = ["ingrediente1", "ingrediente2", "ingrediente3", "ingrediente4", "ingrediente5", "ingrediente6"]
p4 = Prato("Macarrão", Ingredientes4, "coloque na panela e ligue o fogo", 8.50)
Pratos = [p1, p2, p3, p4]
i = 0
for p in Pratos:
    i = i + p.preco

Ped1 = Pedido(date(2024, 5, 3), 0.95, i * 0.95, c1, Pratos)
print(Ped1)