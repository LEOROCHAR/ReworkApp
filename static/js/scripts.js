document.addEventListener('DOMContentLoaded', function() {
    const agregarParteBtn = document.getElementById('agregar-parte');
    const detallesPartesDiv = document.getElementById('detalles-partes');

    if (agregarParteBtn && detallesPartesDiv) {
        agregarParteBtn.addEventListener('click', function() {
            const nuevaParteDiv = document.createElement('div');
            nuevaParteDiv.innerHTML = `
                <label>Material:</label> <input type="text" name="material">
                <label>Calibre:</label> <input type="text" name="calibre">
                <label>Cantidad:</label> <input type="number" name="cantidad">
            `;
            detallesPartesDiv.appendChild(nuevaParteDiv);
        });
    }
});our project