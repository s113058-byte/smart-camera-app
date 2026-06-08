import ctypes
ctypes.CDLL("libGL.so.1", mode=ctypes.RTLD_GLOBAL)

import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from PIL import Image, ImageEnhance

# --- 網頁頁面基本設定 ---
st.set_page_config(page_title="智慧拍照 App", layout="wide")
st.title("📸 智慧拍照 App")
st.caption("專題組員: 01, 03, 04, 05, 09, 17, 38 | 產品特色：造福穆斯林和窮人")

# --- 初始化新版 MediaPipe Tasks 手勢辨識器 ---
@st.cache_resource
def load_recognizer():
    base_options = python.BaseOptions(model_asset_path='gesture_recognizer.task')
    options = vision.GestureRecognizerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE
    )
    return vision.GestureRecognizer.create_from_options(options)

try:
    recognizer = load_recognizer()
except Exception as e:
    st.error(f"模型載入失敗，請確認 gesture_recognizer.task 是否與 app.py 在同一個 GitHub 目錄下。錯誤訊息: {e}")

# --- 輔助函式：使用新版資料結構辨識手勢與數字 ---
def analyze_hand_gesture(mp_image):
    recognition_result = recognizer.recognize(mp_image)
    if not recognition_result.gestures or len(recognition_result.gestures) == 0:
        return 0

    top_gesture = recognition_result.gestures[0][0].category_name
    
    if top_gesture == "Thumb_Up":
        return "LIKE"

    if len(recognition_result.hand_landmarks) == 0:
        return 0
        
    hand_landmarks = recognition_result.hand_landmarks[0]
    tip_ids = [4, 8, 12, 16, 20]
    fingers = []

    if hand_landmarks[tip_ids[0]].x < hand_landmarks[tip_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    for id in range(1, 5):
        if hand_landmarks[tip_ids[id]].y < hand_landmarks[tip_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return sum(fingers)

# --- 輔助函式：動態特效生成器 (網頁靜態模擬多幀) ---
def apply_dynamic_effect(frame, gesture):
    h, w, c = frame.shape
    
    if gesture == 1:
        cv2.putText(frame, "Background: Mecca", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        # 繪製模擬穆斯林人群
        for i in range(3):
            pos_x = int(w * 0.2 + i * 150)
            cv2.circle(frame, (pos_x, h - 80), 20, (200, 100, 50), -1)
            cv2.putText(frame, "Muslim", (pos_x - 25, h - 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
    elif gesture == 2:
        frame[:, :, 2] = cv2.add(frame[:, :, 2], 50) # 加紅
        cv2.putText(frame, "Background: Mars", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # 繪製隕石
        cv2.circle(frame, (int(w*0.5), int(h*0.3)), 30, (0, 165, 255), -1)
        cv2.putText(frame, "Meteor!", (int(w*0.5) - 35, int(h*0.3) - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
    elif gesture == 3:
        frame[:, :, 1] = cv2.add(frame[:, :, 1], 30) # 加黃
        frame[:, :, 2] = cv2.add(frame[:, :, 2], 30)
        cv2.putText(frame, "Background: Pyramid", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        # 繪製沙塵暴線條
        for i in range(0, h, 60):
            cv2.line(frame, (0, i), (w, i + 30), (200, 220, 250), 2)
            
    elif gesture in [4, 5]:
        bg_name = "Antarctica" if gesture == 4 else "Mt. Everest"
        cv2.putText(frame, f"Background: {bg_name}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        # 繪製雪花
        for i in range(30):
            sx = int(np.sin(i) * w * 0.5 + w * 0.5)
            sy = int((i * 25) % h)
            cv2.circle(frame, (sx, sy), 4, (255, 255, 255), -1)
            
    return frame

# --- 輔助函式：修圖功能 ---
def apply_beauty_effects(image, slim, whiten, makeup):
    img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    if whiten > 0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.0 + (whiten / 100) * 0.5)
    open_cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    if slim > 0:
        open_cv_img = cv2.bilateralFilter(open_cv_img, 9, 75, 75)
    if makeup:
        pink_overlay = np.full(open_cv_img.shape, (180, 105, 255), dtype=np.uint8)
        open_cv_img = cv2.addWeighted(open_cv_img, 0.9, pink_overlay, 0.1, 0)
    return open_cv_img

# --- Streamlit 網頁佈局 (完美還原 UI 規格設計) ---
st.sidebar.header("💄 後製修圖功能專區")
slim_val = st.sidebar.slider("瘦臉程度", 0, 100, 0)
whiten_val = st.sidebar.slider("美白程度", 0, 100, 0)
makeup_on = st.sidebar.checkbox("開啟日常妝容")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📹 鏡頭影像即時顯示處")
    # 使用網頁端內建相機元件
    img_file = st.camera_input("請對準鏡頭拍攝一張帶有手勢的照片")

with col2:
    st.subheader("🖼️ 瀏覽與下載圖片")
    
    if img_file is not None:
        # 將上傳的圖片轉為 OpenCV 格式
        bytes_data = img_file.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        
        # 轉成 MediaPipe 格式進行辨識
        rgb_frame = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # 分析手勢
        gesture_result = analyze_hand_gesture(mp_image)
        
        # 根據手勢決定提示或套用特效
        if gesture_result == "LIKE":
            st.success("👍 偵測到『比讚』！成功觸發快門拍照！")
        elif gesture_result in [1, 2, 3, 4, 5]:
            st.info(f"🖐️ 偵測到數字手勢：{gesture_result}，正在動態生成背景特效...")
            cv_img = apply_dynamic_effect(cv_img, gesture_result)
        else:
            st.warning("未偵測到特定手勢，你可以試著比出 1~5 或比讚。")
            
        # 套用美顏修圖功能
        processed_img = apply_beauty_effects(cv_img, slim_val, whiten_val, makeup_on)
        
        # 顯示最終成果圖
        final_rgb = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
        st.image(final_rgb, caption="✨ 智慧處理後的精美照片", use_container_width=True)
        
        # 提供下載按鈕
        pil_save = Image.fromarray(final_rgb)
        pil_save.save("output.png")
        with open("output.png", "rb") as file:
            st.download_button(label="💾 下載這張照片", data=file, file_name="smart_photo_result.png")
    else:
        st.write("👈 請先在左側點擊「Take Photo」拍攝一張照片，右側將會即時產生特效與提供修圖下載！")
