from flask import Flask, Response, render_template, jsonify, request
import cv2

app = Flask(__name__)

# -------------------- CAMERA --------------------
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# -------------------- LOAD COORDS --------------------
parking_lot_coords = []
with open("parking_area_coordinates.txt") as f:
    for line in f:
        coords = line.strip().split()
        if len(coords) < 4:
            continue
        parking_lot_coords.append(list(map(int, coords)))

# -------------------- STORAGE --------------------
reserved_slots = {}

# -------------------- FRAME --------------------
def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            continue

        for idx, (x1, y1, x2, y2) in enumerate(parking_lot_coords):

            slot = frame[y1:y2, x1:x2]

            gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5,5), 0)

            edges = cv2.Canny(blur, 50, 150)
            pixels = cv2.countNonZero(edges)

            occupied = pixels > 500

            if idx in reserved_slots:
                color = (0,165,255)
            elif occupied:
                color = (0,0,255)
            else:
                color = (0,255,0)

            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
            cv2.putText(frame, str(idx), (x1, y1-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# -------------------- HOME --------------------
@app.route('/')
def index():
    return """
    <html>
        <body style="text-align:center; background:#0f172a; color:white;">
            <h1>🚗 Smart Parking System</h1>

            <a href="/reserve_page" style="color:cyan;">Go to Reservation</a><br><br>

            <img src="/video" width="900" style="border-radius:10px;">
        </body>
    </html>
    """

# -------------------- VIDEO --------------------
@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# -------------------- STATUS --------------------
@app.route('/status')
def status():
    occupied_slots = []

    success, frame = camera.read()
    if success:
        for idx, (x1, y1, x2, y2) in enumerate(parking_lot_coords):

            slot = frame[y1:y2, x1:x2]

            gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            if cv2.countNonZero(edges) > 500:
                occupied_slots.append(idx)

    return jsonify({
        "reserved": list(reserved_slots.keys()),
        "occupied": occupied_slots
    })

# -------------------- RESERVE --------------------
@app.route('/reserve', methods=['POST'])
def reserve():
    data = request.json
    slot = data['slot']

    success, frame = camera.read()
    if success:
        x1, y1, x2, y2 = parking_lot_coords[slot]
        slot_img = frame[y1:y2, x1:x2]

        gray = cv2.cvtColor(slot_img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        if cv2.countNonZero(edges) > 500:
            return jsonify({"status": "occupied"})

    if slot in reserved_slots:
        return jsonify({"status": "already"})

    reserved_slots[slot] = {
        "name": data['name'],
        "vehicle": data['vehicle']
    }

    return jsonify({"status": "reserved"})

# -------------------- CANCEL --------------------
@app.route('/cancel/<int:slot>')
def cancel(slot):
    if slot in reserved_slots:
        del reserved_slots[slot]
    return jsonify({"status": "cancelled"})

# -------------------- FRONTEND --------------------
@app.route('/reserve_page')
def reserve_page():
    return render_template("reserve.html",
                           total=len(parking_lot_coords),
                           price=50)

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=False)