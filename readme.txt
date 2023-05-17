A web-based GTFS Loader. GTFS stands for Google Transit File Specification and 
contains route and schedule data for use by transit agencies around the world
to share data with each other and with the public.

This program allows the user to select the zip file to read, creates a database
if one doesn’t exist, creates two tables and inserts the data from (just) two relevant files and
inserts the data in the db. There are two more buttons which allows the user to display the routes
that are loaded and another which determines how many trips are related to each route and headsign 
via a SQL join.

I used Flask, BeautifulSoup, SQLite, csv, datetime, and a few html files accessed via python routes.

Please give the processing a minute or two to complete.
