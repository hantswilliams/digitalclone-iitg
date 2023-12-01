import gradio as gr

block = gr.Blocks()

def run():
  with block:
    gr.Markdown(
    """
    <style> body { text-align: right} </style>
    map: 📄 [arxiv](https://arxiv.org/abs/2112.02749) &nbsp; ⇨ 👩‍💻 [github](https://github.com/FuxiVirtualHuman/AAAI22-one-shot-talking-face) &nbsp; ⇨ 🦒 [colab](https://github.com/camenduru/one-shot-talking-face-colab) &nbsp; ⇨ 🤗 [huggingface](https://huggingface.co/spaces/camenduru/one-shot-talking-face) &nbsp; | &nbsp; tools: 🌀 [duplicate this space](https://huggingface.co/spaces/camenduru/sandbox?duplicate=true) &nbsp; | 🐢 [tortoise tts](https://huggingface.co/spaces/mdnestor/tortoise) &nbsp; | 📺 [video upscaler](https://huggingface.co/spaces/kadirnar/Anime4k) &nbsp; | 🎨 [text-to-image](https://huggingface.co/models?pipeline_tag=text-to-image&sort=downloads) &nbsp; | 🐣 [twitter](https://twitter.com/camenduru) &nbsp; | ☕ [buy-a-coffee](https://patreon.com/camenduru) &nbsp;
    """)
    with gr.Group():
        with gr.Row():
          image_in = gr.Image(show_label=False, type="filepath")
          audio_in = gr.Audio(show_label=False, type='filepath')
          video_out = gr.Video(show_label=False)
        with gr.Row():
          btn = gr.Button("Generate")          

    btn.click(inputs=[image_in, audio_in], outputs=[video_out])
    block.queue()
    block.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    run()