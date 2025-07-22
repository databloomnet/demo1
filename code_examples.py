# code_examples.py




query_chatgpt_code = """
                client = openai.OpenAI(api_key=api_key)
                messages = [
                    {"role": "system", "content": constants.SYSTEM_CONTENT_FILTER},
                    {"role": "user", "content": user_prompt}
                ]
                completion = client.chat.completions.create(
                    model=constants.DEFAULT_OPENAI_MODEL,  
                    messages=messages
                )
                response = completion.choices[0].message.content
"""

converse_chatgpt_code = """
                if len(chat_history) == 0:                    
                    chat_history.append({"role": "system", "content": constants.SYSTEM_CONTENT_FILTER})
                chat_history.append( {"role": "user", "content": user_prompt} )

                client = openai.OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                    model=constants.DEFAULT_OPENAI_MODEL,
                    messages=chat_history,
                    response_format={"type": "text"}  
                )

                response = completion.choices[0].message.content
                chat_history.append({"role": "assistant", "content": response})

                user_prompt = "any other thoughts?"
"""

query_claude_code = """
                client = anthropic.Anthropic(api_key = api_key)
                completion = client.messages.create(
                    model=constants.DEFAULT_CLAUDE_MODEL,
                    max_tokens=200,
                    temperature=1,
                    system=constants.SYSTEM_CONTENT_FILTER,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_prompt
                                }
                            ]
                        }
                    ]
                )

                response = completion.content[0].text
"""


converse_claude_code = """
                chat_history.append( {"role": "user", "content": user_prompt} )

                client = anthropic.Anthropic(api_key = api_key)

                message = client.messages.create(
                    model=constants.DEFAULT_CLAUDE_MODEL,
                    max_tokens=200,
                    temperature=1,
                    system=constants.SYSTEM_CONTENT_FILTER,
                    messages= chat_history
                )

                completion = message
                response = message.content[0].text

                chat_history.append({"role": "assistant", "content": response})

                user_prompt = "any other thoughts?"
"""

query_aws_titan_code = """
                if session[constants.APP_MODE_SETTING] == constants.APP_MODE_VALUE_LOCAL_KEYS:
                    # I'm in local/dev mode
                    boto_session = boto3.Session(profile_name="jeremy")
                    bedrock = boto_session.client("bedrock-runtime", region_name="us-east-1")
                else:
                    # I'm on ec2 and should assume the correct role automatically
                    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

                body = {
                    "inputText": constants.SYSTEM_CONTENT_FILTER + "\n" + user_prompt,
                    "textGenerationConfig": {
                        "temperature": 0.7,
                        "maxTokenCount": 256,
                        "topP": 0.9,
                        "stopSequences": []
                    }
                }

                completion = bedrock.invoke_model(
                    body=json.dumps(body),
                    modelId=constants.DEFAULT_AWS_TITAN_MODEL,
                    contentType="application/json",
                    accept="application/json"
                )

                raw_body = completion["body"].read()
                decoded = json.loads(raw_body)
                response = decoded.get("results", [{}])[0].get("outputText", "")
"""

converse_aws_titan_code = """
                if session[constants.APP_MODE_SETTING] == constants.APP_MODE_VALUE_LOCAL_KEYS:
                    # confirmed I'm in local/dev mode
                    boto_session = boto3.Session(profile_name="jeremy")
                    bedrock = boto_session.client("bedrock-runtime", region_name="us-east-1")
                else:
                    print("will try to use via ec2 roles...")
                    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

                body = {
                    "inputText": constants.SYSTEM_CONTENT_FILTER + "\n" + user_prompt,
                    "textGenerationConfig": {
                        "temperature": 0.7,
                        "maxTokenCount": 256,
                        "topP": 0.9,
                        "stopSequences": []
                    }
                }

                completion = bedrock.invoke_model(
                    body=json.dumps(body),
                    modelId=constants.DEFAULT_AWS_TITAN_MODEL,
                    contentType="application/json",
                    accept="application/json"
                )

                raw_body = completion["body"].read()
                decoded = json.loads(raw_body)
                response = decoded.get("results", [{}])[0].get("outputText", "")
"""