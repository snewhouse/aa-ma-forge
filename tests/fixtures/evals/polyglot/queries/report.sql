SELECT *
FROM visits v, patients p
WHERE v.patient_id = p.id
UNION
SELECT * FROM archived_visits;
