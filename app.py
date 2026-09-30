import streamlit as st
import yt_dlp
import whisper
import google.generativeai as genai
import edge_tts
import asyncio
import os
import tempfile

# --- 1. Streamlit UI Setup ---
st.title("🎬 AI Movie Recap Automation")
st.write("Douyin သို့မဟုတ် RedNote Link ထည့်ပြီး Script နှင့် အသံဖိုင်ကို အလိုအလျောက် ရယူပါ။")

# --- 2. API Key Configuration ---
# Sidebar တွင် API Key ထည့်ရန် နေရာပြုလုပ်ခြင်း
st.sidebar.header("⚙️ Settings")
api_key = st.sidebar.text_input("Gemini API Key ကို ထည့်ပါ:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Gemini Model ကို ရွေးချယ်ခြင်း (gemini-1.5-flash သည် မြန်ဆန်ပြီး ကောင်းမွန်ပါသည်)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.sidebar.warning("ကျေးဇူးပြု၍ သင်၏ Gemini API Key ကို ထည့်ပါ။")

# --- 3. Main Interface ---
video_url = st.text_input("ဒီနေရာမှာ Video Link ကို ထည့်ပါ:")

# Helper function to run edge-tts asynchronously
async def generate_audio(text, output_file):
    # မြန်မာအသံအတွက် သင့်တော်သော Voice ကို ရွေးချယ်ပါ။ (Edge-TTS တွင် မြန်မာအသံ တိုက်ရိုက်မရှိပါက အနီးစပ်ဆုံး သို့မဟုတ် အင်္ဂလိပ်အသံကို သုံးရနိုင်ပါသည်)
    # ဥပမာ: "en-US-AriaNeural" သို့မဟုတ် အခြားရရှိနိုင်သော voice
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural") 
    await communicate.save(output_file)

if st.button("Generate Script & Voice"):
    if not video_url:
        st.error("ကျေးဇူးပြု၍ Video Link ကို ထည့်ပါ။")
    elif not api_key:
        st.error("ကျေးဇူးပြု၍ ဘယ်ဘက်အခြမ်း (Sidebar) တွင် Gemini API Key ကို ထည့်ပါ။")
    else:
        with st.spinner("လုပ်ငန်းစဉ် စတင်နေပါပြီ... ခဏစောင့်ပါ... ⏳"):
            try:
                # --- Step 1: Download Video/Audio using yt-dlp ---
                st.info("📥 ဗီဒီယိုမှ အသံဖိုင်ကို ရယူနေပါသည်...")
                temp_dir = tempfile.mkdtemp()
                audio_path = os.path.join(temp_dir, "audio.mp3")
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': audio_path,
                    'quiet': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(video_url, download=True)

                # --- Step 2: Transcribe Audio using Whisper ---
                st.info("📝 အသံကို စာသားအဖြစ် ပြောင်းလဲနေပါသည် (Whisper AI)...")
                # Load a small model for faster processing on Streamlit Cloud
                whisper_model = whisper.load_model("base") 
                result = whisper_model.transcribe(audio_path)
                original_text = result["text"]
                
                st.success("✅ မူရင်းစာသား ရယူပြီးပါပြီ။")
                with st.expander("မူရင်းစာသား (Original Transcript) ကို ကြည့်ရန်"):
                    st.write(original_text)

                # --- Step 3: Generate Recap Script using Gemini ---
                st.info("✨ Gemini AI ဖြင့် မြန်မာ ဇာတ်ညွှန်း ပြန်လည်ရေးသားနေပါသည်...")
                prompt = f"""
                အောက်ပါစာသားသည် ရုပ်ရှင် သို့မဟုတ် ဗီဒီယိုတစ်ခုမှ ထုတ်ယူထားသော စာသားဖြစ်သည်။ 
                ယင်းစာသားကို အခြေခံ၍ ဆွဲဆောင်မှုရှိသော၊ စိတ်ဝင်စားဖွယ်ကောင်းသော 'Movie Recap' ဇာတ်ညွှန်းတစ်ခုကို 'မြန်မာဘာသာ' ဖြင့် ပြန်လည်ရေးသားပေးပါ။
                ကြည့်ရှုသူများကို ဆွဲဆောင်နိုင်မည့် အသုံးအနှုန်းများကို အသုံးပြုပါ။
                
                မူရင်းစာသား:
                {original_text}
                """
                response = model.generate_content(prompt)
                myanmar_script = response.text
                
                st.success("✅ မြန်မာဇာတ်ညွှန်း ရေးသားပြီးပါပြီ။")
                st.subheader("📜 သင့်အတွက် AI ရေးပေးသော ဇာတ်ညွှန်း")
                st.write(myanmar_script)

                # --- Step 4: Text-to-Speech using Edge-TTS ---
                st.info("🔊 မြန်မာဇာတ်ညွှန်းကို အသံဖိုင်အဖြစ် ပြောင်းလဲနေပါသည်...")
                output_audio_path = os.path.join(temp_dir, "recap_voice.mp3")
                
                # Run the async function in the synchronous Streamlit environment
                asyncio.run(generate_audio(myanmar_script, output_audio_path))
                
                st.success("✅ အသံဖိုင် ဖန်တီးပြီးပါပြီ။")
                
                # အသံဖိုင်ကို နားထောင်ရန်နှင့် ဒေါင်းလုဒ်လုပ်ရန် ပြသခြင်း
                st.audio(output_audio_path, format="audio/mp3")
                
                with open(output_audio_path, "rb") as file:
                    st.download_button(
                        label="⬇️ အသံဖိုင် (Audio) ကို ဒေါင်းလုဒ်လုပ်ရန်",
                        data=file,
                        file_name="movie_recap_voice.mp3",
                        mime="audio/mp3"
                    )

            except Exception as e:
                st.error(f"အမှားအယွင်း ဖြစ်ပေါ်သွားပါသည်: {e}")
