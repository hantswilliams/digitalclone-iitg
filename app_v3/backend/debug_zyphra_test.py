from gradio_client import Client, handle_file

client = Client("Steveeeeeeen/Zonos")

result = client.predict(
		model_choice="Zyphra/Zonos-v0.1-transformer",
		text="Hello my name is Bob.",
		language="en-us",
		speaker_audio=handle_file('app_v3/backend/test_files/voice.wav'),
		prefix_audio=handle_file('app_v3/backend/test_files/voice.wav'),
		unconditional_keys=["emotion"],
		api_name="/generate_audio"
)
print(result)