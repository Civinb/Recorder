from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/power", methods=["POST"])
def power():
    base = request.json.get("base")
    exponent = request.json.get("exponent")
    print(f"Received base: {base}, exponent: {exponent}")
    if base is None or exponent is None:
        return jsonify({"error": "Missing 'base' or 'exponent' in request body"})
    try:
        result = base ** exponent
        print(f"Calculated result: {result}")
        return jsonify({"result": result})
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e), "message": "Please try again"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)