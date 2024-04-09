from openai import OpenAI

class OpenAiModelUser:
  def __init__(self, model: str = "gpt-3.5-turbo"):
    self.model = model
    self.client = OpenAI(api_key='')
    self.convo_history = ""

    user_message = {}
    user_message["role"] = "user"
    user_message["content"] = ""
    self.user_message_array = [user_message]

  def Use(self, input_message: str) -> str:
    input_message_with_helpers = "\nHuman: " input_message + "\nAI: "

    self.user_message_array[0]["content"] = self.convo_history + input_message_with_helpers

    self.convo_history = self.convo_history + input_message_with_helpers

    chat_completion = self.client.chat.completions.create(
      model=self.model,
      messages=self.user_message_array
    )

    ai_response = chat_completion.choices[0].message.content

    self.convo_history = self.convo_history + ai_response

    return ai_response

  def GetConvoHistory(self):
    return self.convo_history
