##ESI-San.

Queries outstanding buy and sell orders in a given region from the EVE Swagger Interface. CCP usually only provides day-by-day summaries; by recording more detailed, fine grained order histories we will be able to perform time series analyses the likes of which most folks can only dream.

Data is stored in a SQLite database with hard-coded queries, so if we actually invest time in this, I should probably abstract those actions out.

DESIGN DECISION TO MAKE: Should rows get the stamp of when their query was run, or when they were actually received?