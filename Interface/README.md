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
### 3. Run the Python Server
Start the Python server by running:
```bash
python server.py
```
### 4. Access the Application
Once the server is running, open your web browser and go to:
```bash
http://127.0.0.1:5000
```

### 5. Demo
The following demo video illustrates how to use the PAT-Agent interface to interactively develop a formal model from general natural language descriptions.

<video width="640" height="360" controls>
  <source src="../demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

If you can’t view the embedded player, download the video directly:
[Download the demo video](../demo.mp4)