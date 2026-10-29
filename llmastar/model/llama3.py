# Local Hugging Face pipeline for Llama-3-8B-Instruct (bf16). torch/transformers are imported only when the class
# is instantiated. Serving the model with vLLM and using ChatGPT(base_url=...) is the recommended path.
class Llama3:
  def __init__(self, model_id="meta-llama/Meta-Llama-3-8B-Instruct", device="cuda", max_new_tokens=8000):
    import torch
    import transformers

    self.max_new_tokens = max_new_tokens
    self.pipeline = transformers.pipeline(
        "text-generation",
        model=model_id,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device=device,
    )
    self.terminators = [
        self.pipeline.tokenizer.eos_token_id,
        self.pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

  def _generate(self, inputs):
    return self.pipeline(
      inputs,
      max_new_tokens=self.max_new_tokens,
      eos_token_id=self.terminators,
      do_sample=False,
      temperature=None,
      top_p=None,
      pad_token_id=self.pipeline.tokenizer.eos_token_id
    )

  def ask(self, prompt):
    outputs = self._generate(prompt)
    return outputs[0]["generated_text"][len(prompt):]

  def chat(self, messages):
    outputs = self._generate(messages)
    return outputs[0]["generated_text"][-1]["content"]
