import gradio as gr
import random
import time
from src.Core.Core import Core
from src.UI.ui_logic import *
bot = Core()

def chat_respond(message, chat_history):
    bot_message = bot.chat(message)
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": bot_message})
    return "", chat_history

with gr.Blocks() as ui:
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Accordion("Menu"):
                gr.Button("Toggle Device 1").click(fn=toggle_ui_device1)
                gr.Button("Toggle Device 2").click(fn=toggle_ui_device2)

        with gr.Column(scale=2):
            with gr.Group():
                time_range = gr.Radio(
                    choices=["Last 1 Hour", "Last 6 Hours", "Last 12 Hours"],
                    label="Select Time Range"
                )
                plot = gr.Plot()
                time_range.change(fn=update_plot, inputs=time_range, outputs=plot)

        with gr.Column(scale=4):
            with gr.Group():
                chatbot = gr.Chatbot(type="messages")
                msg = gr.Textbox(label="Input")
            clear = gr.ClearButton([msg, chatbot])
            msg.submit(chat_respond, [msg, chatbot], [msg, chatbot])