import streamlit as st

st.title("🎬 AI Movie Recap Automation")
st.write("Douyin သို့မဟုတ် RedNote Link ထည့်ပြီး Script နှင့် အသံဖိုင်ကို အလိုအလျောက် ရယူပါ။")

video_url = st.text_input("ဒီနေရာမှာ Video Link ကို ထည့်ပါ:")

if st.button("Generate Script & Voice"):
    st.info("System is ready. လိုအပ်သော AI စနစ်များ မကြာမီ ချိတ်ဆက်ပါမည်။")
