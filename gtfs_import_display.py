import zipfile
import sqlite3
from sqlite3 import Error
import csv
from flask import Flask, render_template, request, redirect, flash
from bs4 import BeautifulSoup
from datetime import datetime


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_routes_table(conn):
    try:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS routes (
                            route_id TEXT,
                            agency_id TEXT,
                            route_short_name TEXT,
                            route_long_name TEXT,
                            route_desc TEXT,
                            route_type TEXT,
                            route_url TEXT,
                            route_color TEXT,
                            route_text_color TEXT,
                            imported_at TIMESTAMP
                        )''')
    except Error as e:
        print(e)

def create_trips_table(conn):
    try:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS trips (
                            trip_id TEXT,
                            route_id TEXT,
                            service_id TEXT,
                            trip_headsign TEXT,
                            direction_id TEXT,
                            block_id TEXT,
                            shape_id TEXT,
                            imported_at TIMESTAMP
                        )''')
    except Error as e:
        print(e)


def delete_trips_data(conn):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM trips")
        conn.commit()
    except Error as e:
        print(e)


def insert_route(conn, route):
    try:
        cur = conn.cursor()
        cur.execute('''INSERT INTO routes (
                            route_id, agency_id, route_short_name, route_long_name,
                            route_desc, route_type, route_url, route_color, route_text_color, imported_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', route + (datetime.now(),))
        conn.commit()
    except Error as e:
        print(e)

def insert_trip(conn, trip):
    try:
        cur = conn.cursor()
        cur.execute('''INSERT INTO trips (
                            trip_id, route_id, service_id, trip_headsign,
                            direction_id, block_id, shape_id, imported_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', trip)
        conn.commit()
    except Error as e:
        print(e)


def get_all_routes(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM routes")
    rows = cur.fetchall()
    return rows


def process_zip_file(file):
    conn = create_connection("gtfsdata.db")
    import_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if conn is not None:
        create_routes_table(conn)
        create_trips_table(conn)

        delete_trips_data(conn)

        with zipfile.ZipFile(file, "r") as z:
            with z.open("routes.txt") as f:
                content = f.read().decode("utf-8")
                reader = csv.reader(content.splitlines(), delimiter=",", quotechar='"')
                next(reader)

                for row in reader:
                    route = tuple(row)
                    insert_route(conn, route)

        with zipfile.ZipFile(file, "r") as z:
            with z.open("trips.txt") as f:
                content = f.read().decode("utf-8")
                reader = csv.reader(content.splitlines(), delimiter=",", quotechar='"')
                next(reader)

                for row in reader:
                    trip = tuple(row + [import_datetime])
                    insert_trip(conn, trip)

    else:
        print("Error! Cannot create the database connection.")

def get_trips_count_by_route_and_headsign(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT r.route_id, r.route_short_name, r.route_long_name, t.trip_headsign, COUNT(*) as trip_count
        FROM trips t
        JOIN routes r ON t.trip_id = r.route_id
        GROUP BY t.trip_id, t.trip_headsign
        ORDER BY r.route_id
    """)

    rows = cur.fetchall()
    return rows


@app.route("/")
def index():
    return render_template("main.html")


@app.route("/upload", methods=["POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and file.filename.lower().endswith(".zip"):
            process_zip_file(file)
            flash("File successfully processed")
            return redirect("/")
        else:
            flash("Invalid file format. Please upload a zip file.")
            return redirect(request.url)


@app.route("/routes")
def routes():
    conn = create_connection("gtfsdata.db")
    if conn is not None:
        routes_data = get_all_routes(conn)
        # trips_count_data = get_trips_count_by_route_and_headsign(conn)
        # trips_count_dict = {}

        html = BeautifulSoup(
            "<html><head><title>Routes Data</title></head><body><h1>Routes Data</h1><table border='1'></table></body></html>",
            "lxml")
        table = html.table

        headers = ['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_desc', 'route_type',
                   'route_url', 'route_color', 'route_text_color', 'imported_at']
        thead = html.new_tag("thead")
        tr = html.new_tag("tr")
        for header in headers:
            th = html.new_tag("th")
            th.string = header
            tr.append(th)
        thead.append(tr)
        table.append(thead)

        tbody = html.new_tag("tbody")
        for route in routes_data:
            tr = html.new_tag("tr")
            for data in route:
                td = html.new_tag("td")
                td.string = str(data)
                tr.append(td)
            tbody.append(tr)
        table.append(tbody)

        return str(html)
    else:
        flash("Error! Cannot create the database connection.")
        return redirect("/")

@app.route("/trips_by_headsign")
def trips_by_headsign():
    conn = create_connection("gtfsdata.db")
    if conn is not None:
        trips_data = get_trips_count_by_route_and_headsign(conn)
        print("Number of rows:", len(trips_data))
        if len(trips_data) > 0:
            print("First row:", trips_data[0])
        return render_template("trips_by_headsign.html", trips_data=trips_data)
    else:
        flash("Error! Cannot create the database connection.")
        return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

