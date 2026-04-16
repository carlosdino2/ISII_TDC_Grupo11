function buscar() {
    alert('Función de búsqueda próximamente disponible...');
}

function registrarUsuario(){
    alert('Función de registrarse próximamente disponible...');
}

function login(){
    alert('Función de iniciar sesion próximamente disponible...');
}

//buscar alojamientos
const destinoInput = document.getElementById('destino');
const sugerenciasContainer = document.getElementById('sugerencias');
let destinos = [];

fetch(DESTINOS_API_URL)
  .then(response => response.json())
  .then(data => {
    destinos = data;
  });

//filtra por la palabra que comienza con lo que escribe el usuario, ignora acentos, mayúsculas y símbolos

function normalizarTexto(texto) {
    return texto.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }
  
  destinoInput.addEventListener('input', function () {
    const input = normalizarTexto(destinoInput.value);
    sugerenciasContainer.innerHTML = '';
  
    if (input.length === 0) return;
  
    const sugerenciasFiltradas = destinos.filter(destino => {
      return (
        normalizarTexto(destino.localidad).startsWith(input) ||
        normalizarTexto(destino.provincia).startsWith(input) ||
        normalizarTexto(destino.pais).startsWith(input)
      );
    });
  
    sugerenciasFiltradas.forEach(destino => {
      const item = document.createElement('div');
      item.textContent = `${destino.localidad}, ${destino.provincia}, ${destino.pais}`;
      item.classList.add('sugerencia-item');
      item.addEventListener('click', function () {
        destinoInput.value = `${destino.localidad}, ${destino.provincia}, ${destino.pais}`;
        sugerenciasContainer.innerHTML = '';
      });
      sugerenciasContainer.appendChild(item);
    });
  });
  
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.autocomplete-container')) {
      sugerenciasContainer.innerHTML = '';
    }
  });

