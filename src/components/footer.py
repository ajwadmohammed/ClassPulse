import streamlit as st

def footer_home():

    # logo_url = "https://i.ibb.co//logo.png" 
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: center; flex-direction: column; margin-bottom: 30px; margin-top: 30px;'>
            <p style="font-weight:bold; color: white">Created with ❤️ by Ajwad</p>
        </div>
                """, unsafe_allow_html=True)




def footer_dashboard():

    # logo_url = "https://i.ibb.co//logo.png" 
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: center; flex-direction: column; margin-bottom: 30px; margin-top: 30px;'>
            <p style="font-weight:bold; color: black">Created with ❤️ by Ajwad</p>
        </div>
                """, unsafe_allow_html=True)