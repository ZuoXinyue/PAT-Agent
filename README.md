# PAT Agent
This project focuses on natural language autoformalization and formal code repair. We provide both a fully automated pipeline that accepts natural language inputs, as well as an interactive interface that allows controllable step-by-step model developement.

## Folder Structure

Here's an overview of the project's folder structure:

```
PAT-Agent-Submission/
├── Appendix/                 # Additional results not provided in the paper due to space constraint
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
├── Datasets/ # Paper experiments datasets
│   ├── A4F.json
│   ├── PAT.json
│   └── UCS.json
├── Interface/                # PAT-Agent interface for controllable and interetaive development
│   ├── history/
│   ├── run_time_record/
│   ├── templates/
│   ├── server.py
│   └── README.md  
└── PAT.Console/              # PAT Model Checker
```

## Video
The following demo video illustrates how to use the PAT-Agent interface to interactively develop a formal model from general natural language descriptions.