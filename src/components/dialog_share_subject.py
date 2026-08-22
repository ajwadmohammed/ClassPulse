# this one is to siplay the qr and info while clicking the button share qr.

import streamlit as st
import segno # for qr code generation
import io # to handle binary data


@st.dialog("Share Class Link")  # this makes them to be opened as in new box
def share_subject_dialog(subject_name, subject_code):
    app_domain = "classpulse-main.streamlit.app"  # webpage url, change it accordingly while hosting
    join_url = f"{app_domain}/?join-code={subject_code}"  # creates http://localhost:8501/?join-code=MATH101 for qr

    st.header("Scan to Join")

    qr = segno.make(join_url) # qr code generation

    out = io.BytesIO() # creating memory location to store the qr image

    qr.save(out, kind='png', scale=10, border=1) # saving the qr in out variable that is being created

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### Copy Link')
        st.code(join_url, language="text") # the use of havin st.code is that it will enable having the copy option by default.
        st.code(subject_code, language="text")
        st.info('Copy this link to share on Whatsapp or Email')

    with col2:
        st.markdown('### Scan to Join')
        st.image(out.getvalue(), caption='QRCODE for class joining')