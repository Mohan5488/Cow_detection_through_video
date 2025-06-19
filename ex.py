import cv2
import os
import tempfile
import streamlit as st
from ultralytics import YOLO
from datetime import timedelta
import streamlit.components.v1 as components

def render_carousel(images, height=300):
    html = """
    <div style="display:flex; overflow-x:auto; gap: 10px; height: {height}px;">
    """.format(height=height)
    for img_path in images:
        html += f"""
        <div style="flex:0 0 auto;">
            <img src="data:image/jpeg;base64,{encode_image(img_path)}" style="height:{height}px; border-radius: 10px;" />
        </div>
        """
    html += "</div>"
    return html


def encode_image(img_path):
    """Encode image as base64 for inline HTML."""
    import base64
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

st.title("🐄 Cow Detection in Video")
st.write("Upload a video to detect cows and extract grouped detection intervals.")

uploaded_file = st.file_uploader("Upload a video", type=["mp4", "avi", "mov"])

if uploaded_file:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())

    st.video(tfile.name)
    st.write("Processing... Please wait.")

    model = YOLO("yolo11n.pt")

    cap = cv2.VideoCapture(tfile.name)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = 10
    frame_num = 0

    output_dir = "cow_frames"
    os.makedirs(output_dir, exist_ok=True)

    grouped_detections = []
    current_event = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % frame_interval == 0:
            results = model.predict(frame, classes=[19], verbose=False)
            boxes = results[0].boxes

            time_sec = frame_num / fps
            time_str = str(timedelta(seconds=int(time_sec)))

            if len(boxes) > 0:
                frame_path = os.path.join(output_dir, f"frame_{frame_num}.jpg")
                cv2.imwrite(frame_path, frame)

                if current_event is None:
                    current_event = {
                        "start": time_str,
                        "end": time_str,
                        "images": [frame_path]
                    }
                else:
                    current_event["end"] = time_str
                    current_event["images"].append(frame_path)
            else:
                if current_event:
                    grouped_detections.append(current_event)
                    current_event = None

        frame_num += 1
        

    cap.release()

    if current_event:
        grouped_detections.append(current_event)
        

    st.success(f"✅ Done! Found {len(grouped_detections)} cow detection intervals.")

    if grouped_detections:
        st.write("### 🕒 Cow Detection Intervals with Image Carousels")

        for i, event in enumerate(grouped_detections, 1):
            st.subheader(f"Event {i}: {event['start']} to {event['end']}")
            html = render_carousel(event["images"], height=250)
            components.html(html, height=280)
    else:
        st.warning("No cow detection intervals found.")