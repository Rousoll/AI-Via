import os
import random
import shutil
import time
import json
from PIL import Image, ImageDraw, ImageFont

dataset_image_dir = 'static/dataset'
output_dir = 'static/predictions'
os.makedirs(output_dir, exist_ok=True)

def draw_predictions(image_path, predictions):
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()

    for prediction in predictions:
        x, y, width, height = prediction['x'], prediction['y'], prediction['width'], prediction['height']
        class_name = prediction['class']
        confidence = prediction['confidence']
        x1, y1 = x - width / 2, y - height / 2
        x2, y2 = x + width / 2, y + height / 2

        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        label = f"{class_name}: {confidence:.2f}"
        draw.text((x1, y1 - 12), label, fill="white", font=font)

    return img

def run_simulation(uploaded_image_path, model):
    emergency_priority = {"ambulance": 1, "fire": 2, "police": 3}
    simulation_data = []
    predicted_image_paths = []
    images_to_predict = []

    if uploaded_image_path:
        images_to_predict.append({'path': uploaded_image_path, 'label': 'Traffic 1'})

    all_dataset = [f for f in os.listdir(dataset_image_dir) if f.lower().endswith(('.jpg', '.png'))]
    for i, img in enumerate(random.sample(all_dataset, min(3, len(all_dataset)))):
        images_to_predict.append({'path': os.path.join(dataset_image_dir, img), 'label': f'Traffic {i + 2}'})

    explanation = ""
    for img_info in images_to_predict:
        path = img_info['path']
        label = img_info['label']
        try:
            result = model.predict(path, confidence=70, overlap=30)
            detections = result.json()
            boxed = draw_predictions(path, detections['predictions'])
            out_path = os.path.join(output_dir, f"{label.replace(' ', '_')}_{int(time.time())}.jpg")
            boxed.save(out_path)
            predicted_image_paths.append(out_path)

            counts = {}
            for det in detections['predictions']:
                cls = det['class']
                counts[cls] = counts.get(cls, 0) + 1

            simulation_data.append({'label': label, 'counts': counts})

        except Exception as e:
            explanation += f"Error in {label}: {e}\n"

    simulation_data.sort(key=lambda x: (
        min([emergency_priority.get(k, float('inf')) for k in x['counts']], default=float('inf')),
        -sum(v for k, v in x['counts'].items() if k not in emergency_priority)
    ))

    explanation += "\nTraffic Light Priority Simulation:\n"
    for i, data in enumerate(simulation_data):
        label, counts = data['label'], data['counts']
        detected = next((veh for veh in emergency_priority if veh in counts), None)
        if detected:
            explanation += f"{label}: Emergency priority to {detected}.\n"
        else:
            total_cars = sum(v for k, v in counts.items() if k not in emergency_priority)
            explanation += f"{label}: Priority based on car count ({total_cars}).\n"

    return predicted_image_paths, explanation
