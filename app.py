from flask import Flask, jsonify, request, send_file
import config
import mysql.connector
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from io import BytesIO
from datetime import date

app = Flask(__name__)


def fetch_all(query, params=()):
    db = config.connect()
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result


def fetch_one(query, params=()):
    db = config.connect()
    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result


def execute_query(query, params=()):
    db = config.connect()
    cursor = db.cursor()
    cursor.execute(query, params)
    db.commit()
    result = cursor.lastrowid
    cursor.close()
    db.close()
    return result


@app.route("/")
def home():
    return jsonify({
        "message": "Electricity Analysis System API",
        "database": "eletrcity_analysis",
        "endpoints": [
            "/consumers",
            "/meters",
            "/meter-readings",
            "/reports/consumer-summary",
            "/reports/total-consumption",
            "/reports/high-consumption",
            "/analytics/consumer-usage",
            "/analytics/meter-summary",
            "/analytics/usage-numpy",
            "/charts/consumer-usage",
            "/charts/meter-readings"
        ]
    })


@app.route("/consumers", methods=["GET"])
def get_consumers():
    return jsonify(fetch_all("SELECT * FROM consumers"))


@app.route("/consumers", methods=["POST"])
def add_consumer():
    data = request.get_json()

    required = ["consumer_name", "address", "phone", "email"]

    if not data or any(key not in data for key in required):
        return jsonify({"error": "Provide consumer_name, address, phone and email"}), 400

    try:
        consumer_id = execute_query(
            """INSERT INTO consumers
            (consumer_name, address, phone, email)
            VALUES (%s, %s, %s, %s)""",
            (
                data["consumer_name"],
                data["address"],
                data["phone"],
                data["email"]
            )
        )

        return jsonify({
            "message": "Consumer added successfully",
            "consumer_id": consumer_id
        }), 201

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/consumers/<int:consumer_id>", methods=["GET"])
def get_consumer(consumer_id):
    consumer = fetch_one(
        "SELECT * FROM consumers WHERE consumer_id = %s",
        (consumer_id,)
    )

    if not consumer:
        return jsonify({"error": "Consumer not found"}), 404

    return jsonify(consumer)


@app.route("/consumers/<int:consumer_id>", methods=["PUT"])
def update_consumer(consumer_id):
    data = request.get_json()

    allowed = ["consumer_name", "address", "phone", "email"]
    updates = [(key, data[key]) for key in allowed if data and key in data]

    if not updates:
        return jsonify({"error": "Provide at least one field to update"}), 400

    consumer = fetch_one(
        "SELECT * FROM consumers WHERE consumer_id = %s",
        (consumer_id,)
    )

    if not consumer:
        return jsonify({"error": "Consumer not found"}), 404

    set_clause = ", ".join(f"{key} = %s" for key, value in updates)
    values = [value for key, value in updates]
    values.append(consumer_id)

    try:
        execute_query(
            f"UPDATE consumers SET {set_clause} WHERE consumer_id = %s",
            tuple(values)
        )

        return jsonify({"message": "Consumer updated successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/consumers/<int:consumer_id>", methods=["DELETE"])
def delete_consumer(consumer_id):
    consumer = fetch_one(
        "SELECT * FROM consumers WHERE consumer_id = %s",
        (consumer_id,)
    )

    if not consumer:
        return jsonify({"error": "Consumer not found"}), 404

    try:
        execute_query(
            "DELETE FROM consumers WHERE consumer_id = %s",
            (consumer_id,)
        )

        return jsonify({"message": "Consumer deleted successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/meters", methods=["GET"])
def get_meters():
    query = """
        SELECT m.*, c.consumer_name, c.address
        FROM meters m
        JOIN consumers c ON m.consumer_id = c.consumer_id
        ORDER BY m.meter_id
    """

    return jsonify(fetch_all(query))


@app.route("/meters", methods=["POST"])
def add_meter():
    data = request.get_json()

    required = ["consumer_id", "meter_number", "meter_type", "installation_date"]

    if not data or any(key not in data for key in required):
        return jsonify({
            "error": "Provide consumer_id, meter_number, meter_type and installation_date"
        }), 400

    try:
        meter_id = execute_query(
            """INSERT INTO meters
            (consumer_id, meter_number, meter_type, installation_date)
            VALUES (%s, %s, %s, %s)""",
            (
                data["consumer_id"],
                data["meter_number"],
                data["meter_type"],
                data["installation_date"]
            )
        )

        return jsonify({
            "message": "Meter added successfully",
            "meter_id": meter_id
        }), 201

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/meters/<int:meter_id>", methods=["GET"])
def get_meter(meter_id):
    meter = fetch_one(
        "SELECT * FROM meters WHERE meter_id = %s",
        (meter_id,)
    )

    if not meter:
        return jsonify({"error": "Meter not found"}), 404

    return jsonify(meter)


@app.route("/meters/<int:meter_id>", methods=["PUT"])
def update_meter(meter_id):
    data = request.get_json()

    allowed = ["consumer_id", "meter_number", "meter_type", "installation_date"]
    updates = [(key, data[key]) for key in allowed if data and key in data]

    if not updates:
        return jsonify({"error": "Provide at least one field to update"}), 400

    meter = fetch_one(
        "SELECT * FROM meters WHERE meter_id = %s",
        (meter_id,)
    )

    if not meter:
        return jsonify({"error": "Meter not found"}), 404

    set_clause = ", ".join(f"{key} = %s" for key, value in updates)
    values = [value for key, value in updates]
    values.append(meter_id)

    try:
        execute_query(
            f"UPDATE meters SET {set_clause} WHERE meter_id = %s",
            tuple(values)
        )

        return jsonify({"message": "Meter updated successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/meters/<int:meter_id>", methods=["DELETE"])
def delete_meter(meter_id):
    meter = fetch_one(
        "SELECT * FROM meters WHERE meter_id = %s",
        (meter_id,)
    )

    if not meter:
        return jsonify({"error": "Meter not found"}), 404

    try:
        execute_query(
            "DELETE FROM meters WHERE meter_id = %s",
            (meter_id,)
        )

        return jsonify({"message": "Meter deleted successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/meter-readings", methods=["GET"])
def get_readings():
    query = """
        SELECT r.*, m.meter_number, c.consumer_name
        FROM meter_readings r
        JOIN meters m ON r.meter_id = m.meter_id
        JOIN consumers c ON m.consumer_id = c.consumer_id
        ORDER BY r.reading_id
    """

    return jsonify(fetch_all(query))


@app.route("/meter-readings", methods=["POST"])
def add_reading():
    data = request.get_json()

    required = ["meter_id", "reading_date", "units_consumed", "amount"]

    if not data or any(key not in data for key in required):
        return jsonify({
            "error": "Provide meter_id, reading_date, units_consumed and amount"
        }), 400

    try:
        reading_id = execute_query(
            """INSERT INTO meter_readings
            (meter_id, reading_date, units_consumed, amount)
            VALUES (%s, %s, %s, %s)""",
            (
                data["meter_id"],
                data["reading_date"],
                data["units_consumed"],
                data["amount"]
            )
        )

        return jsonify({
            "message": "Meter reading added successfully",
            "reading_id": reading_id
        }), 201

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/meter-readings/<int:reading_id>", methods=["GET"])
def get_reading(reading_id):
    reading = fetch_one(
        "SELECT * FROM meter_readings WHERE reading_id = %s",
        (reading_id,)
    )

    if not reading:
        return jsonify({"error": "Reading not found"}), 404

    return jsonify(reading)


@app.route("/meter-readings/<int:reading_id>", methods=["PUT"])
def update_reading(reading_id):
    data = request.get_json()

    allowed = ["meter_id", "reading_date", "units_consumed", "amount"]
    updates = [(key, data[key]) for key in allowed if data and key in data]

    if not updates:
        return jsonify({"error": "Provide at least one field to update"}), 400

    reading = fetch_one(
        "SELECT * FROM meter_readings WHERE reading_id = %s",
        (reading_id,)
    )

    if not reading:
        return jsonify({"error": "Reading not found"}), 404

    set_clause = ", ".join(f"{key} = %s" for key, value in updates)
    values = [value for key, value in updates]
    values.append(reading_id)

    try:
        execute_query(
            f"UPDATE meter_readings SET {set_clause} WHERE reading_id = %s",
            tuple(values)
        )

        return jsonify({"message": "Meter reading updated successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/meter-readings/<int:reading_id>", methods=["DELETE"])
def delete_reading(reading_id):
    reading = fetch_one(
        "SELECT * FROM meter_readings WHERE reading_id = %s",
        (reading_id,)
    )

    if not reading:
        return jsonify({"error": "Reading not found"}), 404

    try:
        execute_query(
            "DELETE FROM meter_readings WHERE reading_id = %s",
            (reading_id,)
        )

        return jsonify({"message": "Meter reading deleted successfully"})

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/reports/consumer-summary", methods=["GET"])
def consumer_summary():
    query = """
        SELECT
            c.consumer_id,
            c.consumer_name,
            c.address,
            COUNT(DISTINCT m.meter_id) AS total_meters,
            COALESCE(SUM(r.units_consumed), 0) AS total_units,
            COALESCE(SUM(r.amount), 0) AS total_amount
        FROM consumers c
        LEFT JOIN meters m ON c.consumer_id = m.consumer_id
        LEFT JOIN meter_readings r ON m.meter_id = r.meter_id
        GROUP BY c.consumer_id, c.consumer_name, c.address
        ORDER BY c.consumer_id
    """

    return jsonify(fetch_all(query))


@app.route("/reports/total-consumption", methods=["GET"])
def total_consumption():
    query = """
        SELECT
            COUNT(*) AS total_readings,
            COALESCE(SUM(units_consumed), 0) AS total_units_consumed,
            COALESCE(SUM(amount), 0) AS total_amount
        FROM meter_readings
    """

    return jsonify(fetch_one(query))


@app.route("/reports/high-consumption", methods=["GET"])
def high_consumption():
    query = """
        SELECT
            c.consumer_name,
            m.meter_number,
            r.reading_date,
            r.units_consumed,
            r.amount
        FROM meter_readings r
        JOIN meters m ON r.meter_id = m.meter_id
        JOIN consumers c ON m.consumer_id = c.consumer_id
        WHERE r.units_consumed >= %s
        ORDER BY r.units_consumed DESC
    """

    threshold = request.args.get("threshold", default=200, type=float)

    return jsonify(fetch_all(query, (threshold,)))


@app.route("/analytics/consumer-usage", methods=["GET"])
def consumer_usage():
    query = """
        SELECT
            c.consumer_id,
            c.consumer_name,
            SUM(r.units_consumed) AS total_units,
            SUM(r.amount) AS total_amount
        FROM consumers c
        JOIN meters m ON c.consumer_id = m.consumer_id
        JOIN meter_readings r ON m.meter_id = r.meter_id
        GROUP BY c.consumer_id, c.consumer_name
        ORDER BY total_units DESC
    """

    rows = fetch_all(query)

    if not rows:
        return jsonify([])

    df = pd.DataFrame(rows)
    df = df.fillna(0)

    return jsonify(df.to_dict(orient="records"))


@app.route("/analytics/meter-summary", methods=["GET"])
def meter_summary():
    query = """
        SELECT
            m.meter_id,
            m.meter_number,
            m.meter_type,
            COUNT(r.reading_id) AS total_readings,
            COALESCE(SUM(r.units_consumed), 0) AS total_units,
            COALESCE(SUM(r.amount), 0) AS total_amount
        FROM meters m
        LEFT JOIN meter_readings r ON m.meter_id = r.meter_id
        GROUP BY m.meter_id, m.meter_number, m.meter_type
        ORDER BY m.meter_id
    """

    return jsonify(fetch_all(query))


@app.route("/analytics/usage-numpy", methods=["GET"])
def usage_numpy():
    rows = fetch_all(
        "SELECT units_consumed FROM meter_readings"
    )

    values = np.array(
        [float(row["units_consumed"]) for row in rows],
        dtype=float
    )

    if values.size == 0:
        return jsonify({
            "total_units": 0,
            "average_units": 0,
            "maximum_units": 0,
            "minimum_units": 0
        })

    return jsonify({
        "total_units": float(np.sum(values)),
        "average_units": float(np.mean(values)),
        "maximum_units": float(np.max(values)),
        "minimum_units": float(np.min(values))
    })


@app.route("/charts/consumer-usage", methods=["GET"])
def consumer_usage_chart():
    rows = fetch_all("""
        SELECT c.consumer_name, COALESCE(SUM(r.units_consumed), 0) AS total_units
        FROM consumers c
        LEFT JOIN meters m ON c.consumer_id = m.consumer_id
        LEFT JOIN meter_readings r ON m.meter_id = r.meter_id
        GROUP BY c.consumer_id, c.consumer_name
        ORDER BY c.consumer_id
    """)

    if not rows:
        return jsonify({"error": "No consumer data available"}), 404

    names = [row["consumer_name"] for row in rows]
    units = [float(row["total_units"]) for row in rows]

    plt.figure(figsize=(12, 6))
    plt.bar(names, units)
    plt.xlabel("Consumers")
    plt.ylabel("Units Consumed")
    plt.title("Consumer Electricity Usage")
    plt.xticks(rotation=60)
    plt.tight_layout()

    image_data = BytesIO()
    plt.savefig(image_data, format="png")
    image_data.seek(0)
    plt.close()

    return send_file(image_data, mimetype="image/png")


@app.route("/charts/meter-readings", methods=["GET"])
def meter_readings_chart():
    rows = fetch_all("""
        SELECT reading_date, SUM(units_consumed) AS total_units
        FROM meter_readings
        GROUP BY reading_date
        ORDER BY reading_date
    """)

    if not rows:
        return jsonify({"error": "No meter readings available"}), 404

    dates = [str(row["reading_date"]) for row in rows]
    units = [float(row["total_units"]) for row in rows]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, units, marker="o")
    plt.xlabel("Reading Date")
    plt.ylabel("Total Units Consumed")
    plt.title("Electricity Consumption by Date")
    plt.xticks(rotation=45)
    plt.tight_layout()

    image_data = BytesIO()
    plt.savefig(image_data, format="png")
    image_data.seek(0)
    plt.close()

    return send_file(image_data, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)