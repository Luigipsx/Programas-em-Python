class Pessoa:
    def __init__(self, nome, telefone, data_nascimento):
        self.nome = nome
        self.telefone = telefone
        self.data_nascimento = data_nascimento

    def __str__(self):
        return f'''
Nome: {self.nome}
Telefone: {self.telefone}
Data de Nascimento: {self.data_nascimento}
'''

class Cliente:
    def __init__(self, pessoa, email):
        self.pessoa = pessoa
        self.email = email
    
    def __str__(self):
        return f'''
DADOS DO CLIENTE: {self.pessoa}Email: {self.email}
'''

class Mecanico:
    def __init__(self, pessoa):
        self.pessoa = pessoa

    def __str__(self):
        return f'''
DADOS DO MECÃNICO:{self.pessoa}
'''

class Servico:
    def __init__(self, descricao, valor):
        self.descricao = descricao
        self.valor = valor

    def __str__(self):
        return f'''
Serviços: {self.descricao}
Valor: {self.valor}
'''

class ServicoRealizado:
    def __init__(self, servico, mecanico):
        self.servico = servico
        self.mecanico = mecanico

    def __str__(self):
        return f'''
{self.servico}
{self.mecanico}
'''

class OrdemServico:
    def __init__(self, cliente, veiculo,  data_entrada, data_saida, valor):
        self.cliente = cliente
        self.veiculo = veiculo
        self.data_entrada = data_entrada
        self.data_saida = data_saida
        self.valor = valor

    def __str__(self):
        return f'''
{self.cliente}
{self.veiculo}
Data de entrada: {self.data_entrada}
Data de saída: {self.data_saida}
Desconto aplicado: 5%
Valor final: R${self.valor * 0.95}
'''
class Veiculo:
    def __init__(self, placa, cor):
        self.placa = placa
        self.cor = cor

    def __str__(self):
        return f'''
DADOS DO VEÍCULO: 
Placa: {self.placa}
Cor: {self.cor}
'''

class VeiculoComPassageiros(Veiculo):
    def __init__(self, lugares, placa, cor):
        super().__init__(placa, cor)
        self.lugares = lugares

class Moto(Veiculo):
    def __init__(self, placa, cor):
        super().__init__(placa, cor)

class Carro(VeiculoComPassageiros):
    def __init__(self, lugares, placa, cor):
        super().__init__(lugares, placa, cor)

class Onibus(VeiculoComPassageiros):
    def __init__(self, lugares, placa, cor):
        super().__init__(lugares, placa, cor)


#TESTE DE CLASSE
pessoa1 = Pessoa("João Silva", "99999-9999", "01/01/1990")
cliente1 = Cliente(pessoa1, "joao@gmail.com")
pessoa2 = Pessoa("Carlos", "1234-5678", "05/05/1985")
mecanico1 = Mecanico(pessoa2)
carro1 = Carro(4, "KJNVKN-859NN", "Branco")
moto1 = Moto("XYZ-9999", "Vermelha")
onibus1 = Onibus("45","VJVDJV-85HN", "Amarelo")
servico1 = Servico("Troca de óleo", 150.0)
servico_realizado1 = ServicoRealizado(servico1, mecanico1)
ordem1 = OrdemServico(cliente1, carro1, "01/04/2026", "02/04/2026", 150)

print(servico_realizado1)
print(ordem1)