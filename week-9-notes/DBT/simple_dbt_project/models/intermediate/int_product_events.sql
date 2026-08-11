SELECT
    e.EVENT_ID,
    e.EVENT_TIMESTAMP,
    E.USER_ID,
    E.ACTION,
    p.PRODUCT_ID,
    P.DESCRIPTION,
    P.COLOR,
    P.SECTION
FROM {{ ref('stg_events') }} AS e
INNER JOIN {{ ref('stg_products') }} AS p    
    ON e.PRODUCT_ID = p.PRODUCT_ID
