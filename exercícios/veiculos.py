class Veiculo:
    def __init__(self, placa, ano):
        self.placa = placa
        self.ano = ano
    def __str__(self):
        return f'''
Placa: {self.placa}
Ano: {self.ano}
'''

class Moto(Veiculo):
    def __init__(self, placa, ano):
        super().__init__(placa, ano)


class Caminhao(Veiculo):
    def __init__(self, placa, ano, peso_em_kg):
        super().__init__(placa, ano)
        self.peso_em_kg = peso_em_kg
    def __str__(self):
        return f'''
Placa: {self.placa}
Ano: {self.ano}
Peso: {self.peso_em_kg}
'''
m1 = Moto("NJVBS-990", 2000)
c1 = Caminhao("AAAA-111", 2020, 78)
print(m1, c1)