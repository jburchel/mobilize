-- Check pipeline data for dashboard charts

-- Check main pipelines
SELECT id, name, pipeline_type, is_main_pipeline, office_id
FROM pipelines
WHERE is_main_pipeline = TRUE;

-- Check pipeline stages for people pipeline
SELECT ps.id, ps.name, ps.color, ps.pipeline_id, ps.order, COUNT(pc.id) as contact_count
FROM pipeline_stages ps
LEFT JOIN pipeline_contacts pc ON ps.id = pc.current_stage_id
WHERE ps.pipeline_id IN (
    SELECT id FROM pipelines WHERE pipeline_type IN ('person', 'people') AND is_main_pipeline = TRUE
)
GROUP BY ps.id, ps.name, ps.color, ps.pipeline_id, ps.order
ORDER BY ps.order;

-- Check pipeline stages for church pipeline
SELECT ps.id, ps.name, ps.color, ps.pipeline_id, ps.order, COUNT(pc.id) as contact_count
FROM pipeline_stages ps
LEFT JOIN pipeline_contacts pc ON ps.id = pc.current_stage_id
WHERE ps.pipeline_id IN (
    SELECT id FROM pipelines WHERE pipeline_type = 'church' AND is_main_pipeline = TRUE
)
GROUP BY ps.id, ps.name, ps.color, ps.pipeline_id, ps.order
ORDER BY ps.order;
