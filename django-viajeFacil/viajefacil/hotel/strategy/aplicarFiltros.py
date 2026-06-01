#contexto de la estrategia
class AplicarFiltrosContexto:
    def __init__(self, estrategia):
        self.estrategia = estrategia

    def set_estrategia(self, estrategia):
        self.estrategia = estrategia

    def aplicar_filtro(self, vuelos):
        return self.estrategia.filtrar(vuelos)
