import streamlit as st
from pdf2image import convert_from_path
import base64
from openai import OpenAI 

SYSTEM_PROMPT_OKU = "You are looking at Malaysian Disabled Person (OKU) Card or medical health confirmation letter. You are going to respond in Markdown without any explanation."
SYSTEM_PROMPT_PARENT = "You are looking at the document of a student's {}. You are going to respond in Markdown without any explanation."
SYSTEM_PROMPT_FORM = "You are looking at an income verification form. Return all info in Markdown format."

USER_PROMPT_OKU = "Is the image a OKU Card or medical report letter? What is the person name and NRIC or IC number? If it is a OKU card, what is the category of disabilities, and what is the registration number? If it is a medical confirmation letter, what is the name of medical centre, date of the letter, summary of the medical letter, and the date the letter is produced. Return all the info in point form."
USER_PROMPT_PARENT = "Is the image a payslip, confirmation letter, deceased letter, or disabled (OKU) card? If it is a payslip, what is the employee name, company name, and the gross pay? If it is a confirmation letter, who signed the letter, what is the letter about, and can you extract the {} name and the declared income? If it is a deceased letter, what is the deceased name, and date of death? If it is a OKU card, what is the cardholder name, type of OKU, and serial number?"
USER_PROMPT_FORM = "Extract the student's name and matric number. In Section B and C, extract the name, IC or Passport number, status, mobile phone number, occupation, employer, nett income, and number of dependent of the father or guardian information. Include the name, officer title, and date of verification."
MODEL = "gpt-4o"
client = OpenAI(api_key=st.secrets['OPENAI_API'])

st.set_page_config(layout='wide')

def get_openai_response(base64_image,system,user):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "text", "text": user},
                {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{base64_image}"}
            }
            ]}
        ],
        temperature=0.0,
    )
    return response

def convert_pdf_to_png(uploaded_file):
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    images = convert_from_path("temp.pdf")
    image_paths = []
    for i, image in enumerate(images):
        image_path = f"temp_image_{i}.png"
        image.save(image_path, "PNG")
        image_paths.append(image_path)
    return image_paths

def convert_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def main():
    st.title("B40 Verification")

    button_selection = st.radio("Choose the documents type", ["Form", "OKU", "Mother", "Father", "Guardian"], horizontal=True)
    system_prompt = st.empty()
    user_prompt = st.empty()

    if button_selection == "OKU":
        sp = system_prompt.text_area("System Prompt", value=SYSTEM_PROMPT_OKU)
        up = user_prompt.text_area("User Prompt", value=USER_PROMPT_OKU)
    elif button_selection == "Form":
        sp = system_prompt.text_area("System Prompt", value=SYSTEM_PROMPT_FORM)
        up = user_prompt.text_area("User Prompt", value=USER_PROMPT_FORM)
    else:
        sp = system_prompt.text_area("System Prompt", value=SYSTEM_PROMPT_PARENT.format(button_selection))
        up = user_prompt.text_area("User Prompt", value=USER_PROMPT_PARENT.format(button_selection))

    # File upload
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    cols = st.columns(2)

    if uploaded_file is not None:
        with cols[0]:
            with st.spinner("Converting PDF to image"):
                image_paths = convert_pdf_to_png(uploaded_file)
                st.markdown("**The first page of the PDF**")
                st.image(image_paths[0])
        
        with cols[1]:
            with st.spinner("Getting result from OpenAI"):
                base64_image = convert_image_to_base64(image_paths[0])
                response = get_openai_response(base64_image, sp,up)
                st.markdown(response.choices[0].message.content)
        
        if st.button("New query"):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
