import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import (CredentialsError,
                                                          ForgotError,
                                                          LoginError,
                                                          RegisterError,
                                                          ResetError,
                                                          UpdateError) 

import google.generativeai as gen_ai
import time
from streamlit_js_eval import streamlit_js_eval
from streamlit_modal import Modal



st.set_page_config(
    page_title="Chatbot!",
    page_icon=":brain:",  # Favicon emoji
    layout="centered",  # Page layout option
    )
def set_bg_hack_url():
    '''
    A function to unpack an image from url and set as bg.
    Returns
    -------
    The background.
    '''
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url("https://i.pinimg.com/originals/f6/94/ce/f694cee920f10241d9671fbc75e19a30.jpg");
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

set_bg_hack_url()
# Loading config file
with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)





if not st.session_state["authentication_status"]:
    st.title("🔐 Convobuddy")
    choice = st.selectbox('Login/Signup',['Login','Sign up'])
    if choice == 'Login':
        try:
            authenticator.login()
        except LoginError as e:
            st.error(e)

        if st.session_state["authentication_status"] is False:
            st.error('Username/password is incorrect')
        elif st.session_state["authentication_status"] is None:
            st.warning('Please enter your username and password')
    elif choice == 'Sign up':
            try:
                (email_of_registered_user,
                    username_of_registered_user,
                    name_of_registered_user) = authenticator.register_user(pre_authorization=False)
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)  
                if email_of_registered_user: 
                    modal = Modal(key="Demo Key",title="User registered successfully")
                    with modal.container():
                         st.markdown('Redirecting to Login Page')
                    time.sleep(3)
                    streamlit_js_eval(js_expressions="parent.window.location.reload()")
            except RegisterError as e:
                st.error(e)    

else:
    authenticator.logout()
    #st.header(f'Welcome *{st.session_state["name"]}*')

    GOOGLE_API_KEY = st.secrets["openai_api_key"]

    # Set up Google Gemini-Pro AI model
    gen_ai.configure(api_key=GOOGLE_API_KEY)
    model = gen_ai.GenerativeModel('gemini-pro')


    # Function to translate roles between Gemini-Pro and Streamlit terminology
    def translate_role_for_streamlit(user_role):
        if user_role == "model":
            return "assistant"
        else:
            return user_role


    # Initialize chat session in Streamlit if not already present
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(history=[])


    # Display the chatbot's title on the page
    st.title("🤖 Convobuddy")

    # Display the chat history
    for message in st.session_state.chat_session.history:
        with st.chat_message(translate_role_for_streamlit(message.role)):
            st.markdown(message.parts[0].text)

    # Input field for user's message
    user_prompt = st.chat_input("Ask Chatbot...")
    if user_prompt:
        # Add user's message to chat and display it
        st.chat_message("user").markdown(user_prompt)

        # Send user's message to Gemini-Pro and get the response
        gemini_response = st.session_state.chat_session.send_message(user_prompt)

        # Display Gemini-Pro's response
        with st.chat_message("assistant"):
            st.markdown(gemini_response.text)
    
