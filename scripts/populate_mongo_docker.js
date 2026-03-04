// Script para poblar MongoDB con feedback sintético
// Ejecutar con: docker exec -i paytransit-mongodb mongosh < populate_mongo_docker.js

use citytransit;

// Comentarios positivos
const positiveComments = [
    "Excelente servicio, muy puntual y limpio. Lo recomiendo!",
    "El conductor fue muy amable y el bus llegó a tiempo.",
    "Genial experiencia, el bus estaba en perfectas condiciones.",
    "Muy buen servicio, rápido y eficiente. Felicitaciones!",
    "Me encanta usar este servicio, siempre es confiable.",
    "Perfecto! El horario se cumple y los buses son cómodos.",
    "Maravilloso servicio de transporte, seguiré usándolo.",
    "Todo excelente, desde el conductor hasta la limpieza del vehículo.",
    "Muy satisfecho con el servicio, puntual y seguro.",
    "Gran servicio! Los conductores son muy profesionales.",
    "El mejor transporte de la ciudad, sin duda.",
    "Impresionante la puntualidad y comodidad del servicio.",
    "Muy contento con la calidad del servicio ofrecido.",
    "Excelente atención y buses muy limpios.",
    "Servicio de primera, lo uso todos los días.",
    "Me siento seguro viajando en estos buses.",
    "Fantástico! Siempre llego a tiempo gracias a este servicio.",
    "Súper recomendado, excelente relación calidad-precio.",
    "Los conductores son muy amables y respetuosos.",
    "Buses modernos y en muy buen estado."
];

// Comentarios neutrales
const neutralComments = [
    "El servicio es normal, nada extraordinario.",
    "Cumple con lo esperado, sin problemas mayores.",
    "Es un servicio aceptable para el día a día.",
    "No tengo quejas pero tampoco destacaría algo especial.",
    "El bus llegó un poco tarde pero no fue grave.",
    "Servicio estándar, sin sorpresas.",
    "Todo bien, aunque podría mejorar en algunos aspectos.",
    "El viaje fue tranquilo, sin incidentes.",
    "Servicio adecuado, cumple su función.",
    "No está mal, aunque he visto mejores servicios.",
    "Es aceptable, aunque a veces hay retrasos menores.",
    "El bus estaba un poco lleno pero llegamos bien.",
    "Servicio regular, nada fuera de lo común.",
    "Está bien para el precio que se paga.",
    "El conductor hizo su trabajo normalmente.",
    "Sin problemas pero tampoco sobresale.",
    "Es un servicio promedio, ni bueno ni malo.",
    "Llegué a mi destino sin contratiempos.",
    "El bus podría estar más limpio pero está aceptable.",
    "Servicio común, nada destacable."
];

// Comentarios negativos
const negativeComments = [
    "Muy mal servicio, el bus llegó 30 minutos tarde.",
    "Pésima experiencia, el conductor fue grosero.",
    "El bus estaba sucio y en mal estado.",
    "Horrible servicio, nunca llegan a tiempo.",
    "Muy insatisfecho, demasiadas demoras.",
    "El peor servicio de transporte que he usado.",
    "Los buses están siempre llenos, incómodo.",
    "Mala experiencia, no lo recomiendo para nada.",
    "El conductor manejaba muy mal, sentí peligro.",
    "Servicio lento e ineficiente, una pérdida de tiempo.",
    "Nunca más uso este servicio, muy malo.",
    "Los buses están viejos y sucios.",
    "Mala atención por parte del conductor.",
    "Demasiados retrasos, no se puede confiar.",
    "El bus no pasó y tuve que esperar otro.",
    "Muy incómodo, no hay espacio para todos.",
    "Pésimo servicio al cliente, nadie responde quejas.",
    "Los horarios no se cumplen nunca.",
    "Decepcionante, esperaba mucho más.",
    "No vale lo que cuesta, muy mal servicio."
];

const sources = ["mobile_app", "web", "social_media"];
const categories = ["puntualidad", "limpieza", "conductor", "comodidad", "general"];

print("🚀 Iniciando población de MongoDB con feedback sintético...");

// Limpiar colección existente
db.user_feedback.drop();
print("✅ Colección limpiada");

// Generar 5000 documentos de feedback
const docs = [];
const numSamples = 5000;
const now = new Date();
const sixMonthsAgo = new Date(now.getTime() - (180 * 24 * 60 * 60 * 1000));

for (let i = 0; i < numSamples; i++) {
    // Determinar sentimiento (40% positivo, 35% neutral, 25% negativo)
    const rand = Math.random();
    let sentiment, rating, text;
    
    if (rand < 0.40) {
        sentiment = "POSITIVE";
        rating = Math.floor(Math.random() * 2) + 4; // 4-5
        text = positiveComments[Math.floor(Math.random() * positiveComments.length)];
    } else if (rand < 0.75) {
        sentiment = "NEUTRAL";
        rating = 3;
        text = neutralComments[Math.floor(Math.random() * neutralComments.length)];
    } else {
        sentiment = "NEGATIVE";
        rating = Math.floor(Math.random() * 2) + 1; // 1-2
        text = negativeComments[Math.floor(Math.random() * negativeComments.length)];
    }
    
    // Generar timestamp aleatorio en los últimos 6 meses
    const randomTime = sixMonthsAgo.getTime() + Math.random() * (now.getTime() - sixMonthsAgo.getTime());
    
    docs.push({
        user_id: Math.floor(Math.random() * 100) + 1,
        route_id: Math.floor(Math.random() * 10) + 1,
        text: text,
        rating: rating,
        sentiment: sentiment,
        confidence: Math.round((0.75 + Math.random() * 0.23) * 100) / 100,
        timestamp: new Date(randomTime),
        source: sources[Math.floor(Math.random() * sources.length)],
        category: categories[Math.floor(Math.random() * categories.length)],
        resolved: sentiment === "NEGATIVE" ? Math.random() > 0.5 : null
    });
    
    // Insertar en lotes de 1000
    if (docs.length >= 1000) {
        db.user_feedback.insertMany(docs);
        print(`   Insertados ${i + 1} documentos...`);
        docs.length = 0;
    }
}

// Insertar documentos restantes
if (docs.length > 0) {
    db.user_feedback.insertMany(docs);
}

print("✅ Feedback insertado exitosamente");

// Crear índices
db.user_feedback.createIndex({ timestamp: -1 });
db.user_feedback.createIndex({ route_id: 1 });
db.user_feedback.createIndex({ sentiment: 1 });
print("✅ Índices creados");

// Verificar resultados
const total = db.user_feedback.countDocuments();
const positive = db.user_feedback.countDocuments({ sentiment: "POSITIVE" });
const neutral = db.user_feedback.countDocuments({ sentiment: "NEUTRAL" });
const negative = db.user_feedback.countDocuments({ sentiment: "NEGATIVE" });

print("\n📊 Estadísticas de feedback:");
print(`   Total: ${total}`);
print(`   POSITIVE: ${positive} (${(positive/total*100).toFixed(1)}%)`);
print(`   NEUTRAL: ${neutral} (${(neutral/total*100).toFixed(1)}%)`);
print(`   NEGATIVE: ${negative} (${(negative/total*100).toFixed(1)}%)`);

// Crear metadata de modelos ML
db.ml_models.drop();
db.ml_models.insertMany([
    {
        model_name: "sentiment_analyzer",
        model_type: "BERT",
        version: "1.0.0",
        created_at: new Date(),
        updated_at: new Date(),
        status: "production",
        metrics: {
            accuracy: 0.92,
            f1_score: 0.89,
            precision: 0.91,
            recall: 0.87
        },
        hyperparameters: {
            learning_rate: 0.00002,
            epochs: 3,
            batch_size: 16
        },
        training_data: {
            samples: 50000,
            split_ratio: 0.8
        }
    },
    {
        model_name: "demand_predictor",
        model_type: "LSTM",
        version: "2.1.0",
        created_at: new Date(),
        updated_at: new Date(),
        status: "production",
        metrics: {
            mae: 12.5,
            rmse: 18.3,
            r2_score: 0.87,
            mape: 8.2
        },
        hyperparameters: {
            units: 128,
            layers: 3,
            dropout: 0.2,
            sequence_length: 168
        },
        training_data: {
            samples: 100000,
            features: 15
        }
    },
    {
        model_name: "user_segmentation",
        model_type: "DBSCAN",
        version: "1.2.0",
        created_at: new Date(),
        updated_at: new Date(),
        status: "production",
        metrics: {
            silhouette_score: 0.58,
            num_clusters: 5,
            outliers_percent: 8.5
        },
        hyperparameters: {
            eps: 0.5,
            min_samples: 5,
            metric: "euclidean"
        },
        training_data: {
            samples: 10000,
            features: 8
        }
    }
]);
print("✅ Metadata de modelos ML creada");

print("\n🎉 ¡Proceso completado exitosamente!");
