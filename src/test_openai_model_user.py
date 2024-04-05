from openai_model_user import OpenAiModelUser

model = OpenAiModelUser()

response_content = model.Use("List colours of the rainbow")

print(response_content)