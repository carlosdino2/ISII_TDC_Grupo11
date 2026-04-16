// Simulación de datos desde el backend (Django en el futuro)
const hoteles = [
    {
      nombre: "Orfeo Suites Cordoba",
      tipo: "Habitación Doble",
      camas: "1 cama doble extragrande",
      noches: 24,
      adultos: 2,
      precio: 3118179,
      impuestos: 654818,
      imagen: STATIC_URL + "img/orfeo_suites.jpg"
    },
    {
      nombre: "Quinto Centenario Hotel",
      tipo: "Habitación Doble Clásica - 2 camas",
      camas: "2 camas individuales",
      noches: 24,
      adultos: 2,
      precio: 3321862,
      impuestos: 697591,
      imagen: STATIC_URL + "img/Quinto_Centenario_Hotel.jpg"
    }
];  
  
  const contenedor = document.getElementById('lista-hoteles');
  const totalHoteles = document.getElementById('total-hoteles');
  
  function renderHoteles() {
    contenedor.innerHTML = '';
    totalHoteles.textContent = hoteles.length;
  
    hoteles.forEach(hotel => {
      const card = document.createElement('div');
      card.className = 'hotel-card';
  
      card.innerHTML = `
        <img src="${hotel.imagen}" alt="${hotel.nombre}">
        <div class="hotel-info">
          <h3>${hotel.nombre}</h3>
          <p><strong>${hotel.tipo}</strong></p>
          <p>${hotel.camas}</p>
          <div class="hotel-detalles">
            <span>${hotel.noches} noches, ${hotel.adultos} adultos</span>
            <h4>$ ${hotel.precio.toLocaleString()}</h4>
            <small>+ $ ${hotel.impuestos.toLocaleString()} de impuestos y cargos</small>
          </div>
          <button class="ver-mas">Ver más</button>
        </div>
      `;
  
      contenedor.appendChild(card);
    });
  }
  
  renderHoteles();

function buscar() {
    alert('Función de búsqueda próximamente disponible...');
}

function registrarUsuario(){
    alert('Función de registrarse próximamente disponible...');
}

function login(){
    alert('Función de iniciar sesion próximamente disponible...');
}

const destinos = [
    "Buenos Aires",
    "Mar del Plata",
    "Río de Janeiro",
    "Bariloche",
    "Córdoba",
    "Mendoza",
    "Iguazú",
    "Salta",
    "Ushuaia"
];

const destinoInput = document.getElementById('destino');
const sugerenciasContainer = document.getElementById('sugerencias');

destinoInput.addEventListener('input', function() {
    const input = destinoInput.value.toLowerCase();
    sugerenciasContainer.innerHTML = '';

    if (input.length === 0) {
        return;
    }

    const sugerenciasFiltradas = destinos.filter(destino => 
        destino.toLowerCase().includes(input)
    );

    sugerenciasFiltradas.forEach(destino => {
        const item = document.createElement('div');
        item.textContent = destino;
        item.classList.add('sugerencia-item');
        item.addEventListener('click', function() {
            destinoInput.value = destino;
            sugerenciasContainer.innerHTML = '';
        });
        sugerenciasContainer.appendChild(item);
    });
});

document.addEventListener('click', function(e) {
    if (!e.target.closest('.autocomplete-container')) {
        sugerenciasContainer.innerHTML = '';
    }
});
  