import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import os
import tempfile

# --- 1. Streamlit UI Setup ---
st.title("🎬 AI Movie Recap Automation")
st.write("ဗီဒီယိုဖိုင်ကို တိုက်ရိုက်တင်ပြီး Gemini AI ဖြင့် မြန်မာ ဇာတ်ညွှန်းနှင့် အသံဖိုင်ကို ရယူပါ။")

# --- 2. API Key Configuration ---
st.sidebar.header("⚙️ Settings")
api_key = st.sidebar.text_input("Gemini API Key ကို ထည့်ပါ:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Gemini 1.5 Flash သည် ဗီဒီယိုဖိုင်များကို တိုက်ရိုက်ဖတ်နိုင်သည်
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.sidebar.warning("ကျေးဇူးပြု၍ သင်၏ Gemini API Key ကို ထည့်ပါ။")

# --- 3. Main Interface (File Upload) ---
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင် ရွေးချယ်ပါ (MP4, MOV စသည်ဖြင့်):", type=['mp4', 'mov', 'avi', 'mkv'])

async def generate_audio(text, output_file):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural") 
    await communicate.save(output_file)

if st.button("Generate Script & Voice"):
    if not uploaded_file:
        st.error("ကျေးဇူးပြု၍ ဗီဒီယိုဖိုင်တစ်ခုခုကို အရင် Upload တင်ပါ။")
    elif not api_key:
        st.error("ကျေးဇူးပြု၍ ဘယ်ဘက်အခြမ်း (Sidebar) တွင် Gemini API Key ကို ထည့်ပါ။")
    else:
        with st.spinner("Gemini AI ဖြင့် ဗီဒီယိုကို လေ့လာပြီး ဇာတ်ညွှန်းထုတ်နေပါပြီ... ခဏစောင့်ပါ... ⏳"):
            try:
                # ဗီဒီယိုဖိုင်ကို ယာယီသိမ်းဆည်းခြင်း
                temp_dir = tempfile.mkdtemp()
                video_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.info("📤 ဗီဒီယိုဖိုင်ကို Gemini AI သို့ ပို့ဆောင်နေပါသည်...")
                
                # Gemini သို့ ဖိုင်တင်ခြင်း (File API)
                video_file = genai.upload_file(video_path)
                
                # ဖိုင်အဆင်သင့်ဖြစ်သည်အထိ စောင့်ဆိုင်းခြင်း
                import time
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)

                if video_file.state.name == "FAILED":
                    raise Exception("ဗီဒီယိုဖိုင် လုပ်ဆောင်မှု ကျရှုံးသွားပါသည်။")

                # --- Generate Movie Recap Script ---
                st.info("✨ ဆွဲဆောင်မှုရှိသော မြန်မာ Movie Recap ဇာတ်ညွှန်း ရေးသားနေပါသည်...")
                prompt = """
                ဤဗီဒီယိုကို ကြည့်ရှုပြီး ၎င်းပါ ဇာတ်လမ်းအကြောင်းအရာများကို အခြေခံကာ စိတ်ဝင်စားဖွယ်ကောင်းပြီး ဆွဲဆောင်မှုရှိသော 'Movie Recap' ဇာတ်ညွှန်းတစ်ခုကို 'မြန်မာဘာသာ' ဖြင့် ရေးသားပေးပါ။
                ကြည့်ရှုသူများကို ဖမ်းစားနိုင်မည့် အသုံးအနှုန်းများဖြင့် အပိုင်းလိုက် စနစ်တကျ ဖန်တီးပေးပါ။
                """
                
                response = model.generate_content([video_file, prompt])
                myanmar_script = response.text
                
                st.success("✅ မြန်မာဇာတ်ညွှန်း ရေးသားပြီးပါပြီ။")
                st.subheader("📜 သင့်အတွက် AI ရေးပေးသော မြန်မာဇာတ်ညွှန်း")
                st.write(myanmar_script)

                # --- Text-to-Speech using Edge-TTS ---
                st.info("🔊 မြန်မာဇာတ်ညွှန်းကို အသံဖိုင်အဖြစ် ပြောင်းလဲနေပါသည်...")
                output_audio_path = os.path.join(temp_dir, "recap_voice.mp3")
                
                asyncio.run(generate_audio(myanmar_script, output_audio_path))
                
                st.success("✅ အသံဖိုင် ဖန်တီးပြီးပါပြီ။")
                
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
