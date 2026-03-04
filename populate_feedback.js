// Generar datos de feedback de usuarios
const feedbacks = [];
const tipos = ['servicio', 'conductor', 'limpieza', 'puntualidad', 'seguridad', 'tarjeta', 'app'];
const rutas = ['R001', 'R002', 'R003', 'R004', 'R005'];
const comentariosPositivos = ['Excelente servicio', 'Muy puntual', 'Conductor amable', 'Limpio y ordenado', 'Buena experiencia', 'Todo perfecto', 'Recomendado'];
const comentariosNegativos = ['Muy lleno', 'Llego tarde', 'Sucio', 'Conductor grosero', 'Mala experiencia', 'Demasiada espera', 'No funciona bien'];

for (let i = 0; i < 500; i++) {
  const rating = Math.floor(Math.random() * 5) + 1;
  const comentario = rating >= 4 ? comentariosPositivos[Math.floor(Math.random() * comentariosPositivos.length)] : comentariosNegativos[Math.floor(Math.random() * comentariosNegativos.length)];
  feedbacks.push({
    usuario_id: Math.floor(Math.random() * 50) + 1,
    tipo_feedback: tipos[Math.floor(Math.random() * tipos.length)],
    ruta_codigo: rutas[Math.floor(Math.random() * rutas.length)],
    comentario: comentario,
    rating: rating,
    sentiment_score: (rating - 3) / 2,
    timestamp: new Date(Date.now() - Math.floor(Math.random() * 30 * 24 * 60 * 60 * 1000)),
    procesado: true
  });
}
db.user_feedback.insertMany(feedbacks);
print('Insertados ' + feedbacks.length + ' feedbacks');
