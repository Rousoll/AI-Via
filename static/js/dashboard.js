// dashboard.js

// Function to update the last updated timestamp (placed globally as it's used immediately)
function updateLastUpdateTime() {
  const now = new Date();
  const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  document.getElementById('last-update').textContent = timeString;
}

/* SMART TRAFFIC SIMULATION  --- NEW ADDITION */

function startSmartSimulation(){
  fetch('/api/start-simulation')
    .then(r => r.json())
    .then(data => {
      console.log('Simulation data:', data);

      // place each image in its slot
      Object.entries(data.signals).forEach(([signal, obj]) => {
        const imgTag = document.getElementById(signal + '_img');
        if (imgTag) {
          imgTag.src = obj.image_url + '?t=' + Date.now(); // bust cache
        }
      });

      // remove green class from all
      document.querySelectorAll('.traffic-light').forEach(div => div.classList.remove('green'));

      // highlight green light
      const greenSignal = document.getElementById(data.go_first);
      if (greenSignal) {
        greenSignal.classList.add('green');
      }
    })
    .catch(err => console.error('Error in simulation:', err));
}

// run every 4 seconds
setInterval(startSmartSimulation, 4000);
startSmartSimulation();

// Update time every second
setInterval(updateLastUpdateTime, 1000);
updateLastUpdateTime(); // Call immediately on load

// Function to fetch and update live stats (placed globally)
async function fetchLiveStats() {
  try {
    const response = await fetch('/api/live-stats');
    const data = await response.json();

    document.getElementById('total-vehicles').textContent = data.total_vehicles;
    document.getElementById('emergency-vehicles').textContent = data.emergency_vehicles;
    document.getElementById('other-vehicles').textContent = data.other_vehicles;
    // Assuming 'time-saved' is also part of live stats if you implement it
    // document.getElementById('time-saved').textContent = data.time_saved;

    // Update alerts
    const alertsContainer = document.getElementById('alerts-container');
    alertsContainer.innerHTML = ''; // Clear previous alerts
    if (data.alerts && data.alerts.length > 0) {
      data.alerts.forEach(alert => {
        const p = document.createElement('p');
        p.textContent = alert;
        alertsContainer.appendChild(p);
      });
    } else {
      alertsContainer.textContent = "No alerts currently.";
    }

  } catch (error) {
    console.error('Error fetching live stats:', error);
  }
}

// Fetch live stats every 5 seconds (adjust as needed)
setInterval(fetchLiveStats, 5000);
fetchLiveStats(); // Fetch immediately on load


// --- Main DOMContentLoaded Listener ---
document.addEventListener('DOMContentLoaded', () => {
  // --- Element References ---
  const imageUploadInput = document.getElementById('image-upload');
  const uploadBtn = document.getElementById('upload-btn');
  const uploadResultDiv = document.getElementById('upload-result');
  const predictedImageElement = document.getElementById('predicted-image');
  const predictionDetailsDiv = document.getElementById('prediction-details'); // For any text details
  const predTotalVehicles = document.getElementById('pred-total-vehicles');
  const predEmergencyVehicles = document.getElementById('pred-emergency-vehicles');
  const predOtherVehicles = document.getElementById('pred-other-vehicles');

  const confidenceThreshold = document.getElementById('confidence-threshold');
  const confidenceValueSpan = document.getElementById('confidence-value');
  const simulationSpeed = document.getElementById('simulation-speed');
  const simulationSpeedValueSpan = document.getElementById('simulation-speed-value');
  const applyControlsBtn = document.getElementById('apply-controls');

  // --- Event Listeners ---

  // Confidence Threshold Slider
  confidenceThreshold.addEventListener('input', () => {
    confidenceValueSpan.textContent = confidenceThreshold.value;
  });

  // Simulation Speed Slider
  simulationSpeed.addEventListener('input', () => {
    simulationSpeedValueSpan.textContent = `${simulationSpeed.value}x`;
  });

  // Apply Controls Button
  applyControlsBtn.addEventListener('click', async () => {
    const confidence = parseFloat(confidenceThreshold.value);
    const speed = parseFloat(simulationSpeed.value);

    try {
      const response = await fetch('/api/apply-controls', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confidence: confidence, speed: speed }),
      });
      const result = await response.json();
      console.log('Control apply response:', result.message);
      alert(result.message);
    } catch (error) {
      console.error('Error applying controls:', error);
      alert('Failed to apply controls.');
    }
  });

  // Image Upload and Prediction Button
  uploadBtn.addEventListener('click', async () => {
    const file = imageUploadInput.files[0];
    if (!file) {
      uploadResultDiv.textContent = 'Please select an image to upload.';
      uploadResultDiv.style.color = 'orange';
      return;
    }

    uploadResultDiv.textContent = 'Uploading and predicting...';
    uploadResultDiv.style.color = 'blue';

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch('/api/upload-image', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        uploadResultDiv.textContent = 'Prediction successful!';
        uploadResultDiv.style.color = 'green';

        // Update the image source
        if (result.image_url) {
          predictedImageElement.src = result.image_url;
          predictedImageElement.style.display = 'block'; // Make image visible
        } else {
          predictedImageElement.style.display = 'none';
          console.error("No image_url received from prediction.");
          uploadResultDiv.textContent = 'Prediction successful, but image URL missing!';
          uploadResultDiv.style.color = 'orange';
        }

        // Update prediction statistics (for the specific uploaded image)
        if (result.stats) {
          predTotalVehicles.textContent = result.stats.total_vehicles;
          predEmergencyVehicles.textContent = result.stats.emergency_vehicles;
          predOtherVehicles.textContent = result.stats.other_vehicles;
          // You can also add prediction.traffic_lights here if you populate it in Flask
          // predictionDetailsDiv.textContent = JSON.stringify(result.prediction, null, 2);
        } else {
          console.warn("No stats received from prediction.");
        }

      } else {
        uploadResultDiv.textContent = `Prediction failed: ${result.error || 'Unknown error'}`;
        uploadResultDiv.style.color = 'red';
        predictedImageElement.style.display = 'none'; // Hide image on failure
      }
    } catch (error) {
      console.error('Error during upload or prediction:', error);
      uploadResultDiv.textContent = 'An error occurred during prediction.';
      uploadResultDiv.style.color = 'red';
      predictedImageElement.style.display = 'none'; // Hide image on failure
    }
  });

  // NOTE: renderPrediction function is not strictly needed for this current setup
  // as you are directly putting the image and stats.
  // If you decide to add more structured prediction details, you can use it.
  /*
  function renderPrediction(prediction) {
      if (!prediction.traffic_lights) return '<p>No traffic lights detected.</p>';
      return prediction.traffic_lights.map(light =>
          `<div class="traffic-light-result">
              <strong>Location:</strong> ${light.location || 'N/A'}<br>
              <strong>State:</strong> ${light.state || 'Unknown'}
          </div>`
      ).join('');
  }
  */

}); // End of the single DOMContentLoaded listener