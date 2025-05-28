###### pipline
import json
import time
import datetime
import os
from openai import OpenAI

import anthropic
import subprocess
import re

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

openai_key = os.environ["OPENAI_API_KEY"]
claude_key = os.environ["CLAUDE_API_KEY"]

client = OpenAI(
    api_key=openai_key,
)

client_claude = anthropic.Anthropic(api_key=claude_key)


### read ./test-automated-pipeline.json

# index.html: lines 383 - 484: based on input, process constants and variables
# const-and-vars.html: lines 117 - 131, 152 - 158, 209 - 299: based on input & index.html's llm output, process actions
# action.html: nothing (?)
# assertion.html: fully replaced by just directly reading from PAT-Examples.json (?)
# nl-instruct.html: lines 56 - 151: based on index.html's llm output, const-and-vars's llm output, and input data (assertions), 
# codegen.html: lines 108 - 243 + 271 - 306 **automatically select the longest chunk of code** and proceed to verify.html (if no code blocks or syntax error: trigger regeneration, regeneration constrained to 3 times?): based on nl-instruct.html's processed result & input data (overall description) [and RAG/syntax]:
# verify.html: **save each round's verification results!!!** (e.g., verifications/modelName/round_{i}.json) + only retain: lines 149 - 174 auto save upon success lines 252 - 288 / save mismatch traces for refine.html lines 175 - 197, 205 - 230, 238 - 246: based on codegen.html's verification results
# refine.html: lines 208 - 233 + lines 237 - 305 + lines 319 - 350, similarly, **automatically select the longest chunk of code** and proceed to verify.html (if no code blocks or syntax error: trigger regeneration, regeneration constrained to 3 times?): based on the previous code and verification results

def get_LLM_answers(question, context, history):
    if question:
        try:
            # Get model response
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
            
            # Create interaction record
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            interaction = {
                'timestamp': formatted_time,
                'question': question,
                'answerGPT': answer,
                'context': context,
            }
            history = history.strip()  # 去除空格和换行符

            if history == 'skip':
                return interaction

            if history == 'const':
                msg_history_path = './history/const-history.json'
            elif history == 'action':
                msg_history_path = './history/action-history.json'
            elif history == 'assertion':
                msg_history_path = './history/assertion-history.json'            
            else:
                msg_history_path = './history/history.json'
            try:
                with open(msg_history_path, 'r') as file:
                    history = json.load(file)
            except FileNotFoundError:
                history = []

            history.append(interaction)

            with open(msg_history_path, 'w') as file:
                json.dump(history, file, indent=4)
            
            return interaction
        except Exception as e:
            print(f"Error: {str(e)}")

def save_run_time(model_name, stage,run_time, hasMismatch=None, codegenFailed=None):
    run_time_record_path = f'./run_time_record/{model_name}.json'
    # Make sure the directory exists
    os.makedirs('./run_time_record', exist_ok=True)
    try:
        with open(run_time_record_path, 'r') as file:
            run_time_data = json.load(file)
    except FileNotFoundError:
        print("File not found. Creating a new one.")
        run_time_data = {}
    # Create the data to save
    save_content = {"runTime": run_time}
    if hasMismatch is not None and hasMismatch != "":
        save_content["hasMismatch"] = hasMismatch
    if codegenFailed is not None and codegenFailed != "":
        save_content["codegenFailed"] = codegenFailed
    # Update the dictionary
    run_time_data[stage] = save_content

    # Save back to file
    with open(run_time_record_path, 'w') as file:
        json.dump(run_time_data, file, indent=4)

    return {"message": "Run time saved successfully."}



# save same foloder save in piple
def gen_const_and_vars(structuredData):
    processesDescription = "\n".join(
    f"process {i + 1}: process name: {sub['name']}, process description: {sub['description']}"
    for i, sub in enumerate(structuredData["subsystems"])
)
    protmpt_gen_const_and_vars = f"""As an expert in information extraction and analysis in computer science domain, can you extract all the constants and variables involved in each of the {structuredData['subsystemCount']} processes described?
{processesDescription}
Please structure your analyzed results in the following JSON format:
{{
    "processes": [
    {{
        "processName": "Process 1",
        "constants": [
        {{
            "name": "MAX_USERS",
            "value": "2",
            "description": "Maximum number of users allowed"
        }}
        ],
        "variables": [
        {{
            "name": "userCount",
            "type": "int",
            "possibleValues": "0 to MAX_USERS",
            "initialValue": "MAX_USERS",
            "description": "Current number of active users"
        }},
        {{
            "name": "positions",
            "type": "array",
            "possibleValues": "NEAR,FAR,IN",
            "initialValue": "[FAR,FAR]",
            "description": "Positions of the two users"
        }}
        ]
    }}
    ]
}}

Requirements for the content:
1. For constants, they have 3 properties: name, value (should be an integer), and description. For variables, they have 4 properties: name, type (integer, array, etc.), possible values (**please ensure the possible values are defined as constants if necessary**), and description.
2. Constants should be defined before variables. The names of variables and constants (including the possible values of variables) must be unique across all processes and must not conflict with any process name.
3. The interaction mode for the processes is {structuredData['interactionMode']}. If the mode is "none" or "choice", note that constants and variables are likely to overlap significantly across processes. In such cases, ensure that shared constants and variables are defined only once - under the first process - and not duplicated in each individual process.
4. Initial values should be specified based on commonsense or process description.
5. Types of variables should be either int or array. If a variable is an array, it is **MANDATORY** to specify its initial value as a list (i.e., the initialValue field cannot be left empty). If no initial value can be reasonably assigned, it indicates that the **possible values are incomplete** and should include additional entries (e.g., it may be necessary to define a value like "disk_empty").
6. The possible values of a variable should be listed out as concrete values separated by "," without "[]". For example: "ENGINE_OFF, ENGINE_ON". It **should not involve any natural language description** (i.e., cannot be something like 0 to MAX_CROSSING_TIME), each possible value **MUST be either a defined constant or a number**.
7. Descriptions should be clear and concise.
8. For processName, please follow exactly the processName entered by the user without any additional natural language description.
9. Variables whose possible values represent actions, transitions, or system control (e.g., moveSelection, activeControl) rather than data states **should not** be included as variables. These are part of the system behavior and will be handled separately during action extraction.

Please ensure your response is a valid JSON string that can be parsed directly."""
    start = time.perf_counter()
    ##### use LLM
    print(f"getting const and vars")
    print("prompt_gen_const_and_vars", protmpt_gen_const_and_vars)
    get_LLM_answers(protmpt_gen_const_and_vars, structuredData, 'const')
    end = time.perf_counter()
    run_time = end - start
    save_run_time(structuredData['modelName'], 'const-var-time', run_time)

def _generate_descriptions_for_actions_helper(structured_data):
    modelName = structured_data.get('modelName', 'N/A')
    modelDesc = structured_data.get('modelDesc', 'N/A')
    subsystemCount = structured_data.get('subsystemCount', 0)
    subsystems_data = structured_data.get('subsystems', [])

    desc = f"The user would like to build a system called {modelName}, where {modelDesc}. "
    desc += f"There are {subsystemCount} processes in the system, the descriptions of the processes are as follows: "
    
    subsystem_descs_list = []
    for sub in subsystems_data:
        subsystem_descs_list.append(f"{sub.get('name', 'Unnamed Process')}: {sub.get('description', 'No description')}")
    desc += "; ".join(subsystem_descs_list)
    
    # interaction_mode_value = structured_data.get('interactionMode', '')

    # if interaction_mode_value == 'none':
    #     desc += '. The way that the processes interact with each other is described in the process description.'
    # elif interaction_mode_value == 'interleaving':
    #     desc += '. Overall system combining all the subsystems interleavingly ("|||").'
    # elif interaction_mode_value == 'parallel':
    #     desc += '. Overall system combining all the subsystems with parallel composition ("||").'
    # elif interaction_mode_value == 'choice':
    #     desc += '. Overall system combining all the subsystems by choosing only one to execute ("[]").'
    # elif interaction_mode_value == 'skip':
    #     desc += '. Interaction mode is skipped due to a single component.'
    # else: 
    #     if interaction_mode_value: 
    #          desc += f". The processes interact with each other through the following way: {interaction_mode_value}."
    return desc

def gen_actions(structured_data, processed_tables):
    descriptions_str = _generate_descriptions_for_actions_helper(structured_data)
    try:
        table_info = json.dumps(processed_tables)
    except:
        table_info = processed_tables

    prompt_gen_actions = f"""As an expert in reasoning and action extraction, analyze the following system: {descriptions_str}
Given the list of system variables and their possible values in JSON format:
{table_info}
Follow these steps:
1. **Identify all possible actions for each process**
- Ensure actions are realistic and align with the system behavior.

2. **Determine the conditions for each action**
- Under what conditions should an action occur?
- What values must the system variables have (including variables from other processes) for the action to be valid?
- **Ensure each condition accounts for dependencies between processes**.

3. Organize the analyzed results into a **JSON format**, each action should have **3 properties**: "action_name", "conditions" (exhaustive list of related variables and values they should assume), and "state_changes" associated with the action (affected variables and their respective new value). For both conditions and state changes, please list the variables with their expected value(s) (the values can be defined constants, numeric values, or expressions combining variables with constants or numbers), instead of using any natural language description. An example JSON is as follows:
{{
    "processes": [
    {{
        "processName": "Process 1",
        "actions": [
        {{
            "action_name": "open",
            "conditions": {{
            "owner.i": "near",
            "door": ["closed", "locked"],
            "complex_composite_conditions": "((key == with_owner_i and owner.i == in) or (key == in))"
            }},
            "state_changes": {{
            "door": "open"
            }}
        }}
        ]
    }}
    ]
}}

4. All conditions must be exhaustively listed under the "conditions" field. There should **NEVER** be any conditions inside "state_changes". If a state change depends on an additional condition, the action **must be split** into multiple more specific actions, each with deterministic conditions and unconditional state changes.

5. In "conditions", the reserved keyword "complex_composite_conditions" is used to represent complex composite conditions. This is the **only** case where a key may be something other than a variable name. However, using "complex_composite_conditions" is **strongly discouraged** and should **ONLY BE USED WHEN THERE IS ABSOLUTELY NO STANDARD WAY TO EXPRESS THE CONDITIONS**. All expressions inside "complex_composite_conditions" **MUST** be based solely on **DEFINED VARIABLES** and their valid value relationships.

Ensure that:
- Action names (action_name) must be **unique** and consists of alphanumeric characters and underscores **only**.
- All variables used in conditions and state changes **MUST** be declared in the provided list of system variables, and their assigned values MUST come from the corresponding list of defined possible values.
- The **conditions are specific** and use system variables appropriately by considering dependencies between processes.
- **Avoid overly generic statements** - each process should feel logically connected to system behavior.

Note that some actions **may not have any conditions or state changes**. In such cases, the corresponding field should be an empty JSON object. This is especially appropriate when conditions and changes cannot be determined through common sense reasoning or by analyzing the system description, or when the intended conditions or changes cannot be expressed using the existing variables.

Please ensure your response is a valid JSON string that can be parsed directly."""

    start = time.perf_counter()
    print(f"getting actions")
    print("prompt_gen_actions", prompt_gen_actions)
    get_LLM_answers(prompt_gen_actions, processed_tables, 'action')
    end = time.perf_counter()
    run_time = end - start
    
    model_name = structured_data.get('modelName', 'unknown_model')
    save_run_time(model_name, 'action-time', run_time)

def _process_assertions_for_nl_helper(structured_data, assertions_list):
    modelName = structured_data.get("modelName", "UnknownModel")
    interaction_mode = structured_data.get("interactionMode", "").strip().lower()

    nl_annotations_assertion = [""]  # Start with a blank line for separation

    # Part 1: Process interactionMode for overall system definition
    if interaction_mode == "interleaving":
        assertion_part_1 = f'// define the {modelName} system: overall system combining all the subsystems interleavingly ("|||"), consider defining the system around the most central variable (e.g., the number of owners) only if appropriate'
        nl_annotations_assertion.append(assertion_part_1)
    elif interaction_mode == "parallel":
        assertion_part_1 = f'// define the {modelName} system: overall system combining all the subsystems with parallel composition ("||"), consider defining the system around the most central variable (e.g., the number of owners) only if appropriate'
        nl_annotations_assertion.append(assertion_part_1)
    elif interaction_mode == "choice":
        assertion_part_1 = f'// define the {modelName} system: overall system combining all the subsystems by choosing only one to execute ("[]"), consider defining the system around the most central variable (e.g., the number of owners) only if appropriate. Note that **each subsystem** should go back to this **overall system**.'
        nl_annotations_assertion.append(assertion_part_1)
    elif interaction_mode == "none":
        assertion_part_1 = f'// there is **no need** to define an overall system or explicitly combine the processes. However, ensure that the generated processes **transfer control** to each other as described in the system description, reflecting the intended interactions'
        nl_annotations_assertion.append(assertion_part_1)
    elif interaction_mode == "skip":
        pass  # No specific overall system definition for 'skip'
    else:  # Customized interaction
        assertion_part_1 = f'// define the {modelName} system following the description: {interaction_mode}'
        nl_annotations_assertion.append(assertion_part_1)

    nl_annotations_assertion.append("// define **exactly** the following states and assertions as specified. Do **NOT** add, modify, or omit anything")

    for assertion_item in assertions_list:
        component_name = assertion_item.get("component")
        sys_or_process = f'subsystem {component_name}' if component_name else f'{modelName} system'
        assertion_type = assertion_item.get("assertionType", "").strip().lower()

        if assertion_type == "deadlock-free":
            nl_annotations_assertion.append(f"// assert {sys_or_process} deadlockfree")
        elif assertion_type == "reachability":
            stateName = assertion_item.get("stateName", "").strip()
            conditions = assertion_item.get("conditions", [])
            reachabilityType = assertion_item.get("reachabilityType", "").strip().lower()
            
            cond_str_parts = []
            if reachabilityType == "customize":
                cond_str = assertion_item.get("customDescription", "")
            else:
                for i, cond in enumerate(conditions):
                    variable = cond.get("variable", "").strip()
                    value = cond.get("value", "").strip()
                    if variable and value:
                        expr = f"{variable} = {value}"
                        if i > 0:
                            connector = cond.get("connector", "AND").strip().upper() # Default to AND
                            cond_str_parts.append(f"{connector} {expr}")
                        else:
                            cond_str_parts.append(expr)
                cond_str = " ".join(cond_str_parts) if cond_str_parts else "no conditions provided"

            nl_annotations_assertion.append(f"// define {stateName if stateName else '{stateName}'}: {cond_str}")
            nl_annotations_assertion.append(f"// assert that the {sys_or_process} can reach the state \"{stateName}\"")
        elif assertion_type == "ltl":
            ltl_target = assertion_item.get("ltlTarget", "").strip().lower()
            ltl_logic = assertion_item.get("ltlLogic", "").strip().replace("_", " ")

            if ltl_target == 'customize':
                custom_desc = assertion_item.get("customDescription","")
                nl_annotations_assertion.append(f"// {custom_desc}")
            elif ltl_target == "action":
                selectedActions = assertion_item.get("selectedActions", [])
                selectedActions_str = ", ".join(map(str, selectedActions)) if isinstance(selectedActions, list) else str(selectedActions).strip()
                nl_annotations_assertion.append(f'// assert that the {sys_or_process} will {ltl_logic} perform those actions "{selectedActions_str}"')
            elif ltl_target == "state":
                stateName = assertion_item.get("stateName", "").strip()
                conditions = assertion_item.get("conditions", [])
                cond_str_parts = []
                for i, cond in enumerate(conditions): # Added index i here
                    variable = cond.get("variable", "").strip()
                    value = cond.get("value", "").strip()
                    if variable and value:
                        cond_str_parts.append(f"{variable} = {value}")
                cond_str = " and ".join(cond_str_parts) if cond_str_parts else "no conditions provided"
                nl_annotations_assertion.append(f"// define {stateName if stateName else '{stateName}'}: {cond_str}")
                nl_annotations_assertion.append(f"// assert that the {sys_or_process} will {ltl_logic} reach the state \"{stateName}\"")
                
    return "\n".join(nl_annotations_assertion)

def gen_nl_instructions(structured_data, const_answer_str, action_answer_str, assertions_list):
    start_time = time.perf_counter()
    
    # Part 1: NL for Constants
    data1_content = ""
    try:
        try:
            parsed_const_data = json.loads(const_answer_str)
            info = json.dumps(parsed_const_data)
        except json.JSONDecodeError:
            # not valid JSON, put into prompt as a string
            parsed_const_data = const_answer_str
            info = const_answer_str
        
        prompt1 = f"""According to the following json data, please generate NL annotation for PAT code generation, for example, to define the number of owners, you should generate such an annotation: // "N": number of owners in the system (set to 2), and to define the constant "far", you should generate this annotation: // "far": represents an owner being out and far away from the car. The annotation for each constant and variable should be generated on a new line. **Note: 1. For variables, there is no need to specify possible values, only specify the initial value for each variable. 2. Generate the annotations for all constants before variables.** The json data is as follows:\n{info}"""

        data1_interaction = get_LLM_answers(prompt1, parsed_const_data, 'skip')
        if data1_interaction and 'answerGPT' in data1_interaction:
            data1_content = data1_interaction['answerGPT']
        else:
            print("Error: Failed to get NL for constants or answerGPT missing.")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from const_answer_str for NL generation.")
    except Exception as e:
        print(f"Error in generating NL for constants: {str(e)}")

    # Part 2: NL for Actions
    data2_content = ""
    try:
        try:
            parsed_action_data = json.loads(action_answer_str)
            info_action = json.dumps(parsed_action_data)
        except json.JSONDecodeError:
            parsed_action_data = action_answer_str
            info_action = action_answer_str
        
        prompt2 = f"""According to the following json data, please generate the NL annotation for PAT code generation. For each process, start the annotation with an annotation line // Definition of the "process_name" subsystem. (if any variable is involved in the process, please also add the description like: for xxx with index i). To annotate the actions that can happen in processes, we specify the conditions, action name, and the changes that the action introduces for the variables. For example, an annotation might be: //if "owner[i]" is "far", the action "towards.i" makes "owner[i]" become "near" (owner approaches the car). Note that, when processing conditions, if "complex_composite_conditions" exists as a key, its value alone forms the condition and should be directly described without mentioning "complex_composite_conditions". For other entries in conditions, the key and value together form the condition. Now please generate the NL annotations for each process in the json data, ensuring that the annotation for each action will span a new row. The json data is as follows:\n{info_action}"""
        
        data2_interaction = get_LLM_answers(prompt2, parsed_action_data, 'skip')
        if data2_interaction and 'answerGPT' in data2_interaction:
            data2_content = data2_interaction['answerGPT']
        else:
            print("Error: Failed to get NL for actions or answerGPT missing.")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from action_answer_str for NL generation.")
    except Exception as e:
        print(f"Error in generating NL for actions: {str(e)}")

    # Part 3: NL for Assertions
    data3_content = _process_assertions_for_nl_helper(structured_data, assertions_list)

    # Combine and Save
    full_prompt = f"{data1_content}\n{data2_content}\n{data3_content}"

    # Save parts
    nl_parts_path = './history/nl-instruction-part.json'
    try:
        with open(nl_parts_path, 'r') as f:
            existing_parts_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_parts_data = []
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_part_entry = {
        "timestamp": current_time, # Added timestamp
        "data1": data1_content,
        "data2": data2_content,
        "data3": data3_content
    }
    existing_parts_data.append(new_part_entry)
    with open(nl_parts_path, 'w') as f:
        json.dump(existing_parts_data, f, indent=2)
    
    print("Assertion Annotations: ", data3_content)

    # Save full prompt
    nl_claude_path = './history/nl-instruction-claude.json'
    try:
        with open(nl_claude_path, 'r') as f:
            existing_claude_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_claude_data = []
    
    new_claude_entry = {
        "timestamp": current_time, # Added timestamp
        "fullText": full_prompt
    }
    existing_claude_data.append(new_claude_entry)
    with open(nl_claude_path, 'w') as f:
        json.dump(existing_claude_data, f, indent=2)

    end_time = time.perf_counter()
    run_time = end_time - start_time
    model_name = structured_data.get('modelName', 'unknown_model')
    save_run_time(model_name, 'nl-annotation-time', run_time)
    
    print(f"NL Instructions generated and saved for {model_name}.")

def _get_most_relevant_rag_example_basic(instruction, rag_database_path='./database-rag-claude.json'):
    try:
        with open(rag_database_path, 'r') as f:
            database = json.load(f)
        
        if not instruction:
            print("Warning: RAG instruction is empty. Returning no example.")
            return {"nl": "", "code": ""}

        nls = [entry["nl"] for entry in database if entry.get("nl")]
        if not nls:
            print("Warning: No valid RAG database.")
            return {"nl": "", "code": ""}
        
        vectorizer = TfidfVectorizer().fit(nls + [instruction])
        vectors = vectorizer.transform(nls + [instruction])

        similarity_scores = cosine_similarity(vectors[-1], vectors[:-1])[0]
        most_similar_idx = similarity_scores.argmax()

        matched_entry = database[most_similar_idx]
        return {"nl": matched_entry["nl"], "code": matched_entry["code"]}
            
    except FileNotFoundError:
        print(f"Error: RAG database file not found at {rag_database_path}")
        return {"nl": "", "code": ""}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from RAG database file {rag_database_path}")
        return {"nl": "", "code": ""}

def _get_claude_code_completion(prompt_text, history_file_path):
    global client_claude # Ensure client_claude is accessible
    try:
        response = client_claude.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=8192, # Max tokens as in codegen.html
            messages=[{"role": "user", "content": prompt_text}]
        )
        answer = response.content[0].text

        current_time_dt = datetime.datetime.now()
        formatted_time = current_time_dt.strftime("%Y-%m-%d %H:%M:%S")

        interaction = {
            'timestamp': formatted_time,
            'question': prompt_text, # Saving the full prompt might be verbose
            'answerClaude': answer,
            'PAT': "" # Consistent with server.py structure
        }

        try:
            with open(history_file_path, 'r') as f:
                history_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history_data = []
        
        history_data.append(interaction)

        with open(history_file_path, 'w') as f:
            json.dump(history_data, f, indent=4)
        
        return answer
    except Exception as e:
        print(f"Error calling Claude model or saving to {history_file_path}: {str(e)}")
        return "" # Return empty string on error

def gen_code(structured_data, full_nl_prompt):
    model_name = structured_data.get('modelName', 'unknown_model')
    print(f"Starting code generation for {model_name}...")
    start_time = time.perf_counter()

    # 1. RAG: Get most relevant example
    print("Retrieving RAG example...")
    retrieved_example = _get_most_relevant_rag_example_basic(full_nl_prompt)
    retrieved_nl = retrieved_example['nl']
    retrieved_code = retrieved_example['code']
    # print(f"RAG NL: {retrieved_nl[:100]}...\nRAG Code: {retrieved_code[:100]}...")

    # 2. Read Syntax Data
    syntax_general_info = ""
    syntax_pitfalls_rules = ""
    try:
        with open('./syntax-dataset.json', 'r') as f:
            syntax_data = json.load(f)
        syntax_general_info = syntax_data.get("general_info", "")
        syntax_pitfalls_rules = syntax_data.get("pitfalls_rules", "")
        # print("Syntax data loaded.")
    except FileNotFoundError:
        print("Error: syntax-dataset.json not found.")
    except json.JSONDecodeError:
        print("Error: Could not decode syntax-dataset.json.")

    # 3. Generate System Description for the prompt
    # Using the existing helper, it also includes interaction mode which might be fine for context
    system_description_for_prompt = _generate_descriptions_for_actions_helper(structured_data)
    # print(f"System description for prompt: {system_description_for_prompt[:200]}...")

    # 4. Construct Final Prompt for Claude
    # Based on codegen.html prompt structure
    final_code_gen_prompt = f"""You are an expert in PAT (Process Analysis Toolkit), and you already possess a strong understanding of PAT concepts as outlined in the documentation. As a reminder, here are a few key guidelines:
--- Quick Reference ---
General Information: {syntax_general_info}

Pitfalls and Syntax Guidelines: {syntax_pitfalls_rules}

Your task is to generate the PAT code given the corresponding natural language annotation for the system.
### Example:
**Input NL Annotation:** {retrieved_nl}
**Expected Output:** {retrieved_code}

Given the general system description: {system_description_for_prompt}, now generate the PAT code corresponding to the **following system annotation**. Refer to the system description **only** if explicitly guided in the annotation, or if there is a contradiction between the annotation and the description.

### System Annotation:\n{full_nl_prompt}

The PAT code should be:
### Response:"""
    
    # print(f"Final prompt for Claude: {final_code_gen_prompt[:500]}...")

    # 5. Call Claude Model for code generation
    print("Calling Claude for code generation...")
    print("prompt_gen_code", final_code_gen_prompt)
    generated_code_output = _get_claude_code_completion(final_code_gen_prompt, './history/claude-code.json')
    
    if not generated_code_output:
        print(f"Code generation failed for {model_name}.")
        # Fallback or error handling could be added here

    # 6. Timing and Saving Runtime
    end_time = time.perf_counter()
    run_time = end_time - start_time
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    save_run_time(model_name, f'codegen-time_{timestamp}', run_time)
    
    print(f"Code generation for {model_name} completed in {run_time:.2f} seconds. Output saved.")
    # No longer returns generated_code_output

def _split_code_and_assertions(code):
    """
    Split PAT code into separate blocks for verification, one per assertion.
    """
    # Match any number of `#define…\n` lines, then one `#assert…;?`
    pat = re.compile(
        r'(?m)'                   # multiline mode
        r'(?:'                    # start group for repeated #defines
            r'^(?!\s*//)\s*'        # ── must be at line start, not // comment
            r'#define[^\n]*\n'      # ── a real #define line
        r')*'                     # repeat zero or more times
        r'^(?!\s*//)\s*'          # ── now for the #assert line…
        r'#assert[^\n]*;?'        # ── a real #assert
        )
    # body = everything except those define/assert pairs
    body = pat.sub('', code).strip()
    # capture each define+assert block
    blocks = pat.findall(code)
    defs, asserts = [], []
    for blk in blocks:
        lines = blk.splitlines()
        # if it starts with a define, collect it
        for line in lines[:-1]:
            if line.startswith('#define'):
                defs.append(line)
        # the last line is always the #assert
        asserts.append(lines[-1])
    # dedupe while preserving order
    seen = set()
    uniq_defs = [d for d in defs if not (d in seen or seen.add(d))]
    # build one output per assertion
    return [
        body + '\n\n' + '\n'.join(uniq_defs + [a])
        for a in asserts
    ]

def verify_code(structured_data, code_to_verify, is_refine=False, refine_round=0):
    """
    Verify the generated code using PAT.
    Checks assertions against expected outcomes and handles mismatches.
    Returns verification results, whether there are mismatches, and if any empty outputs were encountered.
    """
    try:
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        new_record = {
            "timestamp": formatted_time,
            "processedCode": code_to_verify
        }
        filename = "./history/claude-refinement.json"
        try:
            with open(filename, "r", encoding="utf-8") as f:
                refinement_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            refinement_data = []
        refinement_data.append(new_record)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(refinement_data, f, indent=2)
    except Exception as e:
        print("Error saving claude-refinement.json:", e)
        
    print(f"Starting code verification...")
    start_time = time.perf_counter()
    model_name = structured_data.get('modelName', 'unknown_model')
    
    # Setup directories
    root_path = "path_to_your_root_directory"  # Replace with your actual root path
    
    if is_refine:
        # If we're refining, create a specific subdirectory for this round
        folder_path = f"{root_path}/Automated_Pipelines/Full_Pipeline/generated_code/{model_name}/refine_round_{refine_round}"
    else:
        # Initial verification uses the main model directory
        folder_path = f"{root_path}/Automated_Pipelines/Full_Pipeline/generated_code/{model_name}"
    
    # Create the directory if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    else:
        # Only clean up files if we're not in refinement mode
        if not is_refine:
            # Clean up any existing files in the directory
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error removing file {file_path}: {e}")
    
    # Split the code into separate blocks for verification
    code_blocks = _split_code_and_assertions(code_to_verify)
    
    # Record verification results
    verification_results = []
    any_empty = False

    if len(code_blocks) != len(structured_data['assertions']):
        print(f"Warning: Number of code blocks ({len(code_blocks)}) does not match number of assertions ({len(structured_data['assertions'])}).")
        return [], True, True
    
    # Save each code block and verify it
    for i, block in enumerate(code_blocks):
        input_file = f"{folder_path}/{i}.csp"
        output_file = f"{folder_path}/pat_output_{i}.txt"
        
        # Save the code block to file
        try:
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(block)
        except Exception as e:
            print(f"Error saving code block {i} to file: {e}")
            any_empty = True  # Mark as having issues
            continue
        
        # Choose the appropriate command based on the assertion type
        if ('reaches' in block) or ('deadlockfree' in block):
            command = ["mono", f"{root_path}/PAT.Console/Process-Analysis-Toolkit/PAT3.Console.exe",
                      "-csp", "-engine", "1", input_file, output_file]
        else:
            command = ["mono", f"{root_path}/PAT.Console/Process-Analysis-Toolkit/PAT3.Console.exe",
                      "-csp", input_file, output_file]
        
        # Run the PAT verification
        try:
            subprocess.run(command, check=True, timeout=300)
            with open(output_file, 'r', encoding='utf-8') as f:
                output = f.read()
            if output == "":
                any_empty = True
                print(f"Warning: Empty output for assertion {i} - potential syntax error")
            
            # Extract verification result
            start_marker = "********Verification Result********"
            end_marker = "********Verification Setting********"
            start_idx = output.find(start_marker)
            end_idx = output.find(end_marker)
            
            pat_result = ""
            if start_idx != -1 and end_idx != -1:
                pat_result = output[start_idx + len(start_marker):end_idx].strip()
            else:
                # No proper verification result found
                any_empty = True
                pat_result = "Verification result not found - potential syntax error"
            
            # Extract the assertion line from the code block
            assertion_line = ""
            for line in block.splitlines():
                if line.strip().startswith("#assert"):
                    assertion_line = line.strip()
                    break
            
            # Determine actual outcome
            actual_outcome = ""
            match = re.search(r"is\s+(\w+)", pat_result, re.IGNORECASE)
            if match and match.group(1):
                word = match.group(1).upper()
                if word == "VALID":
                    actual_outcome = "Valid"
                else:
                    actual_outcome = "Invalid"
            else:
                # No outcome detected
                any_empty = True
            
            verification_results.append({
                'assertion': assertion_line,
                'patResult': pat_result,
                'actualResult': actual_outcome
            })
        except subprocess.TimeoutExpired:
            print(f"PAT execution timed out for assertion {i}")
            return [], True, True
        except subprocess.CalledProcessError as e:
            print(f"PAT execution failed for assertion {i}: {e}")
            return [], True, True
        except Exception as e:
            print(f"Error processing verification for assertion {i}: {e}")
            return [], True, True
    
    # Get expected outcomes from the assertions data in the structured_data
    assertions_list = structured_data.get('assertions', [])
    has_mismatch = False
    
    # Compare actual outcomes with expected outcomes
    mismatches = []
    for i, result in enumerate(verification_results):
        # Default expected outcome is "Valid"
        expected_outcome = "Valid"
        if i < len(assertions_list):
            outcome_str = assertions_list[i].get("assertionTruth", "").strip()
            expected_outcome = outcome_str if outcome_str else "Valid"
        
        result['desiredOutcome'] = expected_outcome
        
        # Check for mismatch
        if result['actualResult'] != expected_outcome:
            has_mismatch = True
            
            # Extract trace information for mismatches
            lines = result['patResult'].split("\n")
            trace = "<init>"  # Default if no specific trace found
            
            # Look for trace information in the result
            for line in lines:
                if "->" in line and line.strip().startswith("<"):
                    trace = line.strip()
                    break
            
            mismatches.append({
                'assertion': result['assertion'],
                'trace': trace,
                'current_result': result['actualResult'],
                'desired_result': expected_outcome
            })
    
    # Save mismatch traces if any
    if has_mismatch:
        mismatch_file = f"{folder_path}/mismatch_traces.json"
        try:
            with open(mismatch_file, 'w', encoding='utf-8') as f:
                json.dump(mismatches, f, indent=2)
            print(f"Saved {len(mismatches)} mismatch traces to {mismatch_file}")
            
            # Also save to the standard history location for compatibility
            if not is_refine:
                with open('./history/mismatch_traces.json', 'w', encoding='utf-8') as f:
                    json.dump(mismatches, f, indent=2)
        except Exception as e:
            print(f"Error saving mismatch traces: {e}")
    else:
        # If no mismatches, save verified code
        verified_code_path = f"{folder_path}/verifiedCode.csp"
        try:
            with open(verified_code_path, 'w', encoding='utf-8') as f:
                f.write(code_to_verify)
            print(f"Saved verified code to {verified_code_path}")
            try:
                with open('./database-algorithm.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                data = []
            data.append({"model_name": model_name, "verified_code": code_to_verify})
            with open('./database-algorithm.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved verified code for {model_name} model to database-algorithm.json")
        except Exception as e:
            print(f"Error saving verified code: {e}")
    
    # Save verification results
    verification_results_path = f"{folder_path}/verification_results.json"
    try:
        with open(verification_results_path, 'w', encoding='utf-8') as f:
            json.dump(verification_results, f, indent=2)
        print(f"Saved verification results to {verification_results_path}")
    except Exception as e:
        print(f"Error saving verification results: {e}")
    
    # Record timing
    end_time = time.perf_counter()
    run_time = end_time - start_time
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    save_run_time(model_name, f'verification-time_{timestamp}', run_time, has_mismatch, any_empty)
    
    print(f"Code verification completed in {run_time:.2f} seconds. Has mismatches: {has_mismatch}, Has empty results: {any_empty}")
    return verification_results, has_mismatch, any_empty

def _process_mismatch_traces(mismatches):
    """
    Process mismatch traces to generate feedback for Claude to use in refinement.
    """
    processed_messages = []
    
    for refinement_point in mismatches:
        if processed_messages:
            processed_messages.append("Apart from this, please also take note of the following mistake that we need to correct.")
            
        assertion = refinement_point.get('assertion', '')
        trace = refinement_point.get('trace', '')
        current_result = refinement_point.get('current_result', '')
        desired_result = refinement_point.get('desired_result', '')
        
        if "deadlockfree" in assertion:
            message = (
                f"The generated code does not satisfy the following property: {assertion}, "
                f"meaning that the system is prone to deadlock, which is the opposite to the desired result. "
                f"Through analyzing your current implementation, we identify that "
                f"deadlock can be triggered by this trace: {trace}. Therefore, please analyze whether there are any states in the system that don't have any outgoing transitions, with a particular focus on the actions involved in the trace, "
                f"and make sure that the system is deadlock-free. "
            )
        elif trace == "<init>":
            message = (
                f"The generated code does not satisfy the following property: {assertion}, "
                f"its current verification result is {current_result}, which is the opposite to the expected result "
                f"of the desired system ({desired_result}). Through analyzing your current implementation, we identify that "
                f"this assertion is violated after the initialization of the system. Therefore, please analyze the initial "
                f"values of the variables involved in this assertion, and make sure that the initial values of the variables, "
                f"the definitions of the constants which serve as the possible values of the variables are logically correct "
                f"and will not lead to the assertion {assertion} being {current_result} with the initialization."
            )
        else:
            actions = [action.strip() for action in trace.strip("<>").split("->")]
            last_action = actions[-1]
            other_actions = ", ".join(actions[:-1])
            message = (
                f"The generated code does not satisfy the following property: {assertion}, its current verification result is {current_result}, "
                f"which is the opposite to the expected result of the desired system ({desired_result}). Through analyzing your current implementation, "
                f"we identify that this assertion is violated after performing the {last_action} action. Therefore, please carefully analyze if the guarded condition "
                f"of performing the {last_action} action is weaker than it should be, possibly missing out some requirements for the action to be valid. "
                f"If, after careful analysis, you think the problem is not with the {last_action} action, then carefully analyze these actions as well: {other_actions}. "
                f"Please make sure that the conditions of those actions happening are strict enough to not lead to the assertion {assertion} being {current_result}."
            )
        processed_messages.append(message)
    
    return "\n".join(processed_messages)

def gen_refine(structured_data, current_code, mismatches, refine_round):
    """
    Generate refined code based on verification mismatches.
    Returns the refined code.
    """
    print(f"Starting code refinement round {refine_round}...")
    start_time = time.perf_counter()
    model_name = structured_data.get('modelName', 'unknown_model')
    
    # Process mismatch traces into feedback for Claude
    processed_traces = _process_mismatch_traces(mismatches)
    
    # Construct refinement prompt
    refinement_prompt = f'''You are an expert in PAT (Process Analysis Toolkit). Your task now is to refine your previously generated PAT code according to some suggestions.\n\nYour previously generated PAT code is as follows:\n{current_code}\n\nThe logic that we can follow to refine our code to satisfy user requirements is:\n{processed_traces}\n\nPlease refine and fix the PAT code so that it avoids the problems we mentioned, and only through modifying code relevant to our suggestions. **The other parts of code should not be changed to avoid syntax error, especially, NEVER remove semicolons.** Please provide the revised PAT code.'''

    # Call Claude for refinement
    print("Calling Claude for code refinement...")
    print("prompt_refine", refinement_prompt)
    refined_code = _get_claude_code_completion(refinement_prompt, './history/claude-code.json')
    
    if not refined_code:
        print(f"Failed to get refined code for round {refine_round}.")
        return current_code  # Return original code if refinement fails
    
    # Save the refined code to a specific file for this round
    model_name = structured_data.get('modelName', 'unknown_model')
    root_path = "path_to_your_root_directory"  # Replace with your actual root path
    folder_path = f"{root_path}/Automated_Pipelines/Full_Pipeline/generated_code/{model_name}"
    refined_code_path = f"{folder_path}/refined_code_{refine_round}.csp"
    
    try:
        with open(refined_code_path, 'w', encoding='utf-8') as f:
            f.write(refined_code)
        print(f"Saved refined code for round {refine_round} to {refined_code_path}")
    except Exception as e:
        print(f"Error saving refined code for round {refine_round}: {e}")
    
    # Record timing
    end_time = time.perf_counter()
    run_time = end_time - start_time
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    save_run_time(model_name, f'refine-time_{refine_round}_{timestamp}', run_time)
    
    print(f"Code refinement round {refine_round} completed in {run_time:.2f} seconds.")
    return refined_code

def _extract_longest_code_block(text):
    """
    Extract the longest code block from a text which might contain multiple code blocks.
    Code blocks are expected to be enclosed in triple backticks.
    Returns the longest code block found, or the original text if no code blocks are found.
    """
    print("Extracting longest code block from LLM response...")
    
    # Pattern to match code blocks with or without language specifier
    # For example: ```python ... ``` or ``` ... ```
    code_block_pattern = r"```(?:[a-zA-Z]*\n)?(.*?)```"
    
    # Find all code blocks
    code_blocks = re.findall(code_block_pattern, text, re.DOTALL)
    
    if not code_blocks:
        print("No code blocks found with triple backticks. Using entire text.")
        return text.strip()
    
    # Find the longest code block
    longest_block = max(code_blocks, key=len)
    
    # Print some stats about the code blocks
    print(f"Found {len(code_blocks)} code blocks. Selected longest with {len(longest_block)} characters.")
    
    return longest_block.strip()

if __name__ == '__main__':
    # read ./test-automated-pipeline.json
    with open('./PAT-Examples-CSP-dataset.json', 'r') as file:
        structured_data_list = json.load(file)
        assert len(structured_data_list) == 6, "The number of entries in the JSON file should be 6."
        for i in range(len(structured_data_list)): # Iterate through all entries in the JSON
        # for i in range(1):
            current_structured_data = structured_data_list[i]
            print(f"Processing data entry {i} with model name: {current_structured_data.get('modelName', 'N/A')}")
            
            # Stage 1: Generate Constants and Variables
            print(f"getting const and vars for entry {i}")
            gen_const_and_vars(current_structured_data)
            
            # Retrieve the result of gen_const_and_vars to pass to gen_actions
            processed_tables_for_actions = None
            const_history_path = './history/const-history.json'
            try:
                with open(const_history_path, 'r') as hist_file:
                    const_history = json.load(hist_file)
                if const_history:
                    # Assuming the last entry corresponds to the gen_const_and_vars call just made
                    latest_const_answer_str = const_history[-1]['answerGPT']
                    try:
                        processed_tables_for_actions = json.loads(latest_const_answer_str)
                    except json.JSONDecodeError:
                        processed_tables_for_actions = latest_const_answer_str
                else:
                    print(f"Error: Const history is empty after processing entry {i}.")
                    continue # Skip to next data entry if const generation failed to produce history
            except FileNotFoundError:
                print(f"Error: Const history file not found at {const_history_path} for entry {i}")
                continue
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from const_history for entry {i}")
                continue
            
            if processed_tables_for_actions is None:
                print(f"Skipping action generation for entry {i} due to missing processed tables.")
                continue

            # Stage 2: Generate Actions
            print(f"getting actions for entry {i}")
            gen_actions(current_structured_data, processed_tables_for_actions)
            
            # Stage 3: Retrieve data for NL Instruction Generation
            print(f"preparing for NL instruction generation for entry {i}")
            
            latest_action_answer_str = None
            action_history_path = './history/action-history.json'
            try:
                with open(action_history_path, 'r') as hist_file:
                    action_history = json.load(hist_file)
                if action_history:
                    latest_action_answer_str = action_history[-1]['answerGPT']
                else:
                    print(f"Error: Action history is empty for entry {i} before NL generation.")
                    continue
            except FileNotFoundError:
                print(f"Error: Action history file not found at {action_history_path} for entry {i}")
                continue
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from action_history for entry {i}")
                continue

            if latest_const_answer_str is None or latest_action_answer_str is None:
                print(f"Skipping NL instruction generation for entry {i} due to missing const or action answers.")
                continue
                
            assertions_list = current_structured_data.get('assertions', [])
            if not assertions_list:
                 print(f"Warning: No assertions found in structured_data for entry {i}. NL for assertions will be minimal.")

            
            # Stage 4: Generate NL Instructions
            print(f"generating NL instructions for entry {i}")
            gen_nl_instructions(current_structured_data, latest_const_answer_str, latest_action_answer_str, assertions_list)

            # Retrieve the full_nl_prompt from the file saved by gen_nl_instructions
            retrieved_full_nl_prompt = None
            nl_claude_history_path = './history/nl-instruction-claude.json'
            try:
                with open(nl_claude_history_path, 'r') as hist_file:
                    nl_claude_history = json.load(hist_file)
                if nl_claude_history:
                    retrieved_full_nl_prompt = nl_claude_history[-1].get('fullText')
                else:
                    print(f"Error: NL Claude history is empty for entry {i}.")
                    continue
                if not retrieved_full_nl_prompt:
                    print(f"Error: 'fullText' not found in the last NL Claude history entry for entry {i}.")
                    continue # Skip to next data entry
            except FileNotFoundError:
                print(f"Error: NL Claude history file not found at {nl_claude_history_path} for entry {i}")
                continue
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from NL Claude history for entry {i}")
                continue

            if not retrieved_full_nl_prompt:
                print(f"Skipping code generation for entry {i} due to empty or missing NL prompt from history.")
                continue
            
            # Stage 5 & 6: Generate code and verify, with up to 3 generation attempts
            gen_count = 0
            max_gen_attempts = 3
            verified_successfully = False
            
            while gen_count < max_gen_attempts and not verified_successfully:
                # Generate code
                if gen_count > 0:
                    print(f"Regenerating code (attempt {gen_count}/{max_gen_attempts - 1}).")
                else:
                    print(f"Starting code generation for entry {i}, attempt {gen_count + 1}/{max_gen_attempts}")
                gen_code(current_structured_data, retrieved_full_nl_prompt)
                gen_count += 1

                # Retrieve the generated code
                retrieved_generated_code = None
                claude_code_history_path = './history/claude-code.json'
                try:
                    with open(claude_code_history_path, 'r') as hist_file:
                        claude_code_history = json.load(hist_file)
                    if claude_code_history:
                        retrieved_generated_code = claude_code_history[-1].get('answerClaude')
                    else:
                        print(f"Error: Claude code history is empty for entry {i}.")
                        break
                    if not retrieved_generated_code:
                        print(f"Error: 'answerClaude' not found in the last Claude code history entry for entry {i}.")
                        break
                except FileNotFoundError:
                    print(f"Error: Claude code history file not found at {claude_code_history_path} for entry {i}")
                    break
                except json.JSONDecodeError:
                    print(f"Error: Could not decode JSON from Claude code history for entry {i}")
                    break

                if not retrieved_generated_code:
                    print(f"Could not retrieve generated code for entry {i}. Skipping verification stage.")
                    break
                
                # Extract the longest code block from the LLM response
                longest_code_block = _extract_longest_code_block(retrieved_generated_code)
                if longest_code_block == "":
                    continue
                
                # Save both the original response and the extracted code for reference
                model_name = current_structured_data.get('modelName', 'unknown_model')
                root_path = "path_to_your_root_directory"  # Replace with your actual root path
                folder_path = f"{root_path}/Automated_Pipelines/Full_Pipeline/generated_code/{model_name}"
                os.makedirs(folder_path, exist_ok=True)
                
                try:
                    with open(f"{folder_path}/original_llm_response.txt", 'w', encoding='utf-8') as f:
                        f.write(retrieved_generated_code)
                    with open(f"{folder_path}/extracted_code.csp", 'w', encoding='utf-8') as f:
                        f.write(longest_code_block)
                    print("Saved original LLM response and extracted code block for reference")
                except Exception as e:
                    print(f"Error saving original/extracted code: {e}")

                # Verify code
                print(f"Starting code verification for entry {i}")
                verification_results, has_mismatch, any_empty = verify_code(current_structured_data, longest_code_block)
                print(f"Verification result: has_mismatch={has_mismatch}, any_empty={any_empty}")
                
                # If no syntax errors, consider verification successful and exit loop
                if not any_empty:
                    verified_successfully = True
                    print(f"Code verified without syntax errors on attempt {gen_count}")
                    break
                else:
                    # If this was the last attempt, save error information
                    if gen_count >= max_gen_attempts:
                        print(f"Maximum regeneration attempts ({max_gen_attempts}) reached. Could not produce error-free code.")
                        # Save information about the failed attempts
                        error_info_path = f"./generated_code/{current_structured_data.get('modelName', 'unknown')}/regeneration_errors.json"
                        try:
                            with open(error_info_path, 'w') as f:
                                json.dump({
                                    "attempts": gen_count,
                                    "last_error_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "verification_results": verification_results
                                }, f, indent=2)
                        except Exception as e:
                            print(f"Error saving regeneration info: {e}")
                    else:
                        print(f"Code has syntax errors, will attempt regeneration. Attempt {gen_count + 1}/{max_gen_attempts}")
                                
            # Stage 7: Refinement - if we have mismatches but no syntax errors
            if verified_successfully and has_mismatch:
                print("Code verified without syntax errors but has logical mismatches. Proceeding to refinement stage.")
                
                # Prepare for refinement
                current_code = longest_code_block  # Use the extracted code block
                max_refine_attempts = 5
                refine_count = 0
                all_mismatches_fixed = False
                model_name = current_structured_data.get('modelName', 'unknown_model')
                
                # Main directory for the model
                root_path = "path_to_your_root_directory"  # Replace with your actual root path
                model_dir = f"{root_path}/Automated_Pipelines/Full_Pipeline/generated_code/{model_name}"
                
                # Make sure the model directory exists
                os.makedirs(model_dir, exist_ok=True)
                
                # Read the mismatches from the standard location
                mismatches = []
                try:
                    with open('./history/mismatch_traces.json', 'r', encoding='utf-8') as f:
                        mismatches = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading mismatch traces: {e}")
                    # Fallback to using verification results to create mismatch data
                    for result in verification_results:
                        if result.get('actualResult') != result.get('desiredOutcome'):
                            mismatches.append({
                                'assertion': result.get('assertion', ''),
                                'trace': "<init>",  # Default trace
                                'current_result': result.get('actualResult', ''),
                                'desired_result': result.get('desiredOutcome', '')
                            })
                
                # Save initial verification results
                try:
                    # Save in the main model directory
                    with open(f"{model_dir}/verification_results_refine_0.json", 'w', encoding='utf-8') as f:
                        json.dump(verification_results, f, indent=2)
                    print(f"Saved initial verification results as round 0")
                except Exception as e:
                    print(f"Error saving initial verification results: {e}")
                
                # Refinement loop
                while refine_count < max_refine_attempts and not all_mismatches_fixed and mismatches:
                    refine_count += 1
                    print(f"\n=== Starting refinement round {refine_count}/{max_refine_attempts} ===\n")
                    
                    # Generate refined code
                    for i in range(3): # possible to give 3 chances if the generated code contains any syntax error.
                        if i > 0:
                            print(f"Syntax error in refined code, regenerating... (Regeneration attempt: {i})")
                        refined_code = gen_refine(current_structured_data, current_code, mismatches, refine_count)
                        
                        # Extract the longest code block from the refined response
                        longest_refined_block = _extract_longest_code_block(refined_code)
                        if longest_code_block == "":
                            continue
                        
                        # Save both versions for reference
                        try:
                            with open(f"{model_dir}/original_refined_{refine_count}.txt", 'w', encoding='utf-8') as f:
                                f.write(refined_code)
                            with open(f"{model_dir}/extracted_refined_{refine_count}.csp", 'w', encoding='utf-8') as f:
                                f.write(longest_refined_block)
                        except Exception as e:
                            print(f"Error saving original/extracted refined code: {e}")
                        
                        # Verify the refined code
                        print(f"Verifying refined code from round {refine_count}...")
                        refine_verification_results, refine_has_mismatch, refine_any_empty = verify_code(
                            current_structured_data, longest_refined_block, is_refine=True, refine_round=refine_count
                        )
                        
                        # Save this round's verification results in the main model directory
                        try:
                            # with open(f"{model_dir}/verification_results_refine_{refine_count}.json", 'w', encoding='utf-8') as f:
                            #     json.dump(refine_verification_results, f, indent=2)
                            print(f"Saved verification results for refinement round {refine_count}")
                        except Exception as e:
                            print(f"Error saving verification results for round {refine_count}: {e}")
                        
                        # Check for syntax errors (shouldn't happen but just in case)
                        if refine_any_empty:
                            continue
                        else:
                            # Update current code to refined code
                            current_code = longest_refined_block
                            break
                    
                    # Check if all mismatches are fixed
                    if not refine_has_mismatch:
                        all_mismatches_fixed = True
                        print(f"All mismatches fixed in refinement round {refine_count}!")
                        
                        # Save the successful code as verifiedCode.csp in the main model directory
                        verified_code_path = f"{model_dir}/verifiedCode.csp"
                        try:
                            with open(verified_code_path, 'w', encoding='utf-8') as f:
                                f.write(current_code)
                            print(f"Saved verified code to {verified_code_path}")
                        except Exception as e:
                            print(f"Error saving verified code: {e}")
                        try:
                            with open('./database-algorithm.json', 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        except:
                            data = []
                        data.append({"model_name": model_name, "verified_code": current_code})
                        with open('./database-algorithm.json', 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"Saved verified code for {model_name} model to database-algorithm.json")

                        break
                    else:
                        # Update mismatches for next round from the current round's directory
                        refine_dir = f"{model_dir}/refine_round_{refine_count}"
                        mismatch_file = f"{refine_dir}/mismatch_traces.json"
                        try:
                            with open(mismatch_file, 'r', encoding='utf-8') as f:
                                mismatches = json.load(f)
                        except (FileNotFoundError, json.JSONDecodeError) as e:
                            print(f"Error reading mismatch traces from round {refine_count}: {e}")
                            # Fallback to generating mismatches from verification results
                            mismatches = []
                            for result in refine_verification_results:
                                if result.get('actualResult') != result.get('desiredOutcome'):
                                    # Extract trace information
                                    lines = result.get('patResult', '').split("\n")
                                    trace = "<init>"  # Default if no specific trace found
                                    for line in lines:
                                        if "->" in line and line.strip().startswith("<"):
                                            trace = line.strip()
                                            break
                                    
                                    mismatches.append({
                                        'assertion': result.get('assertion', ''),
                                        'trace': trace,
                                        'current_result': result.get('actualResult', ''),
                                        'desired_result': result.get('desiredOutcome', '')
                                    })
                
                # After refinement loop
                if all_mismatches_fixed:
                    print(f"Refinement successful after {refine_count} rounds!")
                else:
                    print(f"Reached maximum refinement attempts ({max_refine_attempts}) without fixing all issues.")
                    
                    # Save the final refined code anyway
                    final_code_path = f"{model_dir}/final_refined_code.csp"
                    try:
                        with open(final_code_path, 'w', encoding='utf-8') as f:
                            f.write(current_code)
                        print(f"Saved final refined code to {final_code_path}")
                    except Exception as e:
                        print(f"Error saving final refined code: {e}")
                    
                    # Save a summary of the refinement process
                    summary_path = f"{model_dir}/refinement_summary.json"
                    try:
                        with open(summary_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                "rounds": refine_count,
                                "all_fixed": all_mismatches_fixed,
                                "remaining_mismatches": len(mismatches),
                                "completion_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }, f, indent=2)
                    except Exception as e:
                        print(f"Error saving refinement summary: {e}")
            
            print(f"Finished processing entry {i}.")
            
            
            




