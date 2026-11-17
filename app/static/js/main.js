// Archivo base de JavaScript / jQuery
$(document).ready(function() {
    console.log('Sistema de inventario cargado');

    // Auto-ocultar alertas después de 4 segundos
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 4000);
});
