from flask import Flask, request, jsonify, render_template, send_from_directory # ADDED send_from_directory
from werkzeug.utils import secure_filename
import os
import sys
import random

# --- Path Configuration ---
# Get the base directory of app.py, which is the project root
PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the 'ai' folder to the Python path so AI.py can be imported
sys.path.append(os.path.join(PROJECT_ROOT_DIR, 'ai'))

# Import the run_prediction function from your AI.py module (Note the capital 'AI')
from AI import run_prediction

# Define important directory paths
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT_DIR, 'uploads')
PREDICTION_STATIC_BASE_PATH = os.path.join(PROJECT_ROOT_DIR, 'static', 'predictions')

# The directory where `predict_and_simulate` (if it existed in your app.py)
# was looking for images. Based on your 'tree' output, this would be:
DATASET_SIMULATION_IMAGE_DIR = os.path.join(PROJECT_ROOT_DIR, 'datasets', 'test', 'images')


# --- Create directories if they don't exist ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PREDICTION_STATIC_BASE_PATH, exist_ok=True)
os.makedirs(DATASET_SIMULATION_IMAGE_DIR, exist_ok=True) # Ensure this exists if any function uses it


# --- Flask App Initialization ---
app = Flask(__name__, static_folder='static', template_folder='templates')

# --- NEW ROUTE TO SERVE PREDICTED IMAGES ---
# This tells Flask to serve files from PREDICTION_STATIC_BASE_PATH
# when requests come to /predictions/<path:filename>
@app.route('/predictions/<path:filename>')
def serve_predictions(filename):
    print(f"Attempting to serve prediction file: {filename} from {PREDICTION_STATIC_BASE_PATH}")
    # send_from_directory securely serves the file.
    # It requires the directory and the filename.
    return send_from_directory(PREDICTION_STATIC_BASE_PATH, filename)
# --- END OF NEW ROUTE ---


# --- Flask Routes ---

@app.route('/')
def dashboard():
    """Renders the main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/apply-controls', methods=['POST'])
def apply_controls():
    """Handles control parameter updates (e.g., confidence, speed)."""
    data = request.get_json()
    confidence = data.get('confidence')
    speed = data.get('speed')
    # Implement logic to update your system's parameters here
    # For now, just return a success message
    print(f"Controls applied: Confidence={confidence}, Speed={speed}")
    return jsonify({"message": "Control parameters updated successfully."})

# at the top of your file
current_frame = 0


@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Handles image uploads, runs prediction, and returns results."""
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image uploaded"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    print(f"Image uploaded to: {save_path}")


    # Call your AI prediction function
    prediction_data, stats_data, full_saved_image_path = run_prediction(save_path)
    
    image_url = None
    if full_saved_image_path:
        try:
            # Convert the absolute path from AI.py into a URL relative to Flask's static folder
            # The calculation `os.path.relpath(full_saved_image_path, app.static_folder)`
            # will yield 'predictions/latest_inference/your_image.jpg'
            # The leading '/' is added to make it an absolute path from the root of the server.
            image_url = '/' + os.path.relpath(full_saved_image_path, app.static_folder).replace('\\', '/')
            print(f"DEBUG: Calculated image_url: {image_url}") # <--- Keep this debug line
        except ValueError:
            print(f"Warning: Predicted image path '{full_saved_image_path}' is not within the static folder '{app.static_folder}'.")
            image_url = None

    if image_url is None:
        print(f"DEBUG: image_url is None, returning failure response.") # <--- Keep this debug line
        return jsonify({"success": False, "error": "Failed to process image or generate prediction image URL."}), 500

    print(f"DEBUG: Final image_url being sent: {image_url}") # <--- Keep this debug line
    return jsonify({"success": True, "prediction": prediction_data, "stats": stats_data, "image_url": image_url})
@app.route('/api/start-simulation', methods=['GET'])
def start_simulation():
    """
    3 random images from datasets/test/images + last uploaded image.
    Run run_prediction() on each and assign signals based on priority.
    """
    # 1) Get 3 random dataset images
    dataset_images_dir = DATASET_SIMULATION_IMAGE_DIR
    available_dataset_imgs = [os.path.join(dataset_images_dir, f) 
                              for f in os.listdir(dataset_images_dir) 
                              if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    random_dataset_imgs = random.sample(available_dataset_imgs, min(3, len(available_dataset_imgs)))

    # 2) Get the latest uploaded image
    upload_imgs = [os.path.join(UPLOAD_FOLDER, f) for f in os.listdir(UPLOAD_FOLDER)]
    latest_upload = max(upload_imgs, key=os.path.getctime) if upload_imgs else None

    if latest_upload:
        random_dataset_imgs.append(latest_upload)

    # 3) Run prediction on all selected images
    signal_map = {}  # {signalA: {...}, signalB: {...}, ...}
    priorities = []
    for idx, img in enumerate(random_dataset_imgs):
        _, stats_data, saved_path = run_prediction(img)
        img_url = '/' + os.path.relpath(saved_path, app.static_folder).replace("\\", "/") if saved_path else None

        # compute priority: lower = more important
        pri = 4  # default
        if stats_data['emergency_vehicles'] > 0:
            pri = 1
        elif stats_data['other_vehicles'] > 0:
            pri = 3

        sig = f"signal{idx+1}"
        signal_map[sig] = {"image_url": img_url, "priority": pri}
        priorities.append((sig, pri))

    # 4) choose who gets green first (lowest priority number)
    green = min(priorities, key=lambda x: x[1])[0]

    return jsonify({
        "signals": signal_map,
        "go_first": green
    })


@app.route('/api/live-stats')
def live_stats():
    """Provides placeholder live statistics (you can integrate real-time data here)."""
    data = {
        "total_vehicles": 15,
        "emergency_vehicles": 4,
        "other_vehicles": 11,
        "alerts": ["Emergency vehicle detected near Sector 3 (Test data)"]
    }
    return jsonify(data)


# --- Main execution block ---
if __name__ == "__main__":
    print(f"--- Starting Flask Application ---")
    print(f"Project Root: {PROJECT_ROOT_DIR}")
    print(f"Uploads Folder: {UPLOAD_FOLDER}")
    print(f"Prediction Output Folder: {PREDICTION_STATIC_BASE_PATH}")
    print(f"Simulation Data Folder (if used): {DATASET_SIMULATION_IMAGE_DIR}")
    # Remove or comment out the line below that caused the NameError
    # print(f"Ensure your AI model (best.pt) is trained and located correctly in 'runs/detect/{TRAINED_WEIGHTS_FOLDER_NAME}/weights/'.") 
    
    app.run(host='0.0.0.0', port=5050, debug=True)