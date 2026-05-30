from flask import Flask, request


app = Flask(__name__)


@app.route("/home", methods=["GET", "POST"])
def home():
    password = request.args.get("pwd")
    print("args:", password)
    password_2 = request.form.get("pwd")
    print("form:", password_2)
    password_3 = request.json.get("pwd") if request.is_json else None
    print("json:", password_3)
    return f"test - Password: {password}"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)