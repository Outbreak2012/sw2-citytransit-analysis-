// Generar 5000 datos de feedback con sentimiento para analytics
db.user_feedback.drop();

const feedbacks = [];
const categorias = ['servicio', 'conductor', 'limpieza', 'puntualidad', 'seguridad', 'tarjeta', 'app'];
const rutas = ['R001', 'R002', 'R003', 'R004', 'R005', 'R006', 'R007', 'R008', 'R009', 'R010'];
const rutaNombres = {
    'R001': 'Linea Centro-Norte',
    'R002': 'Linea Sur Express', 
    'R003': 'Circuito Universitario',
    'R004': 'Linea Industrial',
    'R005': 'Ruta Aeropuerto',
    'R006': 'Circuito Historico',
    'R007': 'Linea Este-Oeste',
    'R008': 'Ruta Residencial Norte',
    'R009': 'Expreso Centro Medico',
    'R010': 'Linea Nocturna'
};

const comentariosPositivos = [
    'Excelente servicio, muy puntual y limpio',
    'El conductor fue muy amable y profesional',
    'Muy satisfecho con el viaje, todo perfecto',
    'Buena experiencia, lo recomiendo totalmente',
    'Servicio de primera calidad, siempre a tiempo',
    'Me encanta usar este transporte, muy comodo',
    'Rapido y eficiente, excelente atencion',
    'El bus estaba limpio y el conductor fue atento',
    'Perfecto, cumplio con todas mis expectativas',
    'Genial experiencia de viaje, muy recomendado',
    'Servicio impecable, seguire usandolo',
    'Todo excelente desde el inicio hasta el final',
    'Muy comodo el viaje y puntual',
    'Fantastico servicio al cliente',
    'Los mejores buses de la ciudad'
];

const comentariosNegativos = [
    'El bus llego 30 minutos tarde, muy mal',
    'Demasiado lleno, viaje muy incomodo',
    'El conductor fue grosero y descortes',
    'Sucio el transporte, da asco',
    'Mala experiencia, no lo recomiendo',
    'Demasiada espera en la parada',
    'La tarjeta no funciono correctamente',
    'Muy lento el servicio, perdi tiempo',
    'El aire acondicionado no funcionaba',
    'Bus viejo y en mal estado',
    'Pesimo servicio, nunca mas',
    'Los asientos estaban rotos',
    'No respetan los horarios',
    'Conductor manejaba muy mal',
    'Tuve que esperar mas de una hora'
];

const comentariosNeutros = [
    'Servicio normal, nada especial que comentar',
    'Cumplio con lo basico esperado',
    'Regular el servicio en general',
    'Ni bueno ni malo, aceptable',
    'Esperaba algo mejor pero estuvo bien',
    'Normal, sin inconvenientes',
    'El viaje fue sin problemas',
    'Servicio estandar del dia a dia',
    'Cumplio su funcion basica',
    'Nada destacable, servicio promedio'
];

// Generar 5000 feedbacks
for (let i = 0; i < 5000; i++) {
    const sentimientoIdx = Math.random();
    let sentimiento, comentario, prioridad, confidence, rating;
    
    // Distribucion: 40% positivo, 25% negativo, 35% neutro
    if (sentimientoIdx < 0.40) {
        sentimiento = 'POSITIVE';
        comentario = comentariosPositivos[Math.floor(Math.random() * comentariosPositivos.length)];
        prioridad = Math.floor(Math.random() * 2) + 1; // 1-2
        confidence = 0.75 + Math.random() * 0.20;
        rating = Math.floor(Math.random() * 2) + 4; // 4-5
    } else if (sentimientoIdx < 0.65) {
        sentimiento = 'NEGATIVE';
        comentario = comentariosNegativos[Math.floor(Math.random() * comentariosNegativos.length)];
        prioridad = Math.floor(Math.random() * 2) + 4; // 4-5
        confidence = 0.70 + Math.random() * 0.25;
        rating = Math.floor(Math.random() * 2) + 1; // 1-2
    } else {
        sentimiento = 'NEUTRAL';
        comentario = comentariosNeutros[Math.floor(Math.random() * comentariosNeutros.length)];
        prioridad = 3;
        confidence = 0.55 + Math.random() * 0.25;
        rating = 3;
    }
    
    const rutaCodigo = rutas[Math.floor(Math.random() * rutas.length)];
    const diasAtras = Math.floor(Math.random() * 180); // Ultimos 6 meses
    
    feedbacks.push({
        usuario_id: Math.floor(Math.random() * 55) + 1,
        categoria: categorias[Math.floor(Math.random() * categorias.length)],
        route_id: rutaCodigo,
        ruta_nombre: rutaNombres[rutaCodigo],
        comentario: comentario,
        sentiment: sentimiento,
        sentimiento: sentimiento,
        confidence_score: Math.round(confidence * 100) / 100,
        rating: rating,
        prioridad: prioridad,
        timestamp: new Date(Date.now() - diasAtras * 24 * 60 * 60 * 1000),
        created_at: new Date(Date.now() - diasAtras * 24 * 60 * 60 * 1000),
        procesado: true,
        source: 'app_movil'
    });
}

// Insertar en lotes de 1000
const batchSize = 1000;
for (let i = 0; i < feedbacks.length; i += batchSize) {
    const batch = feedbacks.slice(i, i + batchSize);
    db.user_feedback.insertMany(batch);
    print('Insertados ' + (i + batch.length) + ' de ' + feedbacks.length);
}

// Crear indices para optimizar consultas
db.user_feedback.createIndex({timestamp: -1});
db.user_feedback.createIndex({route_id: 1});
db.user_feedback.createIndex({sentiment: 1});
db.user_feedback.createIndex({categoria: 1});
db.user_feedback.createIndex({rating: 1});

print('');
print('========================================');
print('POBLACION MONGODB COMPLETADA');
print('========================================');
print('Total documentos: ' + db.user_feedback.countDocuments({}));
print('Positivos: ' + db.user_feedback.countDocuments({sentiment: 'POSITIVE'}));
print('Negativos: ' + db.user_feedback.countDocuments({sentiment: 'NEGATIVE'}));
print('Neutros: ' + db.user_feedback.countDocuments({sentiment: 'NEUTRAL'}));
print('========================================');
