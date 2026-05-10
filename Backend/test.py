import os
import torch
from dotenv import load_dotenv

load_dotenv()

print(os.getenv("OPENAI_API_KEY"))


print(torch.cuda.is_available())
