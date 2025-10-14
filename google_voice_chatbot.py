import os
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import playsound

# --- کتابخانه‌های گوگل ---
from google.cloud import speech
from google.cloud import texttospeech
import google.generativeai as genai

# --- تنظیمات اولیه ---

# مسیر فایل کلید JSON که از گوگل کلاد دانلود کردید
# این خط به برنامه می‌گوید که از این کلید برای دسترسی به حساب شما استفاده کند
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp_key.json'

# کلید API مدل Gemini را از Google AI Studio دریافت و در اینجا قرار دهید
# به https://aistudio.google.com/app/apikey بروید
GEMINI_API_KEY = "AIzaSyC4FCvBDNrDjNbImeEyVLQkcoo6NaBoL4s"

# تنظیمات ضبط صدا
SAMPLE_RATE = 44100
RECORDING_FILENAME = "user_audio.wav"

# --- راه‌اندازی کلاینت‌های گوگل ---
try:
    # کلاینت برای تبدیل گفتار به متن
    speech_client = speech.SpeechClient()
    
    # کلاینت برای تبدیل متن به گفتار
    tts_client = texttospeech.TextToSpeechClient()
    
    # تنظیم مدل Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest') # استفاده از مدل سریع جمینای
    
    print("کلاینت‌های گوگل با موفقیت راه‌اندازی شدند.")
except Exception as e:
    print(f"خطا در راه‌اندازی: آیا فایل gcp_key.json در پوشه است؟ خطا: {e}")
    exit()

def record_audio(duration=5):
    """صدا را از میکروفون ضبط کرده و در یک فایل ذخیره می‌کند."""
    print(f"شروع ضبط به مدت {duration} ثانیه...")
    recording = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    write(RECORDING_FILENAME, SAMPLE_RATE, recording)
    print(f"صدا در فایل '{RECORDING_FILENAME}' ذخیره شد.")
    return RECORDING_FILENAME

def speech_to_text_google(audio_file_path):
    """فایل صوتی را با استفاده از Google Speech-to-Text به متن فارسی تبدیل می‌کند."""
    print("در حال ارسال صدا به گوگل برای تبدیل به متن...")
    try:
        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="fa-IR"  # زبان فارسی
        )

        response = speech_client.recognize(config=config, audio=audio)
        
        if response.results:
            text = response.results[0].alternatives[0].transcript
            print(f"متن شناسایی شده: {text}")
            return text
        else:
            print("گوگل نتوانست متنی را از صدا تشخیص دهد.")
            return ""
    except Exception as e:
        print(f"خطا در تبدیل گفتار به متن: {e}")
        return ""

def get_gemini_response(user_text):
    """پاسخ متنی هوشمندانه از مدل Gemini دریافت می‌کند."""
    print("در حال دریافت پاسخ از Gemini...")
    try:
        # می‌توانید شخصیت دستیار را در اینجا تعریف کنید
        prompt = f"تو یک دستیار صوتی مفید و مهربان به نام 'آوا' هستی. به این سوال به صورت محاوره‌ای و کوتاه پاسخ بده: {user_text}"
        response = gemini_model.generate_content(prompt)
        ai_response_text = response.text
        print(f"پاسخ Gemini: {ai_response_text}")
        return ai_response_text
    except Exception as e:
        print(f"خطا در دریافت پاسخ از Gemini: {e}")
        return "متاسفانه در ارتباط با جمینای مشکلی پیش آمده."

def text_to_speech_google(text_to_speak):
    """متن را با استفاده از Google Text-to-Speech به صدا تبدیل کرده و پخش می‌کند."""
    print("در حال تبدیل متن به صدا و پخش آن...")
    try:
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

        # فایل صوتی دریافت شده از گوگل را ذخیره می‌کنیم
        audio_filename = "response_audio.mp3"
        with open(audio_filename, "wb") as out:
            out.write(response.audio_content)
            print(f"فایل صوتی در '{audio_filename}' ذخیره شد.")

        # فایل ذخیره شده را با playsound پخش می‌کنیم
        playsound.playsound(audio_filename)

    except Exception as e:
        print(f"خطا در تبدیل متن به گفتار: {e}")

def main():
    """حلقه اصلی برنامه برای اجرای چت‌بات صوتی."""
    print("\nچت‌بات صوتی 'آوا' با قدرت گوگل آماده است.")
    while True:
        input("برای شروع مکالمه، کلید Enter را فشار دهید...")
        
        audio_file = record_audio(duration=5)
        
        user_message = speech_to_text_google(audio_file)
        
        if user_message:
            ai_message = get_gemini_response(user_message)
            text_to_speech_google(ai_message)
        else:
            print("پیامی برای پردازش وجود ندارد. لطفاً دوباره تلاش کنید.")

if __name__ == "__main__":
    main()