-- YOU CAN USE ANY OF THESE QUERIES FOR THEIR RESPECTIVE ATS WEBSITES


-- GREENHOUSE.IO
SELECT DISTINCT
    -- EXTRACT SLUGS
    lower(regexp_extract(url_path, '^/([A-Za-z0-9_-]+)', 1)) AS slug
FROM "ccindex"."ccindex"
WHERE 
    -- SEARCH LAST SIX CRAWLS (LAST SIX MONTHS)
    crawl IN ('CC-MAIN-2026-39', 'CC-MAIN-2026-34', 'CC-MAIN-2026-30', 
            'CC-MAIN-2026-25', 'CC-MAIN-2026-21', 'CC-MAIN-2026-17')
    AND subset = 'warc'
    AND fetch_status = 200
    -- ONLY FOR THE FOLLOWING URL HOST NAMES
    AND url_host_name IN ('job-boards.greenhouse.io', 'boards.greenhouse.io')
ORDER BY slug;