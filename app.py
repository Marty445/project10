import streamlit as st
import easyocr
import cv2
import numpy as np
from PIL import Image
import re

# =========================
# НАСТРОЙКИ
# =========================

st.set_page_config(
    page_title="Food Ingredient Scanner",
    layout="centered"
)

# Вредни / нежелани съставки
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

# =========================
# ЕЗИК
# =========================

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
}

# =========================
# OCR
# =========================

@st.cache_resource
def load_reader():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_reader()

# =========================
# ФУНКЦИИ
# =========================

def preprocess_image(image):
    img = np.array(image)

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    # Подобряване на OCR
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


def extract_text(image):
    processed = preprocess_image(image)

    results = reader.readtext(processed, detail=0)

    text = " ".join(results)

    return text


def find_harmful_ingredients(text):
    text_lower = text.lower()

    found = []

    # BG
    for key, value in HARMFUL_INGREDIENTS["bg"].items():
        if key in text_lower:
            found.append(value)

    # EN
    for key, value in HARMFUL_INGREDIENTS["en"].items():
        if key in text_lower:
            found.append(value)

    return list(set(found))


# =========================
# UI
# =========================

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

if image is not None:

    st.image(image, caption="Image", use_column_width=True)

    with st.spinner(TEXTS["processing"]):

        extracted_text = extract_text(image)

        harmful_found = find_harmful_ingredients(extracted_text)

    st.subheader(TEXTS["recognized"])
    st.text_area("", extracted_text, height=200)

    st.subheader(TEXTS["found"])

    if harmful_found:
        for ingredient in harmful_found:
            st.warning(f"{TEXTS['warning']} {ingredient}")
    else:
        st.success(TEXTS["not_found"])
