-- YOU CAN USE ANY OF THESE QUERIES FOR THEIR RESPECTIVE ATS WEBSITES
-- IF A VALUE USES LOWER(), THAT MEANS IT IS NOT CASE SENSITIVE

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
    AND url_host_name = 'job-boards.greenhouse.io'
ORDER BY slug;

-- ASHBY
SELECT DISTINCT
    lower(regexp_extract(url_path, '^/([A-Za-z0-9_-]+)', 1)) AS slug
FROM "ccindex"."ccindex"
WHERE 
    crawl IN ('CC-MAIN-2026-39', 'CC-MAIN-2026-34', 'CC-MAIN-2026-30', 
            'CC-MAIN-2026-25', 'CC-MAIN-2026-21', 'CC-MAIN-2026-17')
    AND subset = 'warc'
    AND fetch_status = 200
    AND url_host_name = 'jobs.ashbyhq.com'
ORDER BY slug;

-- SMARTRECRUITERS
SELECT DISTINCT
    lower(regexp_extract(url_path, '^/([A-Za-z0-9_-]+)', 1) AS slug)
FROM "ccindex"."ccindex"
WHERE 
    crawl IN ('CC-MAIN-2026-39', 'CC-MAIN-2026-34', 'CC-MAIN-2026-30', 
            'CC-MAIN-2026-25', 'CC-MAIN-2026-21', 'CC-MAIN-2026-17')
    AND subset = 'warc'
    AND fetch_status = 200
    AND url_host_name IN ('careers.smartrecruiters.com', 'jobs.smartrecruiters.com')
ORDER BY slug;

-- RECRUITEE
SELECT DISTINCT
    regexp_extract(url_host_name, '^([a-z0-9-]+)\.recruitee\.com$', 1) AS slug
FROM "ccindex"."ccindex"
WHERE
    crawl IN ('CC-MAIN-2026-39', 'CC-MAIN-2026-34', 'CC-MAIN-2026-30', 
            'CC-MAIN-2026-25', 'CC-MAIN-2026-21', 'CC-MAIN-2026-17')
    AND subset = 'warc'
    AND fetch_status = 200
    AND url_host_registered_domain = 'recruitee.com'
ORDER BY slug;

-- BREEZYHR
SELECT DISTINCT
    regexp_extract(url_host_name, '^([a-z0-9-]+)\.breezy\.hr$', 1) AS slug
FROM "ccindex"."ccindex"
WHERE
    crawl IN ('CC-MAIN-2026-39', 'CC-MAIN-2026-34', 'CC-MAIN-2026-30', 
            'CC-MAIN-2026-25', 'CC-MAIN-2026-21', 'CC-MAIN-2026-17')
    AND subset = 'warc'
    AND fetch_status = 200
    AND url_host_registered_domain = 'breezy.hr'
ORDER BY slug;

-- WORKDAY
WITH q AS (
    SELECT DISTINCT
        -- we use the url here since the CommonCrawl URL Index gives AWS charges on data scanned, using less columns = less charge
        lower(regexp_extract(url, '^https://([A-Za-z0-9-]+)\.([A-Za-z0-9-]+)\.myworkdayjobs\.com/([A-Za-z0-9-_]+)$', 1)) AS company,
        lower(regexp_extract(url, '^https://([A-Za-z0-9-]+)\.([A-Za-z0-9-]+)\.myworkdayjobs\.com/([A-Za-z0-9-_]+)$', 2)) AS db,
        regexp_extract(url, '^https://([A-Za-z0-9-]+)\.([A-Za-z0-9-]+)\.myworkdayjobs\.com/([A-Za-z0-9-_]+)$', 3) AS slug
    FROM "ccindex"."ccindex"
    WHERE
        crawl IN ('CC-MAIN-2026-39', 'CC-MAIN-2026-34', 'CC-MAIN-2026-30', 
                'CC-MAIN-2026-25', 'CC-MAIN-2026-21', 'CC-MAIN-2026-17')
        AND subset = 'warc'
        AND fetch_status = 200
        AND url_host_registered_domain = 'myworkdayjobs.com'
) 
SELECT * FROM q
WHERE slug != 'en-US'
ORDER BY company, slug;


-- -- -- -- -- -- -- -- --
--  TODO / IN PROGRESS  --
-- -- -- -- -- -- -- -- --

-- LEVER (RETURNS NOTHING, ODD BEHAVIOR WITH THIS ATS SYSTEM AND CRAWLS)
SELECT DISTINCT
    lower(regexp_extract(url_path, '^/([A-Za-z0-9_-]+)', 1)) AS slug
FROM "ccindex"."ccindex"
WHERE 
    crawl IN ('CC-MAIN-2026-39', 'CC-MAIN-2026-34', 'CC-MAIN-2026-30', 
            'CC-MAIN-2026-25', 'CC-MAIN-2026-21', 'CC-MAIN-2026-17')
    AND subset = 'warc'
    AND url_host_name = 'jobs.lever.co'
ORDER BY slug;