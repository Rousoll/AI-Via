import os
import json

# Input directory where the JSON files are located
input_json_dir = "json_files/"

# Output directory for the class counts files
output_dir = "class_counts"

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Iterate through all JSON files in the input directory
for filename in os.listdir(input_json_dir):
    if filename.endswith('.json'):
        # Load each JSON file
        with open(os.path.join(input_json_dir, filename)) as f:
            data = json.load(f)

        # Initialize count dict
        class_counts = {}

        # Tally counts for this JSON file
        for pred in data['predictions']:
            class_name = pred['class']
            if class_name not in class_counts:
                class_counts[class_name] = 0
            class_counts[class_name] += 1

        # Write the class counts to a JSON file in the output directory
        output_json_file = os.path.join(output_dir, f"class_counts_{filename}")
        with open(output_json_file, 'w') as f:
            json.dump(class_counts, f)

print(f'Class counts saved to the {output_dir} directory.')


