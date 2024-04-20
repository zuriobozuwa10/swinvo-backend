from openai_model_user import OpenAiModelUser

class LlmJudgement:
  def __init__(self):
    self.model = OpenAiModelUser()

  def BinaryJudgement(self, question: str, input_text: str) -> bool:
    prompt = f"From now on, I am going to give you an input text, and i want you to to answer this question about the input text, with either Yes or No. Here is the question: {question}. And here is the input text: {input_text}"
    #print(prompt)
    string_response = self.model.Use(prompt)
    #print(string_response)
    if "Yes" in string_response or "yes" in string_response:
      return True
    else:
      return False

