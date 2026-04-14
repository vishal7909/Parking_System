import cv2
from os import path
import distance_calc

print("-"*50)
print("SMART PARKING SYSTEM".center(50))
print("-"*50)

# -------------------- MENU --------------------
while True:

    print("\nEnter your option:")
    print("1. Capture new parking area")
    print("2. Use saved parking area")

    choice = int(input("Choose: "))

    if choice == 1:
        print("[INFO] Please draw parking area.")
        import draw_parking_area
        import label_parking_lot
        import draw_parking_entrance
        break

    elif choice == 2:
        if path.exists('parking_lot.png'): 
            print("\n[INFO] Found saved parking area.")
            print("[INFO] Using saved parking area.")
            break
        else:
            print("[ERROR] No parking area found!")

# -------------------- CAMERA --------------------
camera = cv2.VideoCapture(0)

print("[INFO] Initializing camera...")

# -------------------- LOAD FILES --------------------
labels = open("parking_labels.txt").read().splitlines()
entrance = list(map(int, open("parking_entrance_coordinates.txt").read().split()))

print("[INFO] Loading parking coordinates...")

parking_lot_coords = []
with open("parking_area_coordinates.txt") as f:
    for line in f:
        coords = line.strip().split()
        if len(coords) < 4:
            continue
        parking_lot_coords.append(list(map(int, coords)))

total_parking_lots = len(parking_lot_coords)

# -------------------- WINDOW FIX --------------------
cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)

# -------------------- MAIN LOOP --------------------
while True:

    closest_parking_label = "N/A"   # ✅ FIXED

    ret, frame = camera.read()

    if not ret:
        print("[ERROR] Failed to initialize camera.")
        break

    available_parking_lot = []
    unavailable_parking_lot = []

    # -------------------- SLOT DETECTION --------------------
    for (x1, y1, x2, y2) in parking_lot_coords:

        slot = frame[y1:y2, x1:x2]

        gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)

        edges = cv2.Canny(blur, 50, 150)
        pixels = cv2.countNonZero(edges)

        # 🔥 TUNE THIS VALUE
        if pixels > 500:
            unavailable_parking_lot.append([x1, y1, x2, y2])
        else:
            available_parking_lot.append([x1, y1, x2, y2])

        # draw slot
        cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 1)

    # -------------------- DRAW OCCUPIED --------------------
    for lot in unavailable_parking_lot:
        cv2.rectangle(frame, (lot[0], lot[1]), (lot[2], lot[3]), (0,0,255), 2)

    # -------------------- CLOSEST SLOT --------------------
    if len(available_parking_lot) > 0:

        closest_parking = distance_calc.find_closest_parking(
            parking_list=available_parking_lot,
            entrance=entrance
        )

        if closest_parking in parking_lot_coords:
            idx = parking_lot_coords.index(closest_parking)
            closest_parking_label = labels[idx]

    # -------------------- DRAW ENTRANCE --------------------
    cv2.rectangle(frame,
                  (entrance[0], entrance[1]),
                  (entrance[2], entrance[3]),
                  (255,0,0), 2)

    cv2.putText(frame, "IN",
                (entrance[0]+5, entrance[1]+20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255,0,0), 2)

    # -------------------- INFO TEXT --------------------
    cv2.putText(frame,
                f"Total parking lots: {total_parking_lots}",
                (10,30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,(0,255,0),2)

    cv2.putText(frame,
                f"Available parking lots: {len(available_parking_lot)}",
                (10,60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,(0,255,0),2)

    cv2.putText(frame,
                f"Closest parking lot: {closest_parking_label}",
                (10,90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,(0,255,0),2)

    # -------------------- DISPLAY FIX --------------------
    h, w = frame.shape[:2]
    frame = cv2.resize(frame, (w//2, h//2))   # ✅ no stretch

    cv2.resizeWindow("Camera", 960, 540)

    cv2.imshow("Camera", frame)

    key = cv2.waitKey(1)

    if key % 256 == 27:
        print("[INFO] Camera terminated.")
        break

camera.release()
cv2.destroyAllWindows()