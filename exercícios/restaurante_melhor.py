class Cliente:
    def __init__(self, nome, data_nascimento, cpf):
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf

class Prato:
    def __init__(self, nome, ingredientes, modo_preparo, preco):
        self.nome = nome
        self.ingredientes = ingredientes
        self.modo_preṕaro = modo_preparo
        self.preco = preco

class ItenDoPedido:
    def __init__(self, prato, valor_prato, quantidade):
        self.prato = prato
        self.valor_prato = valor_prato
        self.quantidade = quantidade

class Pedido:
    def __init__(self, data_Pedido, percentual_desconto, cliente, itens):
        self.data_pedido = data_Pedido
        self.percentual_desconto = percentual_desconto
        self.cliente = cliente
        self.itens = itens

#2-
#