import pandas as pd
import json
import logging
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain_experimental.tools import PythonREPLTool
from langchain.hub import pull as hub_pull
from dotenv import load_dotenv
import os
import streamlit as st

# Initialize logger
logger = logging.getLogger(__name__)

# Load OpenAI API key from environment variables
load_dotenv()
api_key = st.secrets["OPENAI_API_KEY"]

# Initialize LLM with specific settings
def initialize_llm():
    return ChatOpenAI(
        temperature=0.1,
        model="gpt-4o-mini",
        api_key=api_key,
        verbose=True
    )

# Create ReAct agent
def create_react_agent(llm):
    try:
        react_prompt_template = hub_pull("hwchase17/react")
        tools = [PythonREPLTool()]
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={"prompt": react_prompt_template}
        )
        return agent
    except Exception as e:
        logger.error("Error creating ReAct agent: %s", e)
        raise

def transform_input_to_df(input_data):
    """
    Transform input data into a pandas DataFrame using a ReAct agent.
    
    Parameters:
    input_data (str): Input data in the specified format.
    
    Returns:
    pandas.DataFrame: DataFrame with the transformed data.
    """
    try:
        # Initialize LLM and ReAct agent
        llm = initialize_llm()
        agent = create_react_agent(llm)
        
        # Format the question for the agent with instructions and input data
        question = f"""
        **INSTRUCOES:**
        Você é um engenheiro de dados sênior de uma grande empresa. Com base nas entrada fornecida {input_data}, transforme cada conjunto de dados em uma lista de dicionários, com a estrutura desejada:
        
        **FORMATO DE SAÍDA**:
        [
            {{
                "Oportunidade de Melhoria": "Descrição clara da oportunidade",
                "Solução": "Solução recomendada",
                "Backlog de Atividades": "Atividades sugeridas para implementação em **tópicos na mesma celula**",
                "Investimento": "Investimento necessário",
                "Ganhos": "Ganhos esperados"
            }},
            // outros dicionários para cada entrada
        ]
        **FORMATO DE SAÍDA**:
        Retorne apenas a lista de dicionários sem aspas adicionais, sem a palavra "Python", e sem explicações.
        """
        
        # Run the agent to process the question and generate output
        response = agent.run(question)
        data = json.loads(response)
        df = pd.DataFrame(data)
        return df
    except json.JSONDecodeError as e:
        logger.error("Error parsing response to JSON: %s", e)
        return f"Error parsing response: {str(e)}"
    except Exception as e:
        logger.error("Error during transformation with agent: %s", e)
        return f"Error during transformation: {str(e)}"