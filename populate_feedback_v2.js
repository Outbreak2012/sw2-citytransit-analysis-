// Generar datos de feedback con el formato correcto para el servicio de analytics
db.user_feedback.drop();

const feedbacks = [];
const categorias = ['servicio', 'conductor', 'limpieza', 'puntualidad', 'seguridad', 'tarjeta', 'app'];
const rutas = ['Linea Centro-Norte', 'Linea Sur Express', 'Circuito Universitario', 'Linea Industrial', 'Ruta Aeropuerto'];
const sentimientos = ['POSITIVE', 'NEGATIVE', 'NEUTRAL'];

const comentariosPositivos = [
    'Excelente servicio, muy puntual',
    'El conductor fue muy amable y atento',
    'Muy limpio y ordenado el transporte',
    'Buena experiencia de viaje',
    'Todo perfecto, recomendado',
    'Servicio de primera calidad',
    'Muy satisfecho con el servicio',
    'Rapido y eficiente el recorrido'
];

const comentariosNegativos = [
    'El bus llego muy tarde',
    'Demasiado lleno, incomodo',
    'El conductor fue grosero',
    'Sucio el transporte',
    'Mala experiencia, no recomiendo',
    'Demasiada espera en la parada',
    'La tarjeta no funciono bien',
    'Muy lento el servicio'
];

const comentariosNeutros = [
    'Servicio normal, nada especial',
    'Cumplio con lo basico',
    'Regular el servicio',
    'Ni bueno ni malo',
    'Esperaba algo mejor pero estuvo bien'
];

for (let i = 0; i < 500; i++) {
    const sentimientoIdx = Math.random();
    let sentimiento, comentario, prioridad, confidence;
    
    if (sentimientoIdx < 0.45) {
        sentimiento = 'POSITIVE';
        comentario = comentariosPositivos[Math.floor(Math.random() * comentariosPositivos.length)];
        prioridad = Math.floor(Math.random() * 2) + 1;
        confidence = 0.75 + Math.random() * 0.2;
    } else if (sentimientoIdx < 0.75) {
        sentimiento = 'NEGATIVE';
        comentario = comentariosNegativos[Math.floor(Math.random() * comentariosNegativos.length)];
        prioridad = Math.floor(Math.random() * 2) + 4;
        confidence = 0.70 + Math.random() * 0.25;
    } else {
        sentimiento = 'NEUTRAL';
        comentario = comentariosNeutros[Math.floor(Math.random() * comentariosNeutros.length)];
        prioridad = 3;
        confidence = 0.60 + Math.random() * 0.2;
    }
    
    feedbacks.push({
        usuario_id: Math.floor(Math.random() * 50) + 1,
        categoria: categorias[Math.floor(Math.random() * categorias.length)],
        ruta_nombre: rutas[Math.floor(Math.random() * rutas.length)],
        comentario: comentario,
        sentimiento: sentimiento,
        confidence_score: Math.round(confidence * 100) / 100,
        prioridad: prioridad,
        created_at: new Date(Date.now() - Math.floor(Math.random() * 7 * 24 * 60 * 60 * 1000)),
        procesado: true
    });
}

db.user_feedback.insertMany(feedbacks);
print('✅ Insertados ' + feedbacks.length + ' feedbacks con formato correcto');
print('📊 Verificando...');
print('Total documentos: ' + db.user_feedback.countDocuments({}));
print('Con created_at: ' + db.user_feedback.countDocuments({created_at: {$exists: true}}));
print('Positivos: ' + db.user_feedback.countDocuments({sentimiento: 'POSITIVE'}));
print('Negativos: ' + db.user_feedback.countDocuments({sentimiento: 'NEGATIVE'}));
print('Neutros: ' + db.user_feedback.countDocuments({sentimiento: 'NEUTRAL'}));
