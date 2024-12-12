import os
import sys
from dotenv import load_dotenv
import weaviate
from dspy.retrieve.weaviate_rm import WeaviateRM
import dspy
from openai import OpenAI
from dspy_DocsOportune import OportuneRAG
from weaviate.auth import AuthApiKey
import streamlit as st
class OportuneRAGClient:
    def __init__(self):
        # Explicitly load .env file and print debug information
        load_dotenv()
       
        # Debug print environment variables
        print("OPENAI_API_KEY:", "SET" if st.secrets["OPENAI_API_KEY"] else "NOT SET")
        print("WEAVIATE_CLUSTER_URL:", st.secrets["WEAVIATE_URL"])
        print("WEAVIATE_API_KEY:", "SET" if st.secrets["WEAVIATE_API_KEY"] else "NOT SET")
        # Retrieve environment variables
        self.secretk = st.secrets["OPENAI_API_KEY"]
        print("self.secretk: ",self.secretk)
        self.weaviate_cluster_url = st.secrets["WEAVIATE_URL"]
        print("st.secrets: ", st.secrets["OPENAI_API_KEY"])
        self.weaviate_api_key = st.secrets["WEAVIATE_API_KEY"]
        # Validate environment variables
        if not all([self.secretk, self.weaviate_cluster_url, self.weaviate_api_key]):
            print("Error: Missing required environment variables")
            sys.exit(1)

        self.client = OpenAI(api_key=self.secretk)
        self.weaviate_client = self.setup_weaviate_client()
        self.params4o = self.setup_dspy_params()
        self.modelo = OportuneRAG()
        self.load_modelo()

            

    def setup_weaviate_client(self):
        try:
            # Validate cluster URL
            if not self.weaviate_cluster_url:
                raise ValueError("Weaviate cluster URL is not set")
            weaviate_client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.weaviate_cluster_url,
                auth_credentials=weaviate.AuthApiKey(self.weaviate_api_key),
                headers={
                    "X-OpenAI-Api-Key": self.secretk
                }
            )
            
            return weaviate_client
        except Exception as e:
            print(f"ERRO CONEXAO: {e}")
            print(f"Cluster URL: {self.weaviate_cluster_url}")
            print(f"API Key provided: {bool(self.weaviate_api_key)}")
            return None

    def setup_dspy_params(self):
        try:
            if self.weaviate_client is None:
                raise ValueError("Weaviate client is not initialized")
            return {
                "lm": dspy.OpenAI(model='gpt-4o', max_tokens=2048, temperature=0.2),
                "rm": WeaviateRM("DocsOportunidades", weaviate_client=self.weaviate_client,
                                weaviate_collection_text_key="oportunidade_melhoria")
            }
        except Exception as e:
            print(f"ERRO DSpy.settings: {e}")
            return None

    def load_modelo(self):
        try:
            caminho = r"modelo_oportune_08112024.json"
            # Added use_legacy_loading=True to the load method
            self.modelo.load(path=caminho, use_legacy_loading=True)
        except Exception as e:
            print(f"ERRO CARREGANDO MODELO: {e}")

    def run_model(self, prompt):
        try:
            # Check if params are properly set
            if self.params4o is None:
                raise ValueError("DSpy parameters not properly initialized")
            dspy.settings.configure(**self.params4o)
            resposta = self.modelo(question=prompt)
            return resposta.answer
        except Exception as e:
            print(f"ERRO AO RODAR O MODELO: {e}")
            return None

    def close_weaviate_client(self):
        try:
            if self.weaviate_client:
                self.weaviate_client.close()
        except Exception as e:
            print(f"ERRO AO FECHAR WEAVIATE CLIENT: {e}")