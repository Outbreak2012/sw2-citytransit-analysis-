// Script para poblar MongoDB con 100,000 feedbacks
const feedbacks = [];

const categorias = ['Servicio', 'Puntualidad', 'Limpieza', 'Conductor', 'Precio', 'Comodidad', 'Seguridad', 'Frecuencia', 'Rutas', 'App'];
const rutas = ['Ruta 1 - Centro', 'Ruta 2 - Villa 1ro de Mayo', 'Ruta 3 - Plan 3000', 'Ruta 4 - Equipetrol', 'Ruta 5 - Urubó', 
               'Ruta 6 - Pampa de la Isla', 'Ruta 7 - Los Lotes', 'Ruta 8 - Satélite Norte', 'Ruta 9 - Warnes', 'Ruta 10 - Cotoca'];

const comentariosPositivos = [
    "Excelente servicio, muy puntual",
    "El conductor fue muy amable y profesional",
    "Bus limpio y cómodo, recomendado",
    "Precio justo por el servicio",
    "Llegué a tiempo a mi destino",
    "Muy buena experiencia de viaje",
    "El aire acondicionado funciona perfecto",
    "Asientos cómodos y espaciosos",
    "El chofer maneja con cuidado",
    "App muy fácil de usar para pagar",
    "Frecuencia de buses excelente",
    "Nunca he tenido problemas",
    "Siempre llegan a la hora indicada",
    "Personal muy atento y servicial",
    "Me encanta el servicio de PayTransit",
    "Transporte seguro y confiable",
    "Buena relación calidad-precio",
    "Los buses están en buen estado",
    "Excelente cobertura de rutas",
    "Sistema de pago muy conveniente"
];

const comentariosNegativos = [
    "El bus llegó muy tarde",
    "Demasiado lleno, incómodo",
    "El aire acondicionado no funcionaba",
    "El conductor fue grosero",
    "Precio muy alto para el servicio",
    "Bus sucio y mal mantenido",
    "Tardó mucho en pasar",
    "Mala experiencia, no lo recomiendo",
    "El chofer manejaba muy rápido",
    "No respetan las paradas",
    "Tuve que esperar más de 30 minutos",
    "Pésimo servicio al cliente",
    "Los asientos están rotos",
    "No hay suficientes buses en hora pico",
    "El cobrador fue irrespetuoso",
    "Siempre hay retrasos en esta ruta",
    "Bus en malas condiciones",
    "No dan cambio correctamente",
    "Muy inseguro en la noche",
    "La app falló al momento de pagar"
];

const comentariosNeutrales = [
    "Servicio normal, nada especial",
    "Llegué a mi destino sin problemas",
    "El bus estaba regular",
    "Ni bueno ni malo, cumple su función",
    "Podría mejorar pero está bien",
    "Servicio estándar de transporte",
    "Sin comentarios particulares",
    "Transporte básico pero funcional",
    "Experiencia promedio",
    "Cumple con lo esperado"
];

// Generar 100,000 feedbacks
for (let i = 0; i < 100000; i++) {
    // Distribución: 45% positivo, 35% negativo, 20% neutral
    const rand = Math.random();
    let sentimiento, comentarios, confidence;
    
    if (rand < 0.45) {
        sentimiento = 'POSITIVO';
        comentarios = comentariosPositivos;
        confidence = 0.75 + Math.random() * 0.2;
    } else if (rand < 0.80) {
        sentimiento = 'NEGATIVO';
        comentarios = comentariosNegativos;
        confidence = 0.70 + Math.random() * 0.25;
    } else {
        sentimiento = 'NEUTRO';
        comentarios = comentariosNeutrales;
        confidence = 0.60 + Math.random() * 0.2;
    }
    
    // Fecha aleatoria en los últimos 90 días
    const diasAtras = Math.floor(Math.random() * 90);
    const horasAtras = Math.floor(Math.random() * 24);
    const fecha = new Date();
    fecha.setDate(fecha.getDate() - diasAtras);
    fecha.setHours(fecha.getHours() - horasAtras);
    
    const prioridad = sentimiento === 'NEGATIVO' ? Math.floor(Math.random() * 3) + 3 : Math.floor(Math.random() * 3) + 1;
    
    feedbacks.push({
        usuario_id: Math.floor(Math.random() * 10000) + 1,
        categoria: categorias[Math.floor(Math.random() * categorias.length)],
        ruta_nombre: rutas[Math.floor(Math.random() * rutas.length)],
        comentario: comentarios[Math.floor(Math.random() * comentarios.length)],
        sentimiento: sentimiento,
        confidence_score: parseFloat(confidence.toFixed(2)),
        prioridad: prioridad,
        created_at: fecha,
        procesado: true
    });
}

// Limpiar colección existente e insertar nuevos datos
db.user_feedback.drop();
db.user_feedback.insertMany(feedbacks);

print("Insertados " + feedbacks.length + " feedbacks");
print("Positivos: " + feedbacks.filter(f => f.sentimiento === 'POSITIVO').length);
print("Negativos: " + feedbacks.filter(f => f.sentimiento === 'NEGATIVO').length);
print("Neutrales: " + feedbacks.filter(f => f.sentimiento === 'NEUTRO').length);
