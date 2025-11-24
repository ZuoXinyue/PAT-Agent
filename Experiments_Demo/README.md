### Experiments_Demo

This folder provides a complete, step-by-step demonstration of how PAT-Agent generates formally verified models from natural-language system descriptions and requirements.

We use the two most complex systems in our dataset — the Car system and the Tesla system — to showcase the pipeline’s behavior in realistic, structurally rich scenarios.

The materials here are direct outputs from running the actual pipeline, covering the full workflow:
- extracting constants and variables
- identifying actions and transitions
- generating natural-language modeling plans
- synthesizing CSP# models
- verifying the models
- repairing the models using counterexample traces


Below is an overview of the contents of each subfolder.

#### ```run_time_record/```
This folder contains timing information for every generation stage in the pipeline, recorded as JSON files.

#### ```history/```
This folder stores all intermediate results produced during the modeling, verification, and repair process.

Key files include:
- const-history.json: constants extracted from the natural-language description.
- action-history.json: processed actions, including guarded conditions and state transitions.
- nl-instruction-claude.json: the final modeling plan synthesized by the Planning LLM before code generation.
- claude-code.json: the CSP# model generated during model-synthesis stage or repair stage.
- mismatch_traces.json: verification counterexamples used to guide model repair.

Together, these files provide a transparent view of every decision and transformation made during the pipeline.

#### ```generated_code/```
This folder contains all CSP# models produced during model generation and repair.
For each system (e.g., tesla), you will find:

- initially generated CSP# models (e.g., 0.csp, 1.csp, …)
- refined models for each repair round (e.g., refine_round_1/, refine_round_2/)
- any mismatch traces that triggered further repair
- if the initial generation or subsequent repairs succeed, the verifiedCode.csp file containing the verified model

These files demonstrate how PAT-Agent progressively improves the model until all user-specified requirements are formally verified.