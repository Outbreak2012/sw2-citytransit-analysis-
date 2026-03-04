-- Insertar datos de transacciones para ClickHouse (últimos 30 días)
-- Esto simula pasajeros usando el sistema de transporte

INSERT INTO transaction_records 
SELECT 
    number + 1 AS transactionId,
    rand() % 5000 + 1 AS cardId,
    arrayElement(['BOARDING', 'TRANSFER', 'RELOAD'], rand() % 3 + 1) AS transactionType,
    CAST((rand() % 10 + 1) / 2.0 AS Decimal(10,2)) AS amount,
    now() - toIntervalDay(rand() % 30) - toIntervalHour(rand() % 24) - toIntervalMinute(rand() % 60) AS transactionTime,
    concat('V', toString(rand() % 50 + 1)) AS vehicleId,
    concat('R', toString(rand() % 10 + 1)) AS routeId
FROM numbers(10000);
