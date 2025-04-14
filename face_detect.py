import cv2
import os
import numpy as np
import mediapipe as mp
from time import sleep
import pickle

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

def collect_faces(output_dir="dataset", num_samples=100):
    """Capture face samples for training"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    person_name = input("Enter person's name: ").lower()
    person_dir = os.path.join(output_dir, person_name)
    
    if not os.path.exists(person_dir):
        os.makedirs(person_dir)
    
    cap = cv2.VideoCapture(0)
    print(f"Capturing {num_samples} samples for {person_name}...")
    
    count = 0
    while count < num_samples:
        ret, frame = cap.read()
        if not ret:
            break
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                ih, iw, _ = frame.shape
                x, y, w, h = int(bbox.xmin * iw), int(bbox.ymin * ih), \
                             int(bbox.width * iw), int(bbox.height * ih)
                
                # Expand and constrain bounding box
                padding = 20
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(iw - x, w + 2 * padding)
                h = min(ih - y, h + 2 * padding)

                face_roi = frame[y:y+h, x:x+w]
                if face_roi is not None and face_roi.size != 0:
                    gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                    resized_face = cv2.resize(gray_face, (100, 100))
                    cv2.imwrite(f"{person_dir}/{count}.jpg", resized_face)
                    count += 1
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Captured: {count}/{num_samples}", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    sleep(0.3)
        
        cv2.imshow("Collecting Faces", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"Completed capturing {count} samples for {person_name}")

def train_model(dataset_path="dataset"):
    """Train LBPH face recognizer"""
    faces = []
    labels = []
    label_ids = {}
    current_id = 0
    
    for root, _, files in os.walk(dataset_path):
        if len(files) == 0:
            continue
            
        label = os.path.basename(root)
        if label not in label_ids:
            label_ids[label] = current_id
            current_id += 1
            
        for file in files:
            if file.endswith("jpg") or file.endswith("png"):
                path = os.path.join(root, file)
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                img = clahe.apply(img)
                faces.append(img)
                labels.append(label_ids[label])
    
    print(f"Training on {len(faces)} samples from {len(label_ids)} people...")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    recognizer.save("face_model.yml")
    
    with open("labels.pickle", "wb") as f:
        pickle.dump(label_ids, f)
    
    print("Training complete. Model saved to face_model.yml")
    return recognizer, label_ids

def run_recognition():
    """Run face recognition in real-time"""
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read("face_model.yml")
        
        with open("labels.pickle", "rb") as f:
            label_ids = pickle.load(f)
            labels = {v: k for k, v in label_ids.items()}
    except:
        print("Model files not found. Please train first.")
        return
    
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                ih, iw, _ = frame.shape
                x, y, w, h = int(bbox.xmin * iw), int(bbox.ymin * ih), \
                             int(bbox.width * iw), int(bbox.height * ih)
                
                # Adjust bounds
                x = max(0, x)
                y = max(0, y)
                x_end = min(iw, x + w)
                y_end = min(ih, y + h)
                face_roi = frame[y:y_end, x:x_end]

                if face_roi is not None and face_roi.size != 0:
                    gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                    resized_face = cv2.resize(gray_face, (100, 100))

                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    processed_face = clahe.apply(resized_face)

                    id_, confidence = recognizer.predict(processed_face)

                    if confidence < 100:
                        name = labels[id_]
                        color = (0, 255, 0)
                    else:
                        name = "Unknown"
                        color = (0, 0, 255)

                    cv2.rectangle(frame, (x, y), (x_end, y_end), color, 2)
                    cv2.putText(frame, f"{name} {confidence:.1f}", 
                                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.imshow("Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print("1. Collect face samples")
    print("2. Train model")
    print("3. Run recognition")
    choice = input("Select option (1-3): ")
    
    if choice == "1":
        collect_faces()
    elif choice == "2":
        train_model()
    elif choice == "3":
        run_recognition()
