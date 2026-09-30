import streamlit as st
import whisper
import google.generativeai as genai
import edge_tts
import asyncio
import os
import tempfile

# --- 1. Streamlit UI Setup ---
st.title("🎬 AI Movie Recap Automation")
st.write("ဒေါင်းလုဒ်ဆွဲထားသော ဗီဒီယို သို့မဟုတ် အသံဖိုင်ကို တိုက်ရိုက်တင်ပြီး Script နှင့် အသံဖိုင်ကို ရယူပါ။")

# --- 2. API Key Configuration ---
st.sidebar.header("⚙️ Settings")
api_key = st.sidebar.text_input("Gemini API Key ကို ထည့်ပါ:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.sidebar.warning("ကျေးဇူးပြု၍ သင်၏ Gemini API Key ကို ထည့်ပါ။")

# --- 3. Main Interface (File Upload) ---
uploaded_file = st.file_uploader("ဗီဒီယို သို့မဟုတ် အသံဖိုင် ရွေးချယ်ပါ (Upload):", type=['mp4', 'mov', 'avi', 'mp3', 'wav', 'm4a'])

async def generate_audio(text, output_file):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural") 
    await communicate.save(output_file)

if st.button("Generate Script & Voice"):
    if not uploaded_file:
        st.error("ကျေးဇူးပြု၍ ဗီဒီယို (သို့) အသံဖိုင်တစ်ခုခုကို အရင် Upload တင်ပါ။")
    elif not api_key:
        st.error("ကျေးဇူးပြု၍ ဘယ်ဘက်အခြမ်း (Sidebar) တွင် Gemini API Key ကို ထည့်ပါ။")
    else:
        with st.spinner("လုပ်ငန်းစဉ် စတင်နေပါပြီ... ခဏစောင့်ပါ... ⏳"):
            try:
                # ဖိုင်ကို ယာယီသိမ်းဆည်းခြင်း
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # --- Step 1: Transcribe Audio using Whisper ---
                st.info("📝 ဗီဒီယိုမှ မူရင်းစာသားကို ရယူနေပါသည် (Whisper AI)...")
                whisper_model = whisper.load_model("base") 
                result = whisper_model.transcribe(file_path)
                original_text = result["text"]
                
                st.success("✅ မူရင်းစာသား ရယူပြီးပါပြီ။")
                with st.expander("မူရင်းစာသား (Original Transcript) ကို ကြည့်ရန် နှိပ်ပါ"):
                    st.write(original_text)

                # --- Step 2: Generate Recap Script using Gemini ---
                st.info("✨ Gemini AI ဖြင့် မြန်မာ ဇာတ်ညွှန်း ပြန်လည်ရေးသားနေပါသည်...")
                prompt = f"""
                အောက်ပါစာသားသည် ရုပ်ရှင် သို့မဟုတ် ဗီဒီယိုတစ်ခုမှ ထုတ်ယူထားသော မူရင်းစာသား ဖြစ်သည်။ 
                ယင်းစာသားကို အခြေခံ၍ ဆွဲဆောင်မှုရှိသော၊ စိတ်ဝင်စားဖွယ်ကောင်းသော 'Movie Recap' ဇာတ်ညွှန်းတစ်ခုကို 'မြန်မာဘာသာ' ဖြင့် ပြန်လည်ရေးသားပေးပါ။
                
                မူရင်းစာသား:
                {original_text}
                """
                response = model.generate_content(prompt)
                myanmar_script = response.text
                
                st.success("✅ မြန်မာဇာတ်ညွှန်း ရေးသားပြီးပါပြီ။")
                st.subheader("📜 သင့်အတွက် AI ရေးပေးသော မြန်မာဇာတ်ညွှန်း")
                st.write(myanmar_script)

                # --- Step 3: Text-to-Speech using Edge-TTS ---
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
