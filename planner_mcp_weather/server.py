# server.py - Flask HTTP server for Weather Service
import os
import logging
from flask import Flask, request, jsonify
from weather_service import get_weather

app = Flask(__name__)

# Configure logging to logs/weather_queries.log relative to project root or current working directory
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("weather_mcp")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers if reloaded
if not logger.handlers:
    file_handler = logging.FileHandler("logs/weather_queries.log", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

@app.route("/weather", methods=["GET"])
def weather_route():
    destination = request.args.get("destination")
    month = request.args.get("month")
    
    if not destination:
        logger.warning("Weather query received with missing 'destination' parameter.")
        return jsonify({"error": "Missing required parameter 'destination'"}), 400
        
    logger.info(f"Query: destination='{destination}', month='{month or 'N/A'}'")
    result = get_weather(destination, month)
    return jsonify(result)

if __name__ == "__main__":
    print("Starting Weather Service on http://localhost:5001 ...")
    app.run(host="localhost", port=5001, debug=False)
