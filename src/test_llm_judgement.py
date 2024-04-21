from llm_judgement import LlmJudgement

judgement = LlmJudgement()

test_input = ''' Hi Sarah,

I hope this email finds you well. I recently came across your company's Widget X and I'm quite impressed by its features. I'm interested in learning more about its availability and pricing.

Could you please provide me with some information regarding:

Availability of the Widget X
Pricing options and any available discounts
Delivery timeframes
Additionally, if there are any product demonstrations or trials available, I'd be keen to explore those as well.

Looking forward to your prompt response.

Best regards,
John Smith '''

#binary_response = judgement.BinaryJudgement("Is this an email from a customer or potential customer?", test_input)
#print(binary_response)

response = judgement.Task("Extract the key points from this email in only 2 sentences", test_input)
print(response)