from openai import OpenAI

class OpenAiModelUser:
  def __init__(self, model: str = "gpt-3.5-turbo"):
    self.model = model
    self.client = OpenAI(api_key='')

    user_message = {}
    user_message["role"] = "user"
    user_message["content"] = ""
    self.user_message_array = [user_message]

  def Use(self, message: str) -> str:
    self.user_message_array[0]["content"] = message

    chat_completion = self.client.chat.completions.create(
      model=self.model,
      messages=self.user_message_array
    )

    return chat_completion.choices[0].message.content
