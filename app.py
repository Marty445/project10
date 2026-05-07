import streamlit as st
import easyocr
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import pandas as pd

# ====================================
# STREAMLIT CONFIG
# ====================================

st.set_page_config(
    page_title="Food Ingredient Scanner",
    layout="centered"
)

# ====================================
# HISTORY INIT
# ====================================

if "scan_history" not in st.session_state:
    st.session_state.scan_history = []

# ====================================
# HARMFUL INGREDIENTS
# ====================================

HARMFUL_INGREDIENTS = {
    "bg": {
        "e621": "Мононатриев глутамат (E621)",
        "палмово масло": "Палмово масло",
        "аспартам": "Аспартам",
        "e250": "Натриев нитрит (E250)",
        "e951": "Аспартам (E951)",
        "захар": "Добавена захар",
        "глюкозо-фруктозен сироп": "Глюкозо-фруктозен сироп",
    },
    "en": {
        "e621": "Monosodium Glutamate (E621)",
        "palm oil": "Palm Oil",
        "aspartame": "Aspartame",
        "e250": "Sodium Nitrite (E250)",
        "e951": "Aspartame (E951)",
        "sugar": "Added Sugar",
        "glucose-fructose syrup": "Glucose-Fructose Syrup",
    }
}

# ====================================
# LANGUAGE
# ====================================

language = st.sidebar.selectbox(
    "Избери език / Select language",
    ["Български", "English"]
)

is_bg = language == "Български"

TEXTS = {
    "title": "Скенер за вредни съставки" if is_bg else "Harmful Ingredient Scanner",
    "upload": "Качи снимка" if is_bg else "Upload image",
    "camera": "Или използвай камера" if is_bg else "Or use camera",
    "processing": "Обработка..." if is_bg else "Processing...",
    "recognized": "Разпознат текст" if is_bg else "Recognized text",
    "found": "Намерени съставки" if is_bg else "Detected ingredients",
    "not_found": "Няма открити вредни съставки." if is_bg else "No harmful ingredients detected.",
    "warning": "⚠️ Внимание!" if is_bg else "⚠️ Warning!",
    "confidence": "OCR Accuracy Score" if is_bg else "OCR Confidence Score",
    "history": "История на сканиранията" if is_bg else "Scan History",
    "download": "Свали историята" if is_bg else "Download history",
}

# ====================================
# OCR READER
# ====================================

@st.cache_resource
def load_reader():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_reader()

# ====================================
# FUNCTIONS
# ====================================

def preprocess_image(image):
    img = np.array(image)

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh


def extract_text_and_confidence(image):

    processed = preprocess_image(image)

    results = reader.readtext(processed)

    extracted_text = []
    confidence_scores = []

    for result in results:
        text = result[1]
        confidence = result[2]

        extracted_text.append(text)
        confidence_scores.append(confidence)

    final_text = " ".join(extracted_text)

    avg_confidence = (
        sum(confidence_scores) / len(confidence_scores)
        if confidence_scores else 0
    )

    return final_text, avg_confidence


def find_harmful_ingredients(text):

    text_lower = text.lower()

    found = []

    for key, value in HARMFUL_INGREDIENTS["bg"].items():
        if key in text_lower:
            found.append(value)

    for key, value in HARMFUL_INGREDIENTS["en"].items():
        if key in text_lower:
            found.append(value)

    return list(set(found))


def save_scan_to_history(text, ingredients, confidence):

    st.session_state.scan_history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "confidence": round(confidence * 100, 2),
        "ingredients": ", ".join(ingredients) if ingredients else "None",
        "text": text[:150]
    })

# ====================================
# UI
# ====================================

st.title(TEXTS["title"])

uploaded_file = st.file_uploader(
    TEXTS["upload"],
    type=["jpg", "jpeg", "png"]
)

camera_image = st.camera_input(TEXTS["camera"])

image = None

if uploaded_file is not None:
    image = Image.open(uploaded_file)

elif camera_image is not None:
    image = Image.open(camera_image)

# ====================================
# PROCESS IMAGE
# ====================================

if image is not None:

    st.image(image, caption="Uploaded Image", use_column_width=True)

    with st.spinner(TEXTS["processing"]):

        extracted_text, confidence = extract_text_and_confidence(image)

        harmful_found = find_harmful_ingredients(extracted_text)

        save_scan_to_history(
            extracted_text,
            harmful_found,
            confidence
        )

    # ====================================
    # OCR CONFIDENCE SCORE
    # ====================================

    st.subheader(TEXTS["confidence"])

    score_percent = round(confidence * 100, 2)

    st.progress(min(int(score_percent), 100))

    if score_percent >= 85:
        st.success(f"{score_percent}%")
    elif score_percent >= 60:
        st.warning(f"{score_percent}%")
    else:
        st.error(f"{score_percent}%")

    # ====================================
    # RECOGNIZED TEXT
    # ====================================

    st.subheader(TEXTS["recognized"])

    st.text_area(
        "",
        extracted_text,
        height=200
    )

    # ====================================
    # HARMFUL INGREDIENTS
    # ====================================

    st.subheader(TEXTS["found"])

    if harmful_found:
        for ingredient in harmful_found:
            st.warning(f"{TEXTS['warning']} {ingredient}")
    else:
        st.success(TEXTS["not_found"])

# ====================================
# HISTORY SECTION
# ====================================

st.divider()

st.subheader(TEXTS["history"])

if st.session_state.scan_history:

    history_df = pd.DataFrame(
        st.session_state.scan_history[::-1]
    )

    st.dataframe(
        history_df,
        use_container_width=True
    )

    csv = history_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label=TEXTS["download"],
        data=csv,
        file_name="scan_history.csv",
        mime="text/csv"
    )

else:
    st.info("No scans yet.")

# ====================================
# SIDEBAR INFO
# ====================================

st.sidebar.markdown("## Features")

st.sidebar.markdown("""
- OCR via EasyOCR
- Bulgarian + English support
- Harmful ingredient detection
- Camera support
- OCR confidence score
- Scan history
- CSV export
""")
