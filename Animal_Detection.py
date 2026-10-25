import cv2
import time
import os
import serial
import smtplib
import pygame
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

# -------------------- PROJECT PATHS --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# -------------------- AUDIO SETUP --------------------
pygame.mixer.init()

DOG_SOUND  = os.path.join(BASE_DIR, "dog10.mp3")
BEE_SOUND  = os.path.join(BASE_DIR, "bee10.mp3")
HORN_SOUND = os.path.join(BASE_DIR, "horn10.mp3")

last_sound_time = 0
SOUND_COOLDOWN = 5  # seconds

# -------------------- SERIAL SETUP --------------------
SERIAL_PORT = "COM13"
com_port = serial.Serial(SERIAL_PORT, baudrate=9600, timeout=1)

def sendCOM(message):
    print("Sending Data:", message)
    com_port.write((message + "\r\n").encode())
    time.sleep(1)

# -------------------- MODEL SETUP --------------------
MODEL_PATH = os.path.join(MODELS_DIR, "frozen_inference_graph.pb")
CONFIG_PATH = os.path.join(MODELS_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pbtxt")

if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(
        f"Model file not found:\n{MODEL_PATH}\n\n"
        "Make sure frozen_inference_graph.pb is inside the models folder."
    )

if not os.path.isfile(CONFIG_PATH):
    raise FileNotFoundError(
        f"Model configuration file not found:\n{CONFIG_PATH}\n\n"
        "Make sure ssd_mobilenet_v2_coco_2018_03_29.pbtxt is inside the models folder."
    )

classNames = {
    0: 'background', 1: 'person',
    16: 'bird', 17: 'cat', 18: 'dog', 19: 'horse',
    20: 'sheep', 21: 'cow', 22: 'elephant',
    23: 'bear', 24: 'zebra', 25: 'giraffe'
}

def id_class_name(class_id):
    return classNames.get(class_id, "Unknown")

model = cv2.dnn.readNetFromTensorflow(
    MODEL_PATH,
    CONFIG_PATH
)

# -------------------- CAMERA --------------------
cap = cv2.VideoCapture(0)

print("System Started...")

# -------------------- MAIN LOOP --------------------
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.resize(frame, (640, 480))
    image_height, image_width, _ = frame.shape

    model.setInput(cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True))
    output = model.forward()

    detected_animal = "NA"

    for detection in output[0, 0, :, :]:
        confidence = detection[2]
        if confidence > 0.5:
            class_id = int(detection[1])
            class_name = id_class_name(class_id)

            if class_id in [20, 21, 22, 23]:
                detected_animal = class_name.upper()
                print("Detected:", detected_animal, confidence)

                box_x = int(detection[3] * image_width)
                box_y = int(detection[4] * image_height)
                box_w = int(detection[5] * image_width)
                box_h = int(detection[6] * image_height)

                cv2.rectangle(frame, (box_x, box_y), (box_w, box_h), (0, 255, 0), 2)
                cv2.putText(frame, detected_animal, (box_x, box_y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # -------------------- DISPLAY --------------------
    cv2.imshow("Animal Detection", frame)
    cv2.imwrite(os.path.join(BASE_DIR, "image_box_text.jpg"), frame)

    # -------------------- SOUND + SERIAL LOGIC --------------------
    current_time = time.time()

    if detected_animal != "NA" and (current_time - last_sound_time > SOUND_COOLDOWN):
        last_sound_time = current_time

        if detected_animal == "COW":
            sendCOM("1")
            pygame.mixer.music.load(DOG_SOUND)
            pygame.mixer.music.play()

        elif detected_animal == "ELEPHANT":
            sendCOM("2")
            pygame.mixer.music.load(BEE_SOUND)
            pygame.mixer.music.play()

        elif detected_animal == "BEAR":
            sendCOM("3")
            pygame.mixer.music.load(HORN_SOUND)
            pygame.mixer.music.play()

        elif detected_animal == "SHEEP":
            sendCOM("4")
            pygame.mixer.music.load(DOG_SOUND)
            pygame.mixer.music.play()


    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

# -------------------- CLEANUP --------------------
cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()

if com_port.is_open:
    com_port.close()
    com_port.close()
