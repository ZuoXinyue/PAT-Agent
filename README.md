# PAT-Agent
**Accepted by ASE 2025 (International Conference on Automated Software Engineering)**
[![Paper](https://img.shields.io/badge/Paper-IEEE_Xplore-00629B?logo=ieee)](https://ieeexplore.ieee.org/document/11334568)

This project focuses on natural language autoformalization and formal code repair. We provide both a fully automated pipeline that accepts natural language inputs, as well as an interactive interface that allows controllable step-by-step model developement.

## Folder Structure

Here's an overview of the project's folder structure:

```
PAT-Agent-Submission/
├── Appendix/                 # Additional results not provided in the PAT-Agent paper due to space constraint
│   ├── Interface_Screenshots/
│   ├── Prompt_Example/
│   ├── RQ1/
│   ├── RQ2/
│   ├── RQ3/
│   └── User_Study/
├── Automated_Pipelines/      # PAT-Agent pipeline for fully automated development
│   ├── Full_Pipeline/
│   ├── No_Planning/
│   └── README.md 
├── Datasets/                 # Paper experiments datasets
│   ├── A4F.json
│   ├── PAT.json
│   └── UCS.json
├── Experiments_Demo/         # End-to-end pipeline demonstration, including planning, synthesis, verification, and repair
│   ├── generated_code/
│   ├── history/              # Detailed breakdown of the outputs from each pipeline step
│   └── run_time_record/
├── Interface/                # PAT-Agent interface for controllable and interetaive development
│   ├── history/
│   ├── run_time_record/
│   ├── templates/
│   ├── server.py
│   └── README.md  
└── PAT.Console/              # PAT Model Checker
```

## Replicating the Experiments

To reproduce the experiments reported in the PAT-Agent paper:
- Step 1: Clone the Repository.
- Step 2: Move the dataset to run to its expected location.
    - Example: place ```Datasets/PAT.json``` into ```Automated_Pipelines/Full_Pipeline/PAT.json```.
- Step 3: Set the project root path.
    - Update the ```root_path``` variable (e.g., in ```Automated_Pipelines/Full_Pipeline/pipeline.py```) so it points to the absolute path of your cloned repository.
- Step 4: Set up the environment.
    - Create the conda environment as instructed in ```Automated_Pipelines/README.md```.
- Step 5: Run the experiments.
    - Execute the pipeline at ```Full_Pipeline/pipeline.py```.

## Pipeline Demonstration Materials
To help users understand the full workflow, including planning, synthesis, verification, and repair, we provide detailed intermediate results in the ```Experiments_Demo``` folder.

These demonstration materials are taken directly from real executions of our pipeline on the two most complex systems in our dataset. They show how constants and variables are extracted, how plans are constructed, how models are synthesized and verified, and how the final repairs are produced.

For more details, please refer to ```Experiments_Demo/README.md```.

## Video [Interface Demo]
The demo video illustrates how to use the PAT-Agent interface to interactively develop a formal model from general natural language descriptions.

**Click the image below to watch on YouTube:**

[![Watch the demo on YouTube](https://img.youtube.com/vi/1dAPfLEG3wU/0.jpg)](https://youtu.be/1dAPfLEG3wU)

## Citation

For academic references, please cite our ASE 2025 paper:

```bibtex
@inproceedings{zuo2025pat,
  title={PAT-Agent: Autoformalization for Model Checking},
  author={Zuo, Xinyue and Zhang, Yifan and Wang, Hongshu and Cai, Yufan and Hou, Zhe and Sun, Jing and Dong, Jin Song},
  booktitle={2025 40th IEEE/ACM International Conference on Automated Software Engineering (ASE)},
  pages={2122--2133},
  year={2025},
  organization={IEEE}
}
```

This repository is an **experimental research prototype** developed for academic purposes only.
