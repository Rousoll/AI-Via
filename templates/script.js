document.addEventListener("DOMContentLoaded", function() {
    fetch("/api/traffic_analytics")
        .then(res => res.json())
        .then(data => {
            document.getElementById("traffic-analytics").innerText =
                `Traffic Flow: ${data.traffic_flow}\nAverage Speed: ${data.average_speed} km/h`;
        });

    fetch("/api/recent_intersection")
        .then(res => res.json())
        .then(data => {
            document.getElementById("recent-intersection").innerText =
                `Intersection ID: ${data.intersection_id}\nVehicles: ${data.vehicles}`;
        });

    fetch("/api/live_simulation")
        .then(res => res.json())
        .then(data => {
            const simDiv = document.getElementById("live-simulation");
            let text = "Live Simulation\n";
            data.traffic_lights.forEach(t => {
                text += `Light ${t.id}: ${t.status} (Waiting: ${t.waiting_time}s)\n`;
            });
            simDiv.innerText = text;
            document.getElementById("time-saved").innerText = `Time Saved: ${data.time_saved} sec`;
            document.getElementById("emergency-rate").innerText = `Emergency Response Rate: ${data.emergency_response_rate}`;
        });

    fetch("/api/ai_logs")
        .then(res => res.json())
        .then(data => {
            document.getElementById("ai-logs").innerText =
                `Decision: ${data.decision}\nTime: ${data.timestamp}`;
        });

    // Upload intersection image
    const uploadInput = document.getElementById("upload-image");
    uploadInput.addEventListener("change", () => {
        const file = uploadInput.files[0];
        const formData = new FormData();
        formData.append("image", file);

        fetch("/api/upload_intersection", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            alert(`Upload status: ${data.status}`);
        });
    });
});
