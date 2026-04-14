from ultralytics import YOLO

model = YOLO("yolov8n.pt")   # pre-trained model

def parking_availability(frame, parking_lot_coords):

    available = []
    unavailable = []

    results = model(frame)

    cars = []

    # Get car bounding boxes
    for r in results:
        for box, cls in zip(r.boxes.xyxy, r.boxes.cls):

            if int(cls) == 2:   # class 2 = car
                x1, y1, x2, y2 = map(int, box)
                cars.append((x1, y1, x2, y2))

    # Check each parking slot
    for (sx1, sy1, sx2, sy2) in parking_lot_coords:

        occupied = False

        for (x1, y1, x2, y2) in cars:

            # Check overlap
            if (x1 < sx2 and x2 > sx1 and y1 < sy2 and y2 > sy1):
                occupied = True
                break

        if occupied:
            unavailable.append([sx1, sy1, sx2, sy2])
        else:
            available.append([sx1, sy1, sx2, sy2])

    return available, unavailable