SELECT 
    PRODUCT_ID,
    DESCRIPTION,
    COLOR,
    SECTION,
    COUNT(*) AS TOTAL_EVENTS,
    COUNT(DISTINCT USER_ID) AS UNIQUE_USERS,
    SUM(
        CASE    
            WHEN ACTION = 'VIEW' THEN 1
            ELSE 0
        END
    ) AS VIEW_COUNT,
    SUM(
        CASE    
            WHEN ACTION = 'ADD_TO_CART' THEN 1
            ELSE 0
        END
    ) AS CART_COUNT,
    SUM(
        CASE    
            WHEN ACTION = 'PURCHASE' THEN 1
            ELSE 0
        END
    ) AS PURCHASE_COUNT
FROM {{ ref('int_product_events') }}
GROUP BY
    PRODUCT_ID,
    DESCRIPTION,
    COLOR,
    SECTION