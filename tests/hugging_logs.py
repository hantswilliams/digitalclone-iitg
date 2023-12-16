# huggingface_hub

import os
from huggingface_hub import HfApi, HfFolder, Repository
from dotenv import load_dotenv

load_dotenv()

# 0. Set up the environment variables
HUGG_TOKEN = os.getenv("HUGGING")

# 1. Log in to the Hugging Face Hub and provide your credentials
api = HfApi(token=HUGG_TOKEN)
print(api.whoami())

# 2. Get list of spaces
spaces = api.list_spaces(author="hants")
for space in spaces:
    print(space)

# 3. Get space runtime 
api.get_space_runtime("hants/SadTalker")
api.space_info("hants/SadTalker")
api.pause_space(
    "hants/SadTalker",
    )

# 4. Example of pausing a space
HfApi(token=HUGG_TOKEN).pause_space("hants/SadTalker")


# Test login
user = api.whoami()

# 2. Create a repo
