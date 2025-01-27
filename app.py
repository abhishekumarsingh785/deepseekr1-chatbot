import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
import re

st.set_page_config(layout="wide")
st.title("🤖Chatbot powered by DeepSeek R1")

# Initialize the model
model_name = "deepseek-r1:8b"
model = ChatOllama(model=model_name, base_url="http://localhost:11434")

# System message initialization with escaped curly braces
system_message = SystemMessagePromptTemplate.from_template(
    "You are a helpful AI assistant who helps users with any question or task they have."
)

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_message.prompt}]

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(message["content"])

# Function to chunk text logically
def chunk_response(response):
    # Preserve code blocks (```) and split by paragraphs (\n\n)
    pattern = r"(```.*?```)|([^```]+)"
    chunks = []
    for match in re.finditer(pattern, response, re.DOTALL):
        if match.group(1):  # Code block
            chunks.append(match.group(1))
        elif match.group(2):  # Non-code block, split by paragraphs
            chunks.extend(filter(None, match.group(2).split("\n\n")))
    return chunks

# Input box for user input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to the session state
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display the user message in the chat
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response from the model
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Prepare chat history for the model
            chat_history = [
                HumanMessagePromptTemplate.from_template(m["content"])
                if m["role"] == "user"
                else AIMessagePromptTemplate.from_template(m["content"])
                for m in st.session_state.messages
                if m["role"] != "system"
            ]

            # Properly handle the input templates and escape curly braces
            chat_template = ChatPromptTemplate.from_messages(chat_history)
            chain = chat_template | model | StrOutputParser()

            # Generate the response
            response = chain.invoke({})

            # Chunk the response logically
            response_chunks = chunk_response(response)

            # Add each chunk to the assistant's response in the chat
            for chunk in response_chunks:
                st.markdown(chunk)

            # Add the full response to the session state for continuity
            st.session_state.messages.append({"role": "assistant", "content": response})
