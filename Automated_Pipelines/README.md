
## Setup Instructions

### 1. Create a Conda Environment

First, create and activate a new conda environment named `PAT-agent`:

```bash
conda create -n PAT-agent python=3.9 -y
conda activate PAT-agent
```

### 2.  Install Requirements
Install the required Python packages using pip:
```bash
pip install -r requirements.txt
```

### 3. Dataset Format
Refer to the ../Datasets directory for dataset information.

### 4. Run the Pipeline
- Please replace `root_path = "path_to_your_root_directory"` with the root path of your folder 

- Run full pipeline
```bash
cd ./Fill_Pipleline
python pipeline.py
```

- Run pipeline without planning model
```bash
cd ./No_Pipleline
python pipeline.py
```

### 5. Customize the Pipeline

Here's how to customize different parts of the pipeline:

-   **Change the Planning LLM**: Modify the `get_LLM_answers` function.
    -   **Current o3-mini-high calling:**
```python
completion = client.chat.completions.create(
    model="o3-mini-2025-01-31",
    reasoning_effort="high",
    messages=[
        {
            "role": "user",
            "content": question
        }
    ]
)
answer = completion.choices[0].message.content
```
    -   **To replace with another model, e.g., DeepSeek-R1:**
```python
response = client_deepseek.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {
            "role": "user",
            "content": question
        }
    ]
)

answer = response.choices[0].message.content
```

-   **Change the Code Generation LLM**: Modify the `_get_claude_code_completion` function.
    -   **Current claude-3.7-sonnet calling:**
```python
response = client_claude.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=8192, # Max tokens as in codegen.html
    messages=[{"role": "user", "content": prompt_text}]
)
answer = response.content[0].text
```
    -   **To replace with another model, e.g., DeepSeek-R1:**
```python
response = client_deepseek.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {
            "role": "user",
            "content": prompt_text
        }
    ]
)
answer = response.choices[0].message.content
```

-   **Change the dataset**: Modify the first line of `__main__`:
    -   Replace `'./PAT.json'` with the path of the dataset file.
