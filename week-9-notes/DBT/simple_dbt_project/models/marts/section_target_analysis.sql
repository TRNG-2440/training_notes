SELECT
    s.SECTION,
    s.TOTAL_EVENTS,
    s.PURCHASE_COUNT,
    t.TARGET_EVENTS,
    t.TARGET_PURCHASES,
    CASE
        WHEN t.TARGET_EVENTS = t.TARGET_EVENTS 
        THEN 'TARGET MET'
        ELSE 'BELOW TARGET'
    END AS ENGEGEMENT_STATUS
    FROM {{ ref('section_performance') }} s
    LEFT JOIN {{ ref('product_targets') }} t
    ON s.SECTION = t.SECTION
