from flask import Flask, request, jsonify

app = Flask(__name__)

FLAG = "TSGCTF{MOCK_FLAG_FOR_TESTING}"

@app.route("/challenge")
def challenge():
    time = request.args.get("time")
    if not isinstance(time, str):
        return "time should be string", 400
    
    # Mock the Temporal.ZonedDateTime behavior
    # For the sake of this mock, we assume that certain inputs cause the equality check to fail
    if "Malicious/Timezone" in time or "Invalid" in time:
        return f"Congratulations! flag: {FLAG}", 200
    
    return "try again!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)