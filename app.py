
import streamlit as st
import time
import random
import smtplib
import ssl
import html
import re
from email.message import EmailMessage
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT, build_learning_prompt


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 42px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 5px;
        }

        .subtitle {
            text-align: center;
            font-size: 17px;
            color: #888888;
            margin-bottom: 25px;
        }

        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            min-height: 45px;
        }

        .feature-card {
            padding: 18px;
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 12px;
            text-align: center;
            min-height: 120px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 3. GEMINI CONFIGURATION
# =========================================================

MODEL_NAME = "gemini-3.8-flash"

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]

except Exception:
    st.error(
        "Gemini API key is missing. Please configure "
        "GEMINI_API_KEY in .streamlit/secrets.toml."
    )
    st.stop()


client = genai.Client(api_key=API_KEY)


# =========================================================
# 4. SESSION STATE
# =========================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "last_explanation" not in st.session_state:
    st.session_state.last_explanation = None


# =========================================================
# 5. GEMINI IMAGE ANALYSIS WITH RETRIES
# =========================================================

def analyze_image_with_retry(
    image_bytes,
    mime_type,
    prompt,
    max_attempts=3
):
    """
    Send an image and prompt to Gemini.

    Retries temporary service availability and rate-limit
    errors with exponential backoff.
    """

    for attempt in range(max_attempts):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type
                    ),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.3
                )
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as e:

            error_message = str(e).upper()

            temporary_error = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
                or "500" in error_message
                or "INTERNAL" in error_message
            )

            if temporary_error and attempt < max_attempts - 1:

                wait_time = (
                    (2 ** attempt)
                    + random.uniform(0, 1)
                )

                time.sleep(wait_time)

            else:
                raise


def markdown_to_email_html(content):
    """
    Convert the Gemini Markdown response into simple HTML
    suitable for an email.
    """

    # Protect special HTML characters
    content = html.escape(content)

    # Headings
    content = re.sub(
        r'^### (.+)$',
        r'<h3 style="color:#2563eb; margin-top:24px;">\1</h3>',
        content,
        flags=re.MULTILINE
    )

    content = re.sub(
        r'^## (.+)$',
        r'<h2 style="color:#1e3a8a; margin-top:25px;">\1</h2>',
        content,
        flags=re.MULTILINE
    )

    content = re.sub(
        r'^# (.+)$',
        r'<h1 style="color:#1e3a8a;">\1</h1>',
        content,
        flags=re.MULTILINE
    )

    # Bold
    content = re.sub(
        r'\*\*(.+?)\*\*',
        r'<strong>\1</strong>',
        content
    )

    # Horizontal line
    content = re.sub(
        r'^---$',
        '<hr style="border:none; border-top:1px solid #e5e7eb;">',
        content,
        flags=re.MULTILINE
    )

    # Bullet points
    content = re.sub(
        r'^\* (.+)$',
        r'• \1',
        content,
        flags=re.MULTILINE
    )

    # Preserve line breaks
    content = content.replace("\n", "<br>")

    return content


def send_explanation_email(recipient, subject, content):

    sender_email = st.secrets["SMTP_EMAIL"]
    sender_password = st.secrets["SMTP_PASSWORD"]

    message = EmailMessage()

    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject

    # Plain-text fallback
    message.set_content(content)

    formatted_content = markdown_to_email_html(content)

    html_email = f"""
    <!DOCTYPE html>
    <html>
    <body style="
        margin:0;
        padding:0;
        background-color:#f5f7fb;
        font-family:Arial, Helvetica, sans-serif;
    ">

        <div style="
            max-width:700px;
            margin:30px auto;
            background:white;
            border-radius:12px;
            overflow:hidden;
            border:1px solid #e5e7eb;
        ">

            <!-- Header -->

            <div style="
                padding:25px;
                background:#1e3a8a;
                color:white;
                text-align:center;
            ">

                <h1 style="
                    margin:0;
                    font-size:28px;
                ">
                    📚 Snap &amp; Study
                </h1>

                <p style="
                    margin:8px 0 0 0;
                    font-size:14px;
                ">
                    AI-Powered Learning Assistant
                </p>

            </div>

            <!-- Main content -->

            <div style="
                padding:30px;
                color:#1f2937;
                font-size:16px;
                line-height:1.7;
            ">

                <div style="
                    background:#eff6ff;
                    padding:15px;
                    border-radius:8px;
                    margin-bottom:25px;
                ">
                    🎓 <strong>Your Study Explanation</strong>
                </div>

                {formatted_content}

            </div>

            <!-- Footer -->

            <div style="
                background:#f8fafc;
                padding:20px;
                text-align:center;
                color:#64748b;
                font-size:13px;
                border-top:1px solid #e5e7eb;
            ">

                <strong>Snap &amp; Study</strong>

                <br><br>

                Learn smarter with AI.

                <br>

                This explanation was generated using
                Snap &amp; Study.

            </div>

        </div>

    </body>
    </html>
    """

    # HTML version
    message.add_alternative(
        html_email,
        subtype="html"
    )

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        context=context
    ) as server:

        server.login(
            sender_email,
            sender_password
        )

        server.send_message(message)
# =========================================================
# 6. HEADER
# =========================================================

st.markdown(
    '<div class="main-title">📚 Snap & Study</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Your AI-powered learning companion'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# 7. SIDEBAR
# =========================================================

with st.sidebar:

    st.title("📚 Snap & Study")

    st.write(
        "Understand your study material using AI."
    )

    st.divider()

    st.subheader("✨ Features")

    st.write("📷 Upload study images")
    st.write("🤖 AI-powered explanations")
    st.write("📝 Step-by-step solutions")
    st.write("💡 Simple concept explanations")
    st.write("📖 Key-point summaries")

    st.divider()

    st.subheader("⚙️ About")

    st.caption(
        "Snap & Study is an AI-powered learning assistant "
        "built using Python, Streamlit, and Gemini."
    )

    if st.button("🗑️ Clear History", use_container_width=True):

        st.session_state.history = []
        st.session_state.last_explanation = None

        st.rerun()


# =========================================================
# 8. INTRODUCTION
# =========================================================

st.markdown(
    """
    Upload a photo of your textbook question, handwritten notes,
    programming problem, or academic diagram.

    Gemini will analyze the image and explain it in
    simple, student-friendly language.
    """
)

st.write("")


# =========================================================
# 9. FEATURE CARDS
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="feature-card">
            <h3>📷</h3>
            <b>Snap</b>
            <p>Upload your study material</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="feature-card">
            <h3>🤖</h3>
            <b>Understand</b>
            <p>Get AI-powered explanations</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class="feature-card">
            <h3>🎓</h3>
            <b>Learn</b>
            <p>Understand concepts step by step</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()


# =========================================================
# 10. IMAGE UPLOAD
# =========================================================

st.subheader("📷 Upload Your Study Material")

uploaded_file = st.file_uploader(
    "Choose an image",
    type=["jpg", "jpeg", "png", "webp"],
    help="Upload a clear image of notes, questions, or diagrams."
)


if uploaded_file is not None:

    st.success("Image uploaded successfully!")

    st.image(
        uploaded_file,
        caption="Your uploaded study material",
        use_container_width=True
    )


# =========================================================
# 11. STUDENT QUESTION
# =========================================================

st.subheader("💬 Ask a Question")

student_question = st.text_area(
    "What would you like to understand?",
    placeholder=(
        "Example: Explain this concept in simple words "
        "with a real-life example."
    ),
    height=100
)


# =========================================================
# 12. ANALYZE BUTTON
# =========================================================

analyze_button = st.button(
    "🔍 Analyze & Explain",
    type="primary",
    use_container_width=True
)


if analyze_button:

    if uploaded_file is None:

        st.warning(
            "Please upload a study image before analyzing."
        )

    else:

        image_bytes = uploaded_file.getvalue()

        mime_type = uploaded_file.type

        user_prompt = build_learning_prompt(
            student_question
        )

        try:

            with st.spinner(
                "🤖 Gemini is analyzing your image. Please wait..."
            ):

                explanation = analyze_image_with_retry(
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    prompt=user_prompt,
                    max_attempts=3
                )

            st.session_state.last_explanation = explanation

            st.session_state.history.append(
                {
                    "question": student_question or "Explain this image",
                    "explanation": explanation,
                    "filename": uploaded_file.name
                }
            )

            st.success("Your study explanation is ready!")

        except Exception as e:

            error_message = str(e)

            upper_error = error_message.upper()

            if "503" in upper_error or "UNAVAILABLE" in upper_error:

                st.warning(
                    "Gemini is currently experiencing high demand. "
                    "Please wait a little and try again."
                )

            elif (
                "429" in upper_error
                or "RESOURCE_EXHAUSTED" in upper_error
            ):

                st.warning(
                    "The Gemini API request limit may have been reached. "
                    "Please check your API quota and try again later."
                )

            elif "404" in upper_error or "NOT_FOUND" in upper_error:

                st.error(
                    "The configured Gemini model is unavailable "
                    "for this API request. Check the model name "
                    "and available models for your API key."
                )

            elif (
                "401" in upper_error
                or "403" in upper_error
                or "PERMISSION_DENIED" in upper_error
            ):

                st.error(
                    "Gemini API authentication or permission failed. "
                    "Check your API key and API access."
                )

            else:

                st.error(
                    "Something went wrong while analyzing your image."
                )

            with st.expander("🔧 Technical Error Details"):
                st.code(error_message)


# =========================================================
# 13. DISPLAY LATEST EXPLANATION
# =========================================================

if st.session_state.last_explanation:

    st.divider()

    st.subheader("📖 AI Explanation")

    st.markdown(
        st.session_state.last_explanation
    )

    st.download_button(
        label="⬇️ Download Explanation",
        data=st.session_state.last_explanation,
        file_name="snap_and_study_explanation.md",
        mime="text/markdown",
        use_container_width=True
    )

    st.divider()

    st.subheader("📧 Share Your Explanation")

    recipient_email = st.text_input(
        "Recipient Email Address",
        placeholder="student@example.com"
    )

    email_subject = st.text_input(
        "Email Subject",
        value="My Snap & Study Learning Notes"
    )

    if st.button(
        "📨 Send Explanation via Email",
        use_container_width=True
    ):

        if not recipient_email or "@" not in recipient_email:
            st.warning("Please enter a valid email address.")

        else:

            try:

                send_explanation_email(
                    recipient=recipient_email,
                    subject=email_subject,
                    content=st.session_state.last_explanation
                )

                st.success("Explanation sent successfully!")

            except Exception as e:

                st.error("Unable to send the email.")

                with st.expander("Technical Error"):
                    st.code(str(e))

# =========================================================
# 14. LEARNING HISTORY
# =========================================================

if st.session_state.history:

    st.divider()

    st.subheader("🕘 Recent Learning History")

    for index, item in enumerate(
        reversed(st.session_state.history),
        start=1
    ):

        with st.expander(
            f"📄 {item['filename']} — Session {index}"
        ):

            st.write("**Question:**")

            st.write(item["question"])

            st.write("**Explanation:**")

            st.markdown(item["explanation"])


# =========================================================
# 15. FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:gray;">
        <p>📚 Snap & Study</p>
        <p>AI-Powered Learning Assistant</p>
        <p>Built with Python, Streamlit & Gemini</p>
    </div>
    """,
    unsafe_allow_html=True
)