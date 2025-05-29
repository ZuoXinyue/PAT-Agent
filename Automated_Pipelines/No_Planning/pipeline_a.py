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

def _process_assertions(assertions):
    nl_annotations_assertion = []
    
    for i in range(len(assertions)):
        assertion_item = assertions[i]
        component_name = assertion_item.get("component")
        sys_or_process = f'subsystem {component_name}' if component_name else f'system'
        assertion_type = assertion_item.get("assertionType", "").strip().lower()

        if assertion_type == "deadlock-free":
            nl_annotations_assertion.append(f"Assertion {i}: assert that the system is deadlockfree")
        
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

            nl_annotations_assertion.append(f"Assertion {i}:")
            nl_annotations_assertion.append(f" define {stateName if stateName else '{stateName}'}: {cond_str}")
            nl_annotations_assertion.append(f" assert that the {sys_or_process} can reach the state \"{stateName}\"")
        
        elif assertion_type == "ltl":
            ltl_target = assertion_item.get("ltlTarget", "").strip().lower()
            ltl_logic = assertion_item.get("ltlLogic", "").strip().replace("_", " ")

            if ltl_target == 'customize':
                custom_desc = assertion_item.get("customDescription","")
                nl_annotations_assertion.append(f"Assertion {i}: ")
                nl_annotations_assertion.append(f"// {custom_desc}")
            elif ltl_target == "action":
                selectedActions = assertion_item.get("selectedActions", [])
                selectedActions_str = ", ".join(map(str, selectedActions)) if isinstance(selectedActions, list) else str(selectedActions).strip()
                nl_annotations_assertion.append(f"Assertion {i}: ")
                nl_annotations_assertion.append(f'assert that the {sys_or_process} will {ltl_logic} perform those actions "{selectedActions_str}"')
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
                nl_annotations_assertion.append(f"Assertion {i}: ")
                nl_annotations_assertion.append(f"define {stateName if stateName else '{stateName}'}: {cond_str}")
                nl_annotations_assertion.append(f"assert that the {sys_or_process} will {ltl_logic} reach the state \"{stateName}\"")
                
    return "\n".join(nl_annotations_assertion)

def _generate_descriptions_helper(structured_data):
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

    desc += f" The processes interact with each other through the following way: {structured_data.get('interactionMode', '')}. "

    desc += " Please analyze the constants and variables in the system. Subsequently, analyze the actions in the system, focusing on the guarded conditions and the state changes associated with each action. With the analyzed information, please generate the PAT code according to the system description. "

    assertions = structured_data.get('assertions', [])
    assertion_instructions = _process_assertions(assertions)
    desc += f" Finally, please generate exactly the following assertions in order, without any modification: {assertion_instructions}"
    
    return desc

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
    system_description_for_prompt = _generate_descriptions_helper(structured_data)
    # print(f"System description for prompt: {system_description_for_prompt[:200]}...")

    # 4. Construct Final Prompt for Claude
    # Based on codegen.html prompt structure
    final_code_gen_prompt = f"""You are an expert in PAT (Process Analysis Toolkit), and you already possess a strong understanding of PAT concepts as outlined in the documentation. As a reminder, here are a few key guidelines:
--- Quick Reference ---
General Information: {syntax_general_info}

Pitfalls and Syntax Guidelines: {syntax_pitfalls_rules}

Your task is to generate the PAT code given the system description.
### Example PAT Code Output:
**Detailed Description:** {retrieved_nl}
**Expected Output:** {retrieved_code}

Given the general system description: {system_description_for_prompt}, now generate the PAT code.

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
    root_path = "path_to_your_root_directory"  # Adjust this to your actual root path
    
    if is_refine:
        # If we're refining, create a specific subdirectory for this round
        folder_path = f"{root_path}/Automated_Pipelines/No_Planning/generated_code/{model_name}/refine_round_{refine_round}"
    else:
        # Initial verification uses the main model directory
        folder_path = f"{root_path}/Automated_Pipelines/No_Planning/generated_code/{model_name}"
    
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
    root_path = "path_to_your_root_directory"  # Adjust this to your actual root path
    folder_path = f"{root_path}/Automated_Pipelines/No_Planning/generated_code/{model_name}"
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
    with open('./PAT.json', 'r') as file:
        structured_data_list = json.load(file)
        assert len(structured_data_list) == 8, "The number of entries in the JSON file should be 8."
        for i in range(len(structured_data_list)): # Iterate through all entries in the JSON
            current_structured_data = structured_data_list[i]
            print(f"Processing data entry {i} with model name: {current_structured_data.get('modelName', 'N/A')}")
            
            # No Planning LLM
            print(f"formulating prompt for entry {i}")
            full_nl_prompt = _generate_descriptions_helper(current_structured_data)
            
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
                gen_code(current_structured_data, full_nl_prompt)
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
                root_path = "path_to_your_root_directory"  # Adjust this to your actual root path
                folder_path = f"{root_path}/Automated_Pipelines/No_Planning/generated_code/{model_name}"
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
                root_path = "path_to_your_root_directory"  # Adjust this to your actual root path
                model_dir = f"{root_path}/Automated_Pipelines/No_Planning/generated_code/{model_name}"
                
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
            
            
            




