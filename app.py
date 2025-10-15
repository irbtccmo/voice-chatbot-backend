import os
from flask import Flask, request, send_file
from flask_cors import CORS
import logging

# --- وارد کردن همان توابع پردازشی از پروژه قبلی ---
from google.cloud import speech
from google.cloud import texttospeech
import google.generativeai as genai

# --- تنظیمات اولیه ---
# لاگین برای دیدن خطاها در سرور
logging.basicConfig(level=logging.INFO)

# مسیر فایل کلید JSON گوگل کلاد
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp_key.json'

# کلید API مدل Gemini
# کد جدید و امن
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- راه‌اندازی کلاینت‌های گوگل ---
try:
    speech_client = speech.SpeechClient()
    tts_client = texttospeech.TextToSpeechClient()
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    logging.info("کلاینت‌های گوگل با موفقیت راه‌اندازی شدند.")
except Exception as e:
    logging.error(f"خطا در راه‌اندازی کلاینت‌های گوگل: {e}")
    exit()

# --- توابع پردازشی (کپی شده از اسکریپت قبلی) ---
def speech_to_text_google(audio_content):
    logging.info("در حال تبدیل گفتار به متن...")
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS, # فرمت رایج در وب
        sample_rate_hertz=48000, # نرخ نمونه‌برداری استاندارد در وب
        language_code="fa-IR"
    )
    response = speech_client.recognize(config=config, audio=audio)
    if response.results:
        return response.results[0].alternatives[0].transcript
    return ""

def get_gemini_response(user_text):
    logging.info("در حال دریافت پاسخ از Gemini...")
    prompt = f"تو یک دستیار صوتی مفید و مهربان به نام 'آوا' هستی. به این سوال به صورت محاوره‌ای و کوتاه پاسخ بده: {user_text}"
    response = gemini_model.generate_content(prompt)
    return response.text

def text_to_speech_google(text_to_speak):
    logging.info("در حال تبدیل متن به گفتار...")
    synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
    voice = texttospeech.VoiceSelectionParams(
        language_code="fa-IR",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content

# --- راه‌اندازی سرور Flask ---
app = Flask(__name__)
CORS(app) # فعال‌سازی CORS برای اجازه دسترسی از دامنه‌های دیگر
# مسیر تست برای اطمینان از بالا بودن سرور
@app.route('/')
def index():
    return "سلام! سرور چت‌بات صوتی فعال است."

# ... بقیه کد شما از اینجا شروع می‌شود
@app.route('/process-audio', methods=['POST'])
# ...
@app.route('/process-audio', methods=['POST'])
def process_audio_endpoint():
    logging.info("درخواست جدید دریافت شد.")
    
    # دریافت فایل صوتی از درخواست وب
    audio_file = request.files.get('audio')
    if not audio_file:
        return "فایل صوتی یافت نشد", 400
    
    audio_content = audio_file.read()
    # کد فعلی شما
def process_audio_endpoint():
    # ... (کدهای دیگر)
    audio_content = audio_file.read()

    # خط جدید برای عیب‌یابی: حجم فایل دریافتی را چاپ می‌کند
    logging.info(f"Received audio file of size: {len(audio_content)} bytes")

    # ... (بقیه کد ادامه می‌یابد)
    user_text = speech_to_text_google(audio_content)
    # ...
    # مرحله ۱: تبدیل گفتار به متن
    user_text = speech_to_text_google(audio_content)
    if not user_text:
        logging.warning("متنی از صدا استخراج نشد.")
        return "متنی از صدا استخراج نشد", 400
    logging.info(f"متن شناسایی شده: {user_text}")

    # مرحله ۲: دریافت پاسخ از Gemini
    ai_text_response = get_gemini_response(user_text)
    logging.info(f"پاسخ Gemini: {ai_text_response}")

    # مرحله ۳: تبدیل پاسخ متنی به گفتار
    ai_audio_response = text_to_speech_google(ai_text_response)
    
    # ذخیره موقت فایل صوتی برای ارسال
    output_audio_path = "response.mp3"
    with open(output_audio_path, "wb") as f:
        f.write(ai_audio_response)
        
    logging.info("پاسخ صوتی آماده ارسال است.")
    # ارسال فایل صوتی به عنوان پاسخ
    return send_file(output_audio_path, mimetype="audio/mpeg")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)