import gradio as gr
from ai.AI import your_prediction_function  # update based on actual function name

def launch_gradio():
    interface = gr.Interface(
        fn=your_prediction_function,
        inputs=gr.Image(type="filepath"),
        outputs="image",
        live=True
    )
    interface.launch(share=False)
