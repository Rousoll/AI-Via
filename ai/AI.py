from ultralytics import YOLO
import os
import json # Keeping this if it's used elsewhere, but not directly in this snippet
import glob # Needed for robust file finding

# --- Define Project Root and Key Paths ---
# This correctly gets the path to '/Users/russsmac/Desktop/AI-Via/AI-Via-Code/'
PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to your data.yaml file, which is located in the project root
DATA_YAML_PATH = os.path.join(PROJECT_ROOT_DIR, 'data.yaml')

# The name of the specific training run folder where your best.pt is located.
TRAINED_WEIGHTS_FOLDER_NAME = 'train5' 

# Full path to your best.pt weights
LOAD_WEIGHTS_PATH = os.path.join(PROJECT_ROOT_DIR, 'runs', 'detect', TRAINED_WEIGHTS_FOLDER_NAME, 'weights', 'best.pt')

# Base directory for saving inference results (relative to project root)
PREDICTION_OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT_DIR, 'static', 'predictions')

# Ensure the prediction output directory exists
os.makedirs(PREDICTION_OUTPUT_BASE_DIR, exist_ok=True)


# ----- Training function -----
def train_model(data_yaml_path=DATA_YAML_PATH, epochs=50, model_name='yolov8n.pt'):
    """
    Train the YOLO model using the given dataset.
    Args:
        data_yaml_path (str): Path to the data.yaml file. Defaults to DATA_YAML_PATH.
        epochs (int): Number of training epochs. Defaults to 50 (recommended higher than 5).
        model_name (str): The base YOLO model to use (e.g., 'yolov8n.pt', 'yolov8s.pt').
    """
    if not os.path.exists(data_yaml_path):
        print(f"Error: data.yaml not found at {data_yaml_path}. Training aborted.")
        return False

    print(f"Starting training with data: {data_yaml_path}, epochs: {epochs}, using model: {model_name}")
    base_model = YOLO(model_name)
    
    results = base_model.train(
        data=data_yaml_path, 
        epochs=epochs, 
        project=os.path.join(PROJECT_ROOT_DIR, 'runs', 'detect')
    )
    
    print(f"Training finished. Check '{os.path.join(PROJECT_ROOT_DIR, 'runs', 'detect', 'YOUR_TRAIN_FOLDER', 'weights', 'best.pt')}' for weights.")
    print("Note: 'YOUR_TRAIN_FOLDER' will be dynamically named by YOLO (e.g., 'train', 'train2', etc.).")
    return True


# ----- Initialize model globally -----
try:
    if os.path.exists(LOAD_WEIGHTS_PATH):
        print(f"ATTEMPTING TO LOAD TRAINED WEIGHTS FROM: {LOAD_WEIGHTS_PATH}")
        model = YOLO(LOAD_WEIGHTS_PATH)
        print("SUCCESS: Trained weights loaded.")
    else:
        print(f"WARNING: Trained weights NOT found at {LOAD_WEIGHTS_PATH}.")
        print("Falling back to loading base model (yolov8n.pt).")
        model = YOLO('yolov8n.pt')
    
    if hasattr(model, 'names'):
        print(f"Model loaded with {len(model.names)} classes: {model.names}")
    else:
        print("Warning: Could not retrieve class names from loaded model. Check model integrity.")
    
    model.eval()

except Exception as e:
    print(f"CRITICAL ERROR initializing model: {e}")
    print("Falling back to base model (yolov8n.pt) due to critical error.")
    model = YOLO('yolov8n.pt')


# ----- Prediction / Inference function -----
def run_prediction(image_path):
    """
    Use pretrained (or base) weights to perform inference on a single image.
    Args:
        image_path (str): Absolute path to the input image.
    Returns:
        tuple: (prediction_data, stats_data, path_to_saved_image)
    """
    if not os.path.exists(image_path):
        print(f"Error: Input image not found at {image_path}. Cannot run prediction.")
        return {"traffic_lights": []}, {"total_vehicles": 0, "emergency_vehicles": 0, "other_vehicles": 0, "time_saved": "0 min"}, None

    # Initialize variables for return
    prediction_data = {"traffic_lights": []} # Your JSON structure might need more here
    stats_data = {"total_vehicles": 0, "emergency_vehicles": 0, "other_vehicles": 0, "time_saved": "0 min"}
    full_saved_image_path = None

    try:
        # Run inference. save=True will save the annotated image.
        # project=PREDICTION_OUTPUT_BASE_DIR sets the base save directory to static/predictions
        # name="latest_inference" creates a subfolder within project, ensuring results go to static/predictions/latest_inference/
        results = model.predict(image_path, save=True, project=PREDICTION_OUTPUT_BASE_DIR, name="latest_inference", exist_ok=True, conf=0.25, iou=0.7, show_conf=True, show_labels=True)
        
        # --- Determine the path to the saved annotated image ---
        # YOLO typically saves the image with its original filename (or a slightly modified one)
        # inside the 'project/name' directory.
        
        # Get the directory where YOLO saved the results for this specific run
        # This information is usually available in the first result object's save_dir
        if results and hasattr(results[0], 'save_dir') and results[0].save_dir:
            output_dir = results[0].save_dir
            original_filename_base = os.path.splitext(os.path.basename(image_path))[0]
            
            # Search for the saved image file. YOLO might append a number if multiple runs.
            # E.g., 'image.jpg' or 'image.jpg_0' or 'image.jpg_1'
            # Use glob to find files starting with the original basename in the output directory
            # We look for common image extensions.
            
            search_pattern = os.path.join(output_dir, f"{original_filename_base}*")
            found_files = glob.glob(search_pattern)
            
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
            
            for found_file in found_files:
                if os.path.isfile(found_file) and found_file.lower().endswith(image_extensions):
                    full_saved_image_path = os.path.abspath(found_file) # Get the absolute path
                    print(f"DEBUG (AI.py): Found saved annotated image at: {full_saved_image_path}")
                    break # Found the image, no need to search further
            
            if full_saved_image_path is None:
                print(f"Warning (AI.py): Could not find annotated image in '{output_dir}' for '{original_filename_base}'.")
        else:
            print("Warning (AI.py): YOLO results did not contain a 'save_dir'. Cannot determine saved image path.")


        # --- Process results for statistics ---
        class_names = model.names # Get the class names from the loaded model
        if class_names is None:
            print("Warning (AI.py): Class names not found on model, using default mapping for stats.")
            # Fallback in case model.names is not available for some reason
            class_names = {0: 'ambulance', 1: 'bus', 2: 'car', 3: 'fire', 4: 'police', 5: 'truck'}


        for r in results: # Iterate over results for each image (predict can take multiple images)
            for *xyxy, conf, cls in r.boxes.data: # Iterate over detected bounding boxes
                class_id = int(cls)
                class_name = class_names.get(class_id, "unknown") # Use .get for safer access
                stats_data["total_vehicles"] += 1

                if class_name in ['ambulance', 'fire', 'police']:
                    stats_data["emergency_vehicles"] += 1
                elif class_name in ['bus', 'car', 'truck']:
                    stats_data["other_vehicles"] += 1
                # Add more detailed prediction data if needed (e.g., bounding boxes, confidence)
                # prediction_data["detected_objects"].append({
                #     "class": class_name,
                #     "confidence": float(conf),
                #     "box": [float(x) for x in xyxy]
                # })

        return prediction_data, stats_data, full_saved_image_path

    except Exception as e:
        print(f"Error during prediction in AI.py for {image_path}: {e}")
        return {"traffic_lights": []}, {"total_vehicles": 0, "emergency_vehicles": 0, "other_vehicles": 0, "time_saved": "0 min"}, None


# ----- Run training only if script is executed directly -----
if __name__ == "__main__":
    print(f"\n--- AI.py Running in Direct Mode ---")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Project Root Directory: {PROJECT_ROOT_DIR}")
    print(f"Data YAML Path for Training: {DATA_YAML_PATH}")
    print(f"Expected Weights Load Path: {LOAD_WEIGHTS_PATH}")
    print(f"Prediction Output Base Path: {PREDICTION_OUTPUT_BASE_DIR}")
    
    TRAINING_EPOCHS = 50 
    
    print(f"\nInitiating model training for {TRAINING_EPOCHS} epochs...")
    if not train_model(data_yaml_path=DATA_YAML_PATH, epochs=TRAINING_EPOCHS, model_name='yolov8n.pt'):
        print("Training did not complete successfully. Please review the errors above.")
    else:
        print("\nTraining process launched. Please monitor the console for training progress.")
        print("Once training completes, a 'best.pt' file will be in a 'trainX' folder inside 'runs/detect'.")
        print(f"Ensure LOAD_WEIGHTS_PATH is updated if the new 'best.pt' is in a different 'trainX' folder.")

    print(f"\nModel ready for inference based on loaded weights (or base model if not found).")