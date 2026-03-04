-- Insertar 40,000 transacciones adicionales en paytransit (últimos 6 meses)
INSERT INTO paytransit.transaction_records 
SELECT 
    number + 10001 AS transactionId,
    rand() % 50 + 1 AS cardId,
    arrayElement(['BOARDING', 'TRANSFER', 'RELOAD'], rand() % 3 + 1) AS transactionType,
    CAST((rand() % 10 + 1) / 2.0 AS Decimal(10,2)) AS amount,
    now() - toIntervalDay(rand() % 180) - toIntervalHour(rand() % 24) - toIntervalMinute(rand() % 60) AS transactionTime,
    concat('V', toString(rand() % 50 + 1)) AS vehicleId,
    concat('R00', toString(rand() % 10 + 1)) AS routeId
FROM numbers(40000);
