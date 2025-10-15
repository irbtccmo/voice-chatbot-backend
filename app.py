import os
from flask import Flask, request, send_file
from flask_cors import CORS
import logging

# --- وارد کردن همان توابع پردازشی از پروژه قبلی ---
from google.cloud import speech
from google.cloud import texttospeech
import google.generativeai as genai

# --- تنظیمات اولیه ---
logging.basicConfig(level=logging.INFO)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp_key.json'
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

# --- توابع پردازشی ---
def speech_to_text_google(audio_content):
    logging.info("در حال تبدیل گفتار به متن...")
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
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

# --- تابع اصلاح شده و نهایی برای تبدیل متن به گفتار ---
def text_to_speech_google(text_to_speak):
    logging.info("در حال تبدیل متن به گفتار...")
    synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
    voice = texttospeech.VoiceSelectionParams(
        language_code="fa-IR",
        name="fa-IR-Wavenet-A",  # <--- اصلاحیه اصلی اینجاست
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
CORS(app)

@app.route('/')
def index():
    return "سلام! سرور چت‌بات صوتی فعال است."

# --- تابع اصلی برای پردازش صوت (نسخه نهایی و واقعی) ---
@app.route('/process-audio', methods=['POST'])
def process_audio_endpoint():
    logging.info("درخواست جدید دریافت شد.")
    
    audio_file = request.files.get('audio')
    if not audio_file:
        logging.error("فایل صوتی یافت نشد")
        return "فایل صوتی یافت نشد", 400
    
    audio_content = audio_file.read()
    logging.info(f"فایل صوتی با حجم {len(audio_content)} بایت دریافت شد.")
    
    if len(audio_content) == 0:
        logging.warning("فایل صوتی خالی است.")
        return "فایل صوتی خالی است", 400

    try:
        user_text = speech_to_text_google(audio_content)
        if not user_text:
            logging.warning("متنی از صدا استخراج نشد.")
            ai_text_response = "متاسفم، صحبت شما را متوجه نشدم. ممکن است دوباره تکرار کنید؟"
        else:
            logging.info(f"متن شناسایی شده: {user_text}")
            ai_text_response = get_gemini_response(user_text)
        
        logging.info(f"پاسخ Gemini: {ai_text_response}")
        ai_audio_response = text_to_speech_google(ai_text_response)
        
        output_audio_path = "response.mp3"
        with open(output_audio_path, "wb") as f:
            f.write(ai_audio_response)
            
        logging.info("پاسخ صوتی آماده ارسال است.")
        return send_file(output_audio_path, mimetype="audio/mpeg")
    except Exception as e:
        logging.error(f"خطای داخلی سرور: {e}", exc_info=True)
        return "خطای داخلی در سرور رخ داد", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)