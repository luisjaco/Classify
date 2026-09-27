# company_names

In this directory, you will find a list of company names found on various ATS services. These
were sourced using [`CommonCrawl`](https://commoncrawl.org/). To extract company names, we query the
**CommonCrawl URL Index** using **AWS Athena**. For these particular name dumps, we look at the 
previous six crawls; crawls are currently made monthly. You can find the particular query used in
[`query.sql`](./query.sql).

These company names do not need to be updated frequently. As such, we will not automate this
process. In the event that we scale this to be an ongoing project, we may automate the company name
retrieval.

> You can read more about how the **CommonCrawl URL Index** is accessed with **AWS Athena** 
[here](https://commoncrawl.org/url-index).