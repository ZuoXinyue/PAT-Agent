
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
### 3. Dataset Processing
Refer to the ../Datasets directory for data processing instructions.

### 4. Run the Python Server
- run full pipeline
```bash
cd ./Fill_Pipleline
python pipeline.py
```
- run pipeline without planning model
```bash
cd ./No_Pipleline
python pipeline.py
```