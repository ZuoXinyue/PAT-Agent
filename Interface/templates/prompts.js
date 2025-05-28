/**
 * Prompts library - Collection of prompts used across the PAT Agent Interface
 * 
 * This file contains functions that return various prompts used by the application.
 * Each function is focused on a specific use case and can accept parameters to customize
 * the prompt as needed.
 */

function chatbotPrompt(userInput, classicalSummary) {
  return `User description: "${userInput}".
Here is the list of existing algorithms in our database:
${classicalSummary}

Here are the rules to follow in your response:
1. Compare the user's description with the description of existing algorithms, identify the most relevant existing algorithm, if any.

2. If the description of the most relevant existing algorithm says "loose match", and the user's request is very likely describing a classical algorithm (e.g., dining philosopher, peterson, etc.) that matches the most relevant existing algorithm, then organize the analyzed results into the following **JSON format**:
{
"type": "customization-algorithm",
"algorithm": id of the algorithm that appears in the description of existing algorithms (before :),
"description": description of the algorithm
}
3. If the description of the most relevant existing algorithm says "exact match", then only if the user's request references the same major **components** as a known algorithm (**no significant extras or missing pieces**). It is ok if the **requirements** described in the user's request doesn't exactly match with the requirements described in the most relevant existing algorithm, as long as there are no significantly more requirements, organize the analyzed results into the following **JSON format**:
{
"type": "customization-system",
"algorithm": id of the algorithm that appears in the description of existing algorithms (before :),
"description": description of the algorithm
}
4. If the user's request has any additional and/or missing components, or has significantly more requirements when the description of the most relevant existing algorithm says "exact match", or if no existing algorithms that are **sufficiently similar** to the user's request, organize the analyzed results into the following **JSON format**:
{
"type": "new system",
"algorithm": "",
"description": ""
}
5. If the user's request is overly general, too vague, or does not sound like a description of a reasonable algorithm or system, organize the analyzed results into the following **JSON format**:
{
"type": "clarify",
"algorithm": "",
"description": ""
}`;
} 


function genConstPrompt(structuredData, processesDescription){
  return `As an expert in information extraction and analysis in computer science domain, can you extract all the constants and variables involved in each of the ${structuredData.subsystemCount} processes described?
${processesDescription}
Please structure your analyzed results in the following JSON format:
{
  "processes": [
    {
      "processName": "Process 1",
      "constants": [
        {
          "name": "MAX_USERS",
          "value": "2",
          "description": "Maximum number of users allowed"
        }
      ],
      "variables": [
        {
          "name": "userCount",
          "type": "int",
          "possibleValues": "0 to MAX_USERS",
          "initialValue": "MAX_USERS",
          "description": "Current number of active users"
        },
        {
          "name": "positions",
          "type": "array",
          "possibleValues": "near, far, in",
          "initialValue": "[far, far]",
          "description": "Positions of the two users"
        }
      ]
    }
  ]
}

Requirements for the content:
1. For constants, they have 3 properties: name, value (should be an integer), and description. For variables, they have 4 properties: name, type (integer, array, etc.), possible values (**please ensure the possible values are defined as constants if necessary**), and description.
2. Constants should be defined before variables. The names of variables and constants (including the possible values of variables) must be unique across all processes and must not conflict with any process name.
3. The interaction mode for the processes is ${structuredData.interactionMode}, if the mode is "none" or "choice", note that constants and variables are likely to overlap significantly across processes. In such cases, ensure that shared constants and variables are defined only once - under the first process - and not duplicated in each individual process.
4. Initial values should be specified based on commonsense or process description.
5. Types of variables should be either int or array. If a variable is an array, it is **MANDATORY** to specify its initial value as a list (i.e., the initialValue field cannot be left empty). If no initial value can be reasonably assigned, it indicates that the **possible values are incomplete** and should include additional entries (e.g., it may be necessary to define a value like "disk_empty").
6. The possible values of a variable should be listed out as concrete values separated by "," without "[]". For example: "ENGINE_OFF, ENGINE_ON". It **should not involve any natural language description** (i.e., cannot be something like 0 to MAX_CROSSING_TIME), each possible value **MUST be either a defined constant or a number**.
7. Descriptions should be clear and concise.
8. For processName, please follow exactly the processName entered by the user without any additional natural language description.
9. Variables whose possible values represent actions, transitions, or system control (e.g., moveSelection, activeControl) rather than data states **should not** be included as variables. These are part of the system behavior and will be handled separately during action extraction.

Please ensure your response is a valid JSON string that can be parsed directly.`;

}

function genActionsPrompt(descriptions, processedTables){
  return `As an expert in reasoning and action extraction, analyze the following system: ${descriptions}
Given the list of system variables and their possible values in JSON format:
${JSON.stringify(processedTables)}
Follow these steps:
1. **Identify all possible actions for each process**
- Ensure actions are realistic and align with the system behavior.

2. **Determine the conditions for each action**
- Under what conditions should an action occur?
- What values must the system variables have (including variables from other processes) for the action to be valid?
- **Ensure each condition accounts for dependencies between processes**.

3. Organize the analyzed results into a **JSON format**, each action should have **3 properties**: "action_name", "conditions" (exhaustive list of related variables and values they should assume), and "state_changes" associated with the action (affected variables and their respective new value). For both conditions and state changes, please list the variables with their expected value(s) (the values can be defined constants, numeric values, or expressions combining variables with constants or numbers), instead of using any natural language description. An example JSON is as follows:
{
  "processes": [
    {
      "processName": "Process 1",
      "actions": [
        {
          "action_name": "open",
          "conditions": {
          "owner.i": "near",
          "door": ["closed", "locked"],
          "complex_composite_conditions": "((key == with_owner_i and owner.i == in) or (key == in))"
          },
          "state_changes": {
          "door": "open"
          }
        }
      ]
    }
  ]
}

4. All conditions must be exhaustively listed under the "conditions" field. There should **NEVER** be any conditions inside "state_changes". If a state change depends on an additional condition, the action **must be split** into multiple more specific actions, each with deterministic conditions and unconditional state changes.

5. In "conditions", the reserved keyword "complex_composite_conditions" is used to represent complex composite conditions. This is the **only** case where a key may be something other than a variable name. However, using "complex_composite_conditions" is **strongly discouraged** and should **ONLY BE USED WHEN THERE IS ABSOLUTELY NO STANDARD WAY TO EXPRESS THE CONDITIONS**. All expressions inside "complex_composite_conditions" **MUST** be based solely on **DEFINED VARIABLES** and their valid value relationships.

Ensure that:
- Action names (action_name) must be **unique** and consists of alphanumeric characters and underscores **only**.
- All variables used in conditions and state changes **MUST** be declared in the provided list of system variables, and their assigned values MUST come from the corresponding list of defined possible values.
- The **conditions are specific** and use system variables appropriately by considering dependencies between processes.
- **Avoid overly generic statements** - each process should feel logically connected to system behavior.

Note that some actions **may not have any conditions or state changes**. In such cases, the corresponding field should be an empty JSON object. This is especially appropriate when conditions and changes cannot be determined through common sense reasoning or by analyzing the system description, or when the intended conditions or changes cannot be expressed using the existing variables.

Please ensure your response is a valid JSON string that can be parsed directly.`;
}

function genCodePrompt(general_info, pitfalls_rules, retrieved, system_description, nlInstruction){
  return `You are an expert in PAT (Process Analysis Toolkit), and you already possess a strong understanding of PAT concepts as outlined in the documentation. As a reminder, here are a few key guidelines:
--- Quick Reference ---
General Information: ${general_info}

Pitfalls and Syntax Guidelines: ${pitfalls_rules}

Your task is to generate the PAT code given the corresponding natural language annotation for the system.
### Example:
**Input NL Annotation:** ${retrieved.nl}
**Expected Output:** ${retrieved.code}

Given the general system description: ${system_description}, now generate the PAT code corresponding to the **following system annotation**. Refer to the system description **only** if explicitly guided in the annotation, or if there is a contradiction between the annotation and the description.

### System Annotation:\n${nlInstruction}
\nThe PAT code should be:
### Response:`;
}



