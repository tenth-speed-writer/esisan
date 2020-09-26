##ESI-San.

Queries outstanding buy and sell orders in a given region from the EVE Swagger Interface. CCP usually only provides day-by-day summaries; by recording more detailed, fine grained order histories we will be able to perform time series analyses the likes of which most folks can only dream.

Data is stored in a SQLite database with hard-coded queries, so if we actually invest time in this, I should probably abstract those actions out.

DESIGN DECISION TO MAKE: Should rows get the stamp of when their query was run, or when they were actually received?

ANSWER: they should. Even if that becomes inaccurate by a minute or two, we need data to exist on the same timescale if we're to perform meaningful cross analysis.

ANALYTICS CONCEPT: Measure time-period volatility of meaningful orders versus historic OR exp. smoothed volatility.

**ANALYTICAL CHALLENGE:** Define "meaningful" orders. How do we filter out silly-low buys and absurd sells? How do we tell an absurd sell from a deliberately price-setting one?

**DESIGN TASK:** Execute each page's insert as it happens. We'll probably break the pretty recursive solution but each query needs to happen in a try/except block. Otherwise, one bad page of records will cause a full update to crash. 