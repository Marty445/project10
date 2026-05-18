import streamlit as st
import easyocr
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import pandas as pd

# ====================================
# PAGE CONFIG
# ====================================

st.set_page_config(
    page_title="Smart Food Label Scanner",
    layout="centered"
)

# ====================================
# SESSION STATE
# ====================================

if "scan_history" not in st.session_state:
    st.session_state.scan_history = []

# ====================================
# INGREDIENT DATABASE
# ====================================

INGREDIENTS_DB = {

    # HARMFUL INGREDIENTS
    "e621": {
        "name_bg": "Мононатриев глутамат",
        "name_en": "Monosodium Glutamate",
        "type": "harmful",
        "description": "Подобрител на вкуса.",
        "health": "Може да причини главоболие, високо кръвно налягане и зависимост към преработени храни.",
        "alternative": "Домашно приготвена храна с естествени подправки."
    },

    "palm oil": {
        "name_bg": "Палмово масло",
        "name_en": "Palm Oil",
        "type": "harmful",
        "description": "Евтина растителна мазнина.",
        "health": "Може да увеличи риска от сърдечни заболявания.",
        "alternative": "Продукти със слънчогледово или зехтин."
    },

    "аспартам": {
        "name_bg": "Аспартам",
        "name_en": "Aspartame",
        "type": "harmful",
        "description": "Изкуствен подсладител.",
        "health": "Може да причини главоболие и проблеми с метаболизма.",
        "alternative": "Мед или натурални подсладители."
    },

    "sugar": {
        "name_bg": "Добавена захар",
        "name_en": "Added Sugar",
        "type": "harmful",
        "description": "Подсладител.",
        "health": "Прекомерната консумация води до диабет и затлъстяване.",
        "alternative": "Плодове или натурални продукти без добавена захар."
    },

    # SAFE INGREDIENTS
    "oats": {
        "name_bg": "Овес",
        "name_en": "Oats",
        "type": "safe",
        "description": "Богат на фибри.",
        "health": "Подобрява храносмилането и сърдечното здраве.",
        "alternative": "Добър избор."
    },

    "milk": {
        "name_bg": "Мляко",
        "name_en": "Milk",
        "type": "safe",
        "description": "Източник на калций.",
        "health": "Подпомага костите и мускулите.",
        "alternative": "Добър избор."
    },

    "honey": {
        "name_bg": "Мед",
        "name_en": "Honey",
        "type": "safe",
        "description": "Натурален подсладител.",
        "health": "Съдържа антиоксиданти.",
        "alternative": "Добър избор."
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
    "title": "Умен скенер за хранителни етикети" if is_bg else "Smart Food Label Scanner",
    "upload": "Качи снимка" if is_bg else "Upload image",
    "camera": "Или използвай камера" if is_bg else "Or use camera",
    "processing": "Обработка..." if is_bg else "Processing...",
    "recognized": "Разпознат текст" if is_bg else "Recognized text",
    "results": "Резултати" if is_bg else "Results",
    "history": "История" if is_bg else "History",
    "download": "Свали историята" if is_bg else "Download history",
    "safe": "Невредна съставка" if is_bg else "Safe ingredient",
    "harmful": "Вредна съставка" if is_bg else "Harmful ingredient",
    "health": "Здравословни проблеми" if is_bg else "Health risks",
    "alternative": "По-добра алтернатива" if is_bg else "Better alternative"
}

# ====================================
# OCR READER
# ====================================

@st.cache_resource
def load_reader():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_reader()

# ====================================
# IMAGE PROCESSING
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

# ====================================
# OCR FUNCTION
# ====================================

def extract_text(image):

    processed = preprocess_image(image)

    results = reader.readtext(processed)

    extracted = []

    for result in results:
        extracted.append(result[1])

    return " ".join(extracted)

# ====================================
# INGREDIENT ANALYSIS
# ====================================

def analyze_ingredients(text):

    text_lower = text.lower()

    found = []

    for key, data in INGREDIENTS_DB.items():

        if key in text_lower:
            found.append(data)

    return found

# ====================================
# SAVE HISTORY
# ====================================

def save_history(text, results):

    st.session_state.scan_history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": text[:100],
        "ingredients_found": len(results)
    })

# ====================================
# UI
# ====================================

st.title(TEXTS["title"])

uploaded_file = st.file_uploader(
    TEXTS["upload"],
    type=["jpg", "png", "jpeg"]
)

camera_image = st.camera_input(TEXTS["camera"])

image = None

if uploaded_file:
    image = Image.open(uploaded_file)

elif camera_image:
    image = Image.open(camera_image)

# ====================================
# PROCESS
# ====================================

if image is not None:

    st.image(image, use_column_width=True)

    with st.spinner(TEXTS["processing"]):

        extracted_text = extract_text(image)

        results = analyze_ingredients(extracted_text)

        save_history(extracted_text, results)

    # OCR TEXT

    st.subheader(TEXTS["recognized"])

    st.text_area("", extracted_text, height=200)

    # RESULTS

    st.subheader(TEXTS["results"])

    if results:

        for item in results:

            if item["type"] == "harmful":

                st.error(
                    f"⚠️ {TEXTS['harmful']}: "
                    f"{item['name_bg'] if is_bg else item['name_en']}"
                )

            else:

                st.success(
                    f"✅ {TEXTS['safe']}: "
                    f"{item['name_bg'] if is_bg else item['name_en']}"
                )

            st.write(
                f"📖 {item['description']}"
            )

            st.write(
                f"❤️ {TEXTS['health']}: {item['health']}"
            )

            st.write(
                f"🥗 {TEXTS['alternative']}: {item['alternative']}"
            )

            st.divider()

    else:
        st.info("No ingredients detected.")

# ====================================
# HISTORY
# ====================================

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
        TEXTS["download"],
        csv,
        "scan_history.csv",
        "text/csv"
    )

# ====================================
# SIDEBAR
# ====================================

st.sidebar.markdown("## Features")

st.sidebar.markdown("""
- OCR Label Scanning
- Bulgarian + English
- Harmful ingredient detection
- Safe ingredient detection
- Health risk explanations
- Healthy alternatives
- Camera support
- Scan history
- CSV export
""")
