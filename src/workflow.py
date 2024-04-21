from llm_judgement import LlmJudgement
from gmail_caller import GmailCaller

class Workflow:
  def __init__(self, workflow_yaml):
    self.gmail_caller = GmailCaller()
    self.llm_judgement = LlmJudgement()
    pass

  def RunOnce(self):
    pass