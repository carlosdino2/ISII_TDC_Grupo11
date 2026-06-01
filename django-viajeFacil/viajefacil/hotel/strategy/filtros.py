from abc import ABC, abstractmethod
#clase abstracta
class EstrategiaFiltro(ABC):
    @abstractmethod
    def filtrar(self, vuelos):
        pass
#filtros segun la estrategia
class FiltroMasBaratos(EstrategiaFiltro):
    def filtrar(self, vuelos):
        return sorted(vuelos, key=lambda x: x['precio_unitario'])

class FiltroMasRapidos(EstrategiaFiltro):
    def filtrar(self, vuelos):
        return sorted(vuelos, key=lambda x: x['duracion_minutos'])

class FiltroRecomendados(EstrategiaFiltro):
    def filtrar(self, vuelos):
        return sorted(vuelos, key=lambda x: (x['precio_unitario'], x['duracion_minutos']))
