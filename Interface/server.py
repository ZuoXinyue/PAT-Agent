from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import subprocess
import json
import datetime
import io
import os
import sys
from openai import OpenAI
import anthropic
from rules_classical_algos import process_classical_algos
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

openai_key = os.environ["OPENAI_API_KEY"]
claude_key = os.environ["CLAUDE_API_KEY"]

client = OpenAI(
    api_key=openai_key,
)

client_claude = anthropic.Anthropic(api_key=claude_key)

app = Flask(__name__, static_folder='./templates', static_url_path='')
cors = CORS(app, supports_credentials=True)

# File paths
msg_history_path = './history/history.json'
const_history_path = './history/const-history.json'
action_history_path = './history/action-history.json'

@app.route("/get_planning_model_answers", methods=["POST"])
def get_planning_model_answers():
    data = request.get_json()
    question = data.get('question')
    context = data.get('context')
    history = data.get('history')

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
                'PAT': ""  # Empty PAT response as specified
            }
            history = history.strip()  # 去除空格和换行符

            if history == 'skip':
                return jsonify({
                    'status': 'success',
                    'data': interaction
                })

            if history == 'const':
                msg_history_path = './history/const-history.json'
            elif history == 'action':
                msg_history_path = './history/action-history.json'
            elif history == 'assertion':
                msg_history_path = './history/assertion-history.json'            
            else:
                msg_history_path = './history/history.json'
            
            
            # print("saving...",msg_history_path)
            # Save to history
            try:
                with open(msg_history_path, 'r') as file:
                    history = json.load(file)
            except FileNotFoundError:
                history = []

            history.append(interaction)

            with open(msg_history_path, 'w') as file:
                json.dump(history, file, indent=4)
            
            return jsonify({
                'status': 'success',
                'data': interaction
            })
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'No question provided'}), 400

@app.route("/get_chatbot_model_answers", methods=["POST"])
def get_chatbot_model_answers():
    data = request.get_json()
    question = data.get('question')
    context = data.get('context')
    history = data.get('history')
    print("question",question)

    if question:
        try:
            # Get model response: using o3-mini instead of o3-mini-high
            completion = client.chat.completions.create(
                model="o3-mini-2025-01-31",
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
                'PAT': ""  # Empty PAT response as specified
            }
            

            history = history.strip()  # 去除空格和换行符

            if history == 'skip':
                return jsonify({
                    'status': 'success',
                    'data': interaction
                })

            if history == 'const':
                msg_history_path = './history/const-history.json'
            elif history == 'action':
                msg_history_path = './history/action-history.json'
            elif history == 'assertion':
                msg_history_path = './history/assertion-history.json'
            elif history == 'chatbot':
                msg_history_path = './history/chatbot-history.json'            
            else:
                msg_history_path = './history/history.json'
            

            # Save to history
            try:
                with open(msg_history_path, 'r') as file:
                    history = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                history = []

            history.append(interaction)

            with open(msg_history_path, 'w') as file:
                json.dump(history, file, indent=4)
            
            return jsonify({
                'status': 'success',
                'data': interaction
            })
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'No question provided'}), 400

@app.route("/get_prev_code_model_answers_claude", methods=["GET"])
def get_prev_code_model_answers_claude():
    filename = './history/claude-code.json'
    with open(filename, 'r') as file:
        history_data = json.load(file)
    
    return jsonify({
                'status': 'success',
                'data': history_data[len(history_data)-1]
            })
    
@app.route("/get_code_model_answers_claude", methods=["POST"])
def get_code_model_answers_claude():
    data = request.get_json()
    question = data.get('question')
    context = data.get('context')
    history = data.get('history')
    print("Question: ", question)


    if question:
        try:
            # Get model response from Claude
            response = client_claude.messages.create(
                model="claude-3-7-sonnet-20250219",  # or update to a newer version if available
                max_tokens = 8192,
                messages=[
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )
            answer = response.content[0].text

            # Create interaction record
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        

            interaction = {
                'timestamp': formatted_time,
                'question': question,
                'answerClaude': answer,  # Labeling the answer for Claude
                'PAT': ""  # Empty PAT response as specified
            }

            print(answer)

      
            history = history.strip()  # Remove any whitespace or newline characters
            if history != './history/claude-code.json':
                print("An error in the saving path")
            
     
            # Read existing history data, or create new list if file not found
            try:
                with open(history, 'r') as file:
                    history_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                history_data = []

            history_data.append(interaction)

            with open(history, 'w') as file:
                json.dump(history_data, file, indent=4)
            
            return jsonify({
                'status': 'success',
                'data': interaction
            })
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'No question provided'}), 400

@app.route("/save_assertion_history", methods=["POST"])
def save_assertion_history():
    data = request.get_json()

    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    try:
        timestamp = data.get('timestamp')
        question = data.get('question')
        answer = data.get('answerGPT')  # this is already a dict from frontend
        pat = data.get('PAT', '')

        interaction = {
            'timestamp': timestamp,
            'question': question,
            'answerGPT': answer,  # DON'T stringify this
            'PAT': pat
        }

        path = './history/assertion-history.json'

        try:
            with open(path, 'r') as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []

        history.append(interaction)

        with open(path, 'w') as f:
            json.dump(history, f, indent=2)  # json.dump will handle answerGPT correctly

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def GPT4_output(input, context=None):
    pre_ = 'Please generate the csp file containing corresponding PAT code for this questions.'
    post_ = 'Please generate ONLY executable CSP code and nothing else.'
    
    # Create messages list with system context if available
    messages = []
    if context:
        context_prompt = "System Context:\n" + "\n".join([f"{k}: {v}" for k, v in context.items()])
        messages.append({
            "role": "system",
            "content": context_prompt
        })
    
    # Add example Q&A
    messages.extend([
        {
            "role": "user",
            "content": pre_ + "This system models a concurrent version of the classic Dining Philosophers problem for two philosophers (N=2) using Communicating Sequential Processes (CSP). Each philosopher alternates between thinking and eating and requires two forks to eat."
        },
        {
            "role": "assistant",
            "content": '''
#define N 2;
    Phil(i) = [i % 2 == 0] (get.i.(i+1)%N -> get.i.i -> eat.i -> put.i.(i+1)%N -> put.i.i -> Phil(i)) []
              [i % 2 != 0] (get.i.i -> get.i.(i+1)%N -> eat.i -> put.i.i -> put.i.(i+1)%N -> Phil(i));

    Fork(x) = get.x.x -> put.x.x -> Fork(x) 
             [] get.(x-1)%N.x -> put.(x-1)%N.x -> Fork(x);

    College() = ||x:{0..N-1}@(Phil(x)||Fork(x));

    Implementation() = College() \ {get.0.0,get.0.1,put.0.0,put.0.1,eat.1,get.1.1,get.1.0,put.1.1,put.1.0};

    Specification() = eat.0 -> Specification();

    ////////////////The Properties//////////////////
    #assert College() deadlockfree;
'''
        },
        {
            "role": "user",
            "content": pre_ + input + post_
        }
    ])

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    return completion.choices[0].message.content

def our_output(input):
    filename = "test.csp"
    
    with open(filename, "w") as file:
        if isinstance(input, list):
            file.write("\n".join(input))
        else:
            file.write(input)
            
    command = [
        "mono",
        "~/PAT-Agent/PAT.Console/Process-Analysis-Toolkit/PAT3.Console.exe",
        "-csp",
        "~/PAT-Agent/LLM-chatbot/test.csp",
        "~/PAT-Agent/LLM-chatbot/output.txt"
    ]

    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    print("Standard Output:", result.stdout)
    
    with open("./output.txt") as file:
        output = file.read()
    
    return output

@app.route("/get_answers", methods=["POST"])
def get_answers():
    data = request.get_json()
    question = data.get('question')
    context = data.get('context')

    if question:
        # Get GPT response with context
        answerGPT = GPT4_output(question, context)
        PAT = our_output(answerGPT)
        
        # Create interaction record
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        interaction = {
            'timestamp': formatted_time,
            'question': question,
            'answerGPT': answerGPT,
            'PAT': PAT
        }
        
        # Save to history
        try:
            with open(msg_history_path, 'r') as file:
                history = json.load(file)
        except FileNotFoundError:
            history = []

        history.append(interaction)

        with open(msg_history_path, 'w') as file:
            json.dump(history, file, indent=4)
        
        return jsonify(history)
    
    return jsonify({'error': 'No question provided'}), 400

@app.route("/get_history", methods=["GET"])
def load_history():
    try:
        with open(msg_history_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("File not found. Returning an empty list.")
        return []
    
@app.route("/get_const_history", methods=["GET"])
def load_const_history():
    msg_history_path = './history/const-history.json'
    try:
        with open(msg_history_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("File not found. Returning an empty list.")
        return []

@app.route("/get_action_history", methods=["GET"])
def load_action_history():
    msg_history_path = './history/action-history.json'
    try:
        with open(msg_history_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("File not found. Returning an empty list.")
        return []   
    
@app.route("/get_assertion_history", methods=["GET"])
def get_assertion_history():
    try:
        with open('./history/assertion-history.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.route("/get_last_nl_instruction_claude", methods=["GET"])
def get_last_nl_instruction_claude():
    filename = "./history/nl-instruction-claude.json"
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return jsonify(data)

@app.route("/save_nl_instruction_parts", methods=["POST"])
def save_nl_parts():
    """
    Each code generation run produces data1, data2, data3.
    We store them as one grouped entry in nl-instruction-part.json.
    """
    data = request.get_json()
    data1 = data.get("data1", "")
    data2 = data.get("data2", "")
    data3 = data.get("data3", "")

    # Create the new entry as a dictionary
    new_entry = {
        "data1": data1,
        "data2": data2,
        "data3": data3
    }

    # Read existing JSON array (or start a new one if file not found/empty)
    filename = "./history/nl-instruction-part.json"
    try:
        with open(filename, "r") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    # Append the new entry to the array
    existing_data.append(new_entry)

    # Write back the updated array
    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=2)

    return jsonify({"status": "success"})

@app.route("/save_nl_instruction_claude", methods=["POST"])
def save_nl_claude():
    """
    Save each final combined text (data1+data2+data3) as a new entry in
    nl-instruction-claude.json. So the file is an array of objects,
    each with a "fullText" key.
    """
    data = request.get_json()
    full_text = data.get("fullText", "")
    filename = "./history/nl-instruction-claude.json"

    # 1. Read existing file or create a new list if file doesn't exist or is invalid
    try:
        with open(filename, "r") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    # 2. Build the new entry
    new_entry = {
        "fullText": full_text
    }

    # 3. Append it to the existing array
    existing_data.append(new_entry)

    # 4. Write the updated array back
    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=2)

    return jsonify({"status": "success"})

@app.route("/verify_pat_code", methods=['POST'])
def verify_pat_code():
    data = request.get_json()
    code = data.get("code", "")
    # print("code", code)
    try:
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        # You may adjust the question as desired. Here, we use a static prompt.
        new_record = {
            "timestamp": formatted_time,
            "question": "You are an expert in PAT (Process Analysis Toolkit). Please refine the PAT code.", 
            "answerClaude": code,   # the (possibly edited) PAT code
            "PAT": ""
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
        # Optionally, you can continue even if saving fails.
        
    code_blocks = split_code_and_assertions(code)

    modelName = data.get("model_name", "")
    root_path = "path_to_your_root_directory"  # Adjust this path as needed
    
    # Remove any existing files in the model's folder (both .csp and .txt)
    folder_path = f"{root_path}/PAT.Console/Process-Analysis-Toolkit/PATfiles/{modelName}"
    if os.path.exists(folder_path):
        # Remove all files in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception as remove_err:
                    print(f"Error removing file {file_path}: {remove_err}")
    else:
        os.makedirs(folder_path, exist_ok=True)

    anyEmpty = False
    for i in range(len(code_blocks)):
        input_file = f"{folder_path}/{i}.csp"
        output_file = f"{folder_path}/pat_output_{i}.txt"
        # 保存 code 到 .csp 文件
        try:
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(code_blocks[i])
        except Exception as e:
            print("error happened during saving codes")
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
        
        if ('reaches' in code_blocks[i]) or ('deadlockfree' in code_blocks[i]):
            command = [ "mono", f"{root_path}/PAT.Console/Process-Analysis-Toolkit/PAT3.Console.exe",
              "-csp", "-engine", "1", input_file, output_file]
        else:
            command = [ "mono", f"{root_path}/PAT.Console/Process-Analysis-Toolkit/PAT3.Console.exe",
              "-csp", input_file, output_file]
        try:
            subprocess.run(command, check=True, timeout=300)
            with open(output_file, 'r', encoding='utf-8') as f:
                output = f.read()
            if output == "":
                anyEmpty = True
        except subprocess.TimeoutExpired:
            print(f"PAT execution timed out for assertion {i}")
            # If execution exceeds 5 minutes, return immediately for this loop
            return jsonify({'output': "", 'anyEmpty': True})
        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'PAT execution failed: {str(e)}'}), 500
        except FileNotFoundError:
            return jsonify({'error': 'Output file not found'}), 500
        

    # # 保存 code 到 .csp 文件
    # try:
    #     with open(input_file, 'w', encoding='utf-8') as f:
    #         f.write(code)
    # except Exception as e:
    #     return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    # # 构造 PAT 命令
    # command = [
    #     "mono",
    #     f"{root_path}/PAT.Console/Process-Analysis-Toolkit/PAT3.Console.exe",
    #     "-csp", input_file, output_file
    # ]
    # # 运行命令并获取输出
    


    return jsonify({'output': output, 'anyEmpty': anyEmpty})

import re

@app.route("/verify_classical_code", methods=['POST'])
def verify_classical_code():
    data = request.get_json()
    code = data.get("code", "")
    model_name = data.get("model_name", "")
    try:
        # Process the code to generate the assertions and verify using PAT
        code_blocks = split_code_and_assertions(code)
        verification_results = []
        root_path = "path_to_your_root_directory"  # Adjust this path as needed
        folder_path = f"{root_path}/PAT.Console/Process-Analysis-Toolkit/PATfiles/{model_name}"

        if os.path.exists(folder_path):
            # Remove all files in the folder
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as remove_err:
                        print(f"Error removing file {file_path}: {remove_err}")
        else:
            os.makedirs(folder_path, exist_ok=True)

        def generate():
            for i in range(len(code_blocks)):
                input_file = f"{folder_path}/{i}.csp"
                output_file = f"{folder_path}/pat_output_{i}.txt"

                try:
                    with open(input_file, 'w', encoding='utf-8') as f:
                        f.write(code_blocks[i])
                except Exception as e:
                    yield json.dumps({'error': f'Failed to save file: {str(e)}'}) + '\n'
                    return

                command = [
                    "mono", f"{root_path}/PAT.Console/Process-Analysis-Toolkit/PAT3.Console.exe", "-csp", input_file, output_file
                ]
                try:
                    subprocess.run(command, check=True, timeout=300)
                    with open(output_file, 'r', encoding='utf-8') as f:
                        output = f.read()
                    
                    # process pat output
                    start_marker = "********Verification Result********"
                    end_marker = "********Verification Setting********"
                    start_idx = output.find(start_marker)
                    end_idx = output.find(end_marker)
                    if start_idx != -1 and end_idx != -1:
                        pat_result = output[start_idx + len(start_marker):end_idx].strip()

                    # Extracting the actual outcome from the output
                    match = re.search(r"is\s+(\w+)", pat_result, re.IGNORECASE)
                    actual_outcome = ""
                    if match and match.group(1):
                        word = match.group(1).upper()
                        if word == "VALID":
                            actual_outcome = "Valid"
                        else:
                            actual_outcome = "Invalid"

                    # Extract the assertion line from the code block
                    assertion_line = ""
                    for line in code_blocks[i].splitlines():
                        if line.strip().startswith("#assert"):
                            assertion_line = line.strip()
                            break

                    result = {
                        'index': i,
                        'assertion': assertion_line,
                        'patResult': pat_result,
                        'actualResult': actual_outcome
                    }
                    yield json.dumps(result) + '\n'

                except subprocess.TimeoutExpired:
                    print(f"PAT execution timed out for assertion {i}")
                    yield json.dumps({'status': 'timeout', 'index': i}) + '\n'
                    return
                except subprocess.CalledProcessError as e:
                    yield json.dumps({'error': f'PAT execution failed: {str(e)}'}) + '\n'
                    return
                except FileNotFoundError:
                    yield json.dumps({'error': 'Output file not found'}) + '\n'
                    return

        return app.response_class(generate(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/get_most_relevant_example", methods=["POST"])
def get_most_relevant_example():
    try:
        data = request.get_json()
        instruction = data["instruction"]

        with open('./database-rag-claude.json', 'r') as f:
            database = json.load(f)
        
        nls = [entry["nl"] for entry in database if entry.get("nl")]
        if not nls:
            return jsonify({'error': 'No valid NL entries in database'}), 500
        
        
        vectorizer = TfidfVectorizer().fit(nls + [instruction])
        vectors = vectorizer.transform(nls + [instruction])
        
         # 计算 instruction 与每个 nl 的余弦相似度
        similarity_scores = cosine_similarity(vectors[-1], vectors[:-1])[0]
        most_similar_idx = similarity_scores.argmax()

        # 返回最相似的一条 nl 和 code
        matched_entry = database[most_similar_idx]
        return jsonify({
            'nl': matched_entry["nl"],
            'code': matched_entry["code"]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


def split_code_and_assertions(code):
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

@app.route("/save_run_time", methods=["POST"])
def save_run_time():
    data = request.get_json()
    model_name = data.get("modelName", "")
    stage = data.get("stage", "")
    run_time = data.get("runTime", "")
    hasMismatch = data.get("hasMismatch", None)  # <-- default to None

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

    # Update the dictionary
    run_time_data[stage] = save_content

    # Save back to file
    with open(run_time_record_path, 'w') as file:
        json.dump(run_time_data, file, indent=4)

    return {"message": "Run time saved successfully."}


@app.route("/process_assertions", methods=["POST"])
def process_assertions():
    try:
        data = request.get_json()
        # print("data:", data)

        response = load_const_history()
        # print("response:", response)
        # print("response type:", type(response))
        history = response
        # print("history:", history)
        if history and len(history) > 0:
            latestEntry = history[-1]
            ctx = latestEntry["context"]               # grab the nested dict
            modelName    = ctx["modelName"]            # dict indexing
        else:
            raise ValueError("Please start from index.html page.")

        nl_annotations_assertion = [""] # to create a line separation from the subsystem definitions

        # Step 1: Process interactionMode
        interaction_mode = data.get("interactionMode", "").strip().lower()
        # print("interaction mode: ", interaction_mode)
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
            pass
        else: # customized interaction
            assertion_part_1 = f'// define the {modelName} system following the description: {interaction_mode}'
            nl_annotations_assertion.append(assertion_part_1)
        # print("firstline:", nl_annotations_assertion)

        # Step 2: Create list to store NL annotation for each assertion.

        # Process each assertion from the "assertions" field.
        nl_annotations_assertion.append("// define **exactly** the following states and assertions as specified. Do **NOT** add, modify, or omit anything")  # explicitly state that the following assertions should be specified
        assertions_list = data.get("assertions", [])
        for a in assertions_list:
            if a.get("component"):
                sys_or_process = f'''subsystem {a.get("component")}'''
            else:
                sys_or_process = f'''{modelName} system'''
            assertion_type = a.get("assertionType", "").strip().lower()

            if assertion_type == "deadlock-free":
                nl_annotations_assertion.append(f"// assert {sys_or_process} deadlockfree")

            elif assertion_type == "reachability":
                stateName = a.get("stateName", "").strip()
                # Create a description line by iterating over conditions.
                conditions = a.get("conditions", [])
                
                reachabilityType = a.get("reachabilityType", "").strip().lower()
                if reachabilityType == "customize":
                    cond_str = a.get("customDescription","")
                else:
                    cond_parts = []
                    # print("12333",conditions)
                    for i,cond in enumerate(conditions):
                        variable = cond.get("variable", "").strip()
                        value = cond.get("value", "").strip()
                        
                        if variable and value:
                            expr = f"{variable} = {value}"
                            if i > 0:
                                connector = cond.get("connector", "").strip().lower()
                                cond_parts.append(f"{connector} {expr}")
                            else:
                                cond_parts.append(expr)
                    cond_str = " ".join(cond_parts) if cond_parts else "no conditions provided"

                        # cond_parts.append(f"{variable} = {value}")
                # cond_str = " and ".join(cond_parts) if cond_parts else "no conditions provided"
                
                print("cond_str",cond_str)
                # First, a definition line:
                nl_annotations_assertion.append(f"// define {stateName if stateName else '{stateName}'}: {cond_str}")
                # Then, an assertion line:
                nl_annotations_assertion.append(f"// assert that the {sys_or_process} can reach the state \"{stateName}\"")

            elif assertion_type == "ltl":
                ltl_target = a.get("ltlTarget", "").strip().lower()
               
                ltl_logic = a.get("ltlLogic", "").strip()
                # Process ltlLogic: if "_" exists, replace with space.
                if "_" in ltl_logic:
                    ltl_logic_processed = ltl_logic.replace("_", " ")
                else:
                    ltl_logic_processed = ltl_logic
                if ltl_target == 'customize':
                    cond_str = a.get("customDescription","")
                    # nl_annotations_assertion.append(f"// define {stateName if stateName else '{stateName}'}: {cond_str}")
                    nl_annotations_assertion.append(f"// {cond_str}")
                elif ltl_target == "action":
                    selectedActions = a.get("selectedActions", [])
                    # Ensure selectedActions is a list, then join into a string
                    if isinstance(selectedActions, list):
                        selectedActions_str = ", ".join(map(str, selectedActions))
                    else:
                        selectedActions_str = str(selectedActions).strip()
                    nl_annotations_assertion.append(
                        f'// assert that the {sys_or_process} will {ltl_logic_processed} perform those actions "{selectedActions_str}"'
                    )
                    print("nl_annotations_assertion", nl_annotations_assertion)
                elif ltl_target == "state":
                    stateName = a.get("stateName", "").strip()
                    # Create a definition line from conditions.
                    conditions = a.get("conditions", [])
                    cond_parts = []
                    for cond in conditions:
                        variable = cond.get("variable", "").strip()
                        value = cond.get("value", "").strip()
                        if variable and value:
                            cond_parts.append(f"{variable} = {value}")
                    cond_str = " and ".join(cond_parts) if cond_parts else "no conditions provided"
                    nl_annotations_assertion.append(f"// define {stateName if stateName else '{stateName}'}: {cond_str}")
                    nl_annotations_assertion.append(f"// assert that the {sys_or_process} will {ltl_logic_processed} reach the state \"{stateName}\"")
        
        # Combine all lines into one output string.
        # print("rule-based processing completed")
        final_output = "\n".join(nl_annotations_assertion)
        # print("final_output", final_output)
        return jsonify({'output': final_output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route("/get_verification_data", methods=["GET"])
def get_verification_data():
    try:
        # Get the model name from query parameters (e.g., Testing)
        model_name = request.args.get("model_name", "").strip()
        if not model_name:
            return jsonify({"error": "No model_name provided"}), 400
        
        # Define the root and base directory for the PAT files.
        root_path = "path_to_your_root_directory"  # Adjust this path as needed
        base_dir = os.path.join(root_path, "PAT.Console", "Process-Analysis-Toolkit", "PATfiles", model_name)
        
        # List all .csp files in the base directory.
        csp_files = [f for f in os.listdir(base_dir) if f.endswith(".csp")]
        # Assume file names are numeric (e.g., "0.csp", "1.csp", etc.) and sort them.
        csp_files.sort(key=lambda x: int(os.path.splitext(x)[0]))
        
        # Try to load the desired outcomes from assertion-history.json.
        desired_assertions = []
        try:
            with open("./history/assertion-history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
            # Assume history is an array; take the last entry.
            last_entry = history[-1]
            # The answerGPT is assumed to be a JSON string containing a key "assertions"
            answer_gpt_dict = last_entry.get("answerGPT", {})
            desired_assertions = answer_gpt_dict.get("assertions", [])
        except Exception as e:
            # If something goes wrong, default to an empty list.
            print("Error loading assertion-history.json:", e)
            desired_assertions = []
        
        verification_groups = []
        
        for i, csp_filename in enumerate(csp_files):
            csp_path = os.path.join(base_dir, csp_filename)
            # Corresponding txt file: assuming naming pattern "pat_output_{i}.txt"
            base_name = os.path.splitext(csp_filename)[0]  # e.g., "0"
            txt_filename = f"pat_output_{base_name}.txt"
            txt_path = os.path.join(base_dir, txt_filename)
            
            # 1. Extract the assertion from the .csp file.
            with open(csp_path, "r", encoding="utf-8") as f:
                csp_content = f.read()
            assertion_line = ""
            for line in csp_content.splitlines():
                if line.strip().startswith("#assert"):
                    assertion_line = line.strip()
                    break
            
            # 2. Extract the PAT verification result from the .txt file.
            pat_result = ""
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    txt_content = f.read()
                start_marker = "********Verification Result********"
                end_marker = "********Verification Setting********"
                start_idx = txt_content.find(start_marker)
                end_idx = txt_content.find(end_marker)
                if start_idx != -1 and end_idx != -1:
                    pat_result = txt_content[start_idx + len(start_marker):end_idx].strip()
            
            # 3. Compute the actual outcome from the PAT result.
            actual_outcome = ""
            match = re.search(r"is\s+(\w+)", pat_result, re.IGNORECASE)
            if match and match.group(1):
                word = match.group(1).upper()
                if word == "VALID":
                    actual_outcome = "Valid"
                else:
                    actual_outcome = "Invalid"
            
            # 4. Retrieve the desired outcome from the desired assertions.
            desired_outcome = "Valid"
            # print("length of desired_assertions: ", len(desired_assertions))
            if i < len(desired_assertions):
                outcome = desired_assertions[i].get("assertionTruth", "").strip()
                # print(i, outcome)
                desired_outcome = outcome if outcome else "Valid"
            
            verification_groups.append({
                "assertion": assertion_line,
                "patResult": pat_result,
                "desiredOutcome": desired_outcome,
                "actualResult": actual_outcome
            })
        
        return jsonify(verification_groups)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/get_last_claude_refinement", methods=["GET"])
def get_last_claude_refinement():
    filename = "./history/claude-refinement.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            refinement_data = json.load(f)
        if not refinement_data:
            return jsonify({"error": "No refinement data available"}), 404
        last_entry = refinement_data[-1]
        # Return the code from the last record
        return jsonify({"data": {"answerClaude": last_entry.get("answerClaude", "")}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_syntax_data", methods=["GET"])
def get_syntax_data():
    filename = "syntax-dataset.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/save_verified_code", methods=["POST"])
def save_verified_code():
    data = request.get_json()
    model_name = data.get("model_name", "").strip()
    code = data.get("code", "")
    
    if not model_name:
        return jsonify({"error": "Model name not provided"}), 400
    if not code:
        return jsonify({"error": "No code provided"}), 400

    root_path = "path_to_your_root_directory"  # Adjust this path as needed
    folder = os.path.join(root_path, "PAT.Console", "Process-Analysis-Toolkit", "PATfiles", model_name)
    # Ensure the target folder exists.
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, "verifiedCode.csp")
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        return jsonify({"path": file_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/save_mismatch_traces", methods=["POST"])
def save_mismatch_traces():
    """
    Expects a JSON payload with a key "mismatches", an array of objects.
    Each object should have:
      - "assertion": The assertion text (from the .csp file)
      - "trace": The mismatch trace (from the PAT output)
      - "current_result": The current verification result
      - "desired_result": The desired verification result specified by users
    Saves these into mismatch_traces.json.
    """
    data = request.get_json()
    mismatches = data.get("mismatches", [])
    filename = "./history/mismatch_traces.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(mismatches, f, indent=2)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/get_mismatch_traces", methods=["GET"])
def get_mismatch_traces():
    filename = "./history/mismatch_traces.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            mismatches = json.load(f)
        return jsonify({"data": mismatches})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/process_traces", methods=["POST"])
def process_traces():
    """
    Placeholder endpoint to process mismatch traces information.
    Expects a JSON payload with a key "traces" containing an array of objects,
    each with keys: assertion, trace, current_result, desired_result.
    Returns a processed string that augments the prompt.
    """
    try:
        data = request.get_json()
        traces = data.get("traces", [])
        processed_messages = []
        # For example, we simply join each trace in a formatted way.
        for refinement_point in traces:
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
                # print(other_actions)  # Outputs (for example): init, approach_car, enter_car, take_key, exit_car, start_engine
                message = (
                    f"The generated code does not satisfy the following property: {assertion}, its current verification result is {current_result}, "
                    f"which is the opposite to the expected result of the desired system ({desired_result}). Through analyzing your current implementation, "
                    f"we identify that this assertion is violated after performing the {last_action} action. Therefore, please carefully analyze if the guarded condition "
                    f"of performing the {last_action} action is weaker than it should be, possibly missing out some requirements for the action to be valid. "
                    f"If, after careful analysis, you think the problem is not with the {last_action} action, then carefully analyze these actions as well: {other_actions}. "
                    f"Please make sure that the conditions of those actions happening are strict enough to not lead to the assertion {assertion} being {current_result}."
                )
            processed_messages.append(message)
        
        processed = "\n".join(processed_messages)
        return jsonify({"processed_traces": processed})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_classical_algorithms", methods=["GET"])
def get_classical_algorithms():
    filename = "database-algorithm.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get_classical_algorithm_details", methods=["GET"])
def get_classical_algorithm_details():
    algorithm_id = request.args.get("algorithm", "").strip()
    filename = "database-algorithm.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            algorithms = json.load(f)
        for algo in algorithms:
            if algo.get("id") == algorithm_id:
                return jsonify({"status": "success", "data": algo})
        return jsonify({"status": "error", "message": "Algorithm not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/process_algos", methods=["POST"])
def process_algos():
    data = request.get_json()
    algo_id = data.get("id", "")
    var_value = data.get("value", "")
    processed_code = process_classical_algos(algo_id, var_value)
    
    return jsonify({"status": "success", "processed_code": processed_code})

@app.route("/add_new_classical_algorithm", methods=["POST"])
def add_new_classical_algorithm():
    """
    This endpoint demonstrates the 'self-evolving' logic:
    1) We get the final code from the request.
    2) We ask Claude to generate a textual description.
    3) We ask GPT-o3 to generate an ID and name from that description.
    4) We clean up the ID.
    5) We append a new entry to 'database-algorithm.json'.
    """
    data = request.get_json()
    code = data.get("code", "").strip()
    if not code:
        return jsonify({"status": "error", "message": "No code provided"}), 400
    
    try:
        # 1) Ask Claude for a description from the code
        description = get_description_from_claude(code)
        
        # 2) Ask GPT-o3 for an ID and name from the description
        new_id = get_id_from_gpt_o3(description)
        new_name = get_name_from_gpt_o3(description)
        
        # 3) Clean up the ID (remove spaces, punctuation, etc.)
        new_id = "".join(ch for ch in new_id if ch.isalnum() or ch == '_').lower()
        
        # 4) Append to database-algorithm.json
        new_entry = {
            "id": new_id,
            "name": new_name,
            "matchtype": "exact match",
            "description": description,
            "variable": "",
            "implementation": code
        }
        add_to_database_algorithm(new_entry)
        
        return jsonify({"status": "success", "newEntry": new_entry})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

def get_description_from_claude(code):
    prompt = f"As a PAT expert, given the following PAT code, please summarize it briefly in one paragraph. Please be succinct and focus on listing the different components that compose the system and the requirements. For requirements, just describe without assertion result as you have no information of the expected result of the verification. Remember, be brief, say in a pattern like 'This model simulates a xxx system composed of x interacting components: xxx. The system includes requirements on xxx.' **WITHOUT ADDITIONAL INFORMATION, do not describe how the components interact, etc.**:\n{code}"
    response = call_claude_model(prompt)
    return response.strip()

def get_id_from_gpt_o3(description):
    prompt = f"Based on this description, create an id for the model, note, the id **MUST FOLLOW THE FORMAT like 'car_owner_key_door_motor' to be a single connected string**, **DO NOT INCLUDE ANY WORDS OTHER THAN THE ID**\n{description}"
    response = call_gpt_o3_model(prompt)
    return response.strip()

def get_name_from_gpt_o3(description):
    prompt = f"Based on this description, create a name for the model, note, the name should be a few words describing the model, ideally capturing the number of components, **DO NOT INCLUDE ANY WORDS OTHER THAN THE NAME**:\n{description}"
    response = call_gpt_o3_model(prompt)
    return response.strip()

def add_to_database_algorithm(new_entry):
    """
    Append the new entry to database-algorithm.json
    """
    filename = "database-algorithm.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    
    data.append(new_entry)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def call_claude_model(prompt):
    response = client_claude.messages.create(
        model="claude-3-7-sonnet-20250219",  # or update to a newer version if available
        max_tokens = 1024,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.content[0].text

def call_gpt_o3_model(prompt):
    completion = client.chat.completions.create(
        model="o3-mini-2025-01-31",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return completion.choices[0].message.content

@app.route("/del_msg", methods=["POST"])
def delMsg():
    data = request.get_json()
    msg_history = load_history()
    index = data.get('index')

    if index is not None and 0 <= index < len(msg_history):
        del msg_history[index]
        with open(msg_history_path, 'w') as file:
            json.dump(msg_history, file)
        return jsonify(msg_history)
    else:
        return jsonify({"error": "Invalid index"}), 400

@app.route("/", methods=["GET"])
def chatbot():
    return send_from_directory(app.static_folder, 'chatbot.html')

@app.route("/pat-agent.html", methods=["GET"])
def pat_agent():
    return send_from_directory(app.static_folder, 'pat-agent.html')

@app.route("/index.html", methods=["GET"])
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/const-and-vars.html", methods=["GET"])
def const_and_vars():
    return send_from_directory(app.static_folder, 'const-and-vars.html')

@app.route("/customize.html", methods=["GET"])
def customize():
    return send_from_directory(app.static_folder, 'customize.html')

@app.route('/request.js')
def serve_js():
    return send_from_directory(app.static_folder, 'request.js')

@app.route("/save_modified_const", methods=["POST"])
def save_modified_const():
    try:
        # Get the current request data
        data = request.json
        modified_data = data.get('modified_data')
        
        # Format the data to match the expected structure
        formatted_data = {
            "processes": modified_data
        }
        
        # Load existing history
        history_file = './history/const-history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
            
        # Get the last entry from history
        if history:
            last_entry = history[-1].copy()  # Create a copy of the last entry
            # Update only the answerGPT part with the formatted data
            last_entry['answerGPT'] = json.dumps(formatted_data)
            last_entry['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Append the new entry to history
            history.append(last_entry)
            
            # Save back to file
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            return jsonify({"status": "success", "message": "Constants updated successfully"})
        else:
            return jsonify({"status": "error", "message": "No history found"}), 400
            
    except Exception as e:
        print("Error saving modified constants:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8085)
