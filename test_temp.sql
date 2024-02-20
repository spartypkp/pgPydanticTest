 /* @nameselect_federal_rows */
SELECT * FROM us_federal_ecfr WHERE node_type = 'content_type' AND status is NULL LIMIT 5;