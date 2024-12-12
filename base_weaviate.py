import pandas as pd
import openai
import weaviate
import os
import streamlit as st


df_base = pd.read_excel('Base.xlsx', skiprows = 2, header = 1)
df_base = df_base.iloc[:, :9]

renomear = {"EMPRESA": "EMPRESA",
            "SEGMENTO DE MERCADO": "SEGMENTO_MERCADO",
            "PROCESSO": "PROCESSO",
            "ATIVIDADE RELACIONADA": "ATIVIDADE_RELACIONADA",
            "TIPO DE MELHORIA": "MELHORIA_SUGERIDA",
            "DESCONEXÕES (GAP)": "GAPS",
            "CAUSA": "CAUSA",
            "MELHORIA/SOLUÇÃO": "SOLUCAO",
            "GANHOS/OBJETIVO": "GANHOS"
}

df_base = df_base.rename(columns=renomear)

# Configuração da API OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Conexão com o Weaviate
client = weaviate.Client(
    url=st.secrets["WEAVIATE_URL"],
    auth_client_secret=weaviate.AuthApiKey(
        api_key=st.secrets["WEAVIATE_API_KEY"] 
    ),
    additional_headers={
        "X-OpenAI-Api-Key": openai.api_key,  
    }
)

schema = {
    "classes": [
        {
            "class": "DocsOportunidades",
            "description": "Detalhes de melhorias em processos empresariais",
            "properties": [
                {"name": "EMPRESA", "dataType": ["text"], "description": "Nome da empresa"},
                {"name": "SEGMENTO_MERCADO", "dataType": ["text"], "description": "Segmento de mercado"},
                {"name": "PROCESSO", "dataType": ["text"], "description": "Descrição do processo"},
                {"name": "ATIVIDADE_RELACIONADA", "dataType": ["text"], "description": "Atividade relacionada ao processo"},
                {"name": "MELHORIA_SUGERIDA", "dataType": ["text"], "description": "Categoria da melhoria sugerida"},
                {"name": "GAPS", "dataType": ["text"], "description": "Problemas ou lacunas identificadas"},
                {"name": "CAUSA", "dataType": ["text"], "description": "Causa raiz do problema"},
                {"name": "SOLUCAO", "dataType": ["text"], "description": "Proposta de melhoria ou solução"},
                {"name": "GANHOS", "dataType": ["text"], "description": "Ganhos ou objetivos esperados com a solução"}
            ],
            "vectorizer": "text2vec-openai"  # Permite vetorização automática
        }
    ]
}

# Verifica se o schema já existe
if not client.schema.contains({'classes': [{'class': 'DocsOportunidades'}]}):
    client.schema.create(schema)

# Função para gerar embeddings com OpenAI
def generate_embedding(text):
    if not text:  # Garantir que o texto não seja vazio
        return None
    response = openai.embeddings.create(
        model="text-embedding-ada-002",  # Modelo de embeddings
        input=text
    )
    return response['data'][0]['embedding']

# Iterar sobre as linhas do DataFrame df_base e processar os dados
for _, row in df_base.iterrows():
    # Criar uma string concatenada para gerar embedding
    combined_text = f"{row['MELHORIA_SUGERIDA']} {row['SEGMENTO_MERCADO']} {row['EMPRESA']} {row['PROCESSO']} {row['ATIVIDADE_RELACIONADA']} {row['GAPS']} {row['CAUSA']} {row['SOLUCAO']} {row['GANHOS']}"
    embedding = generate_embedding(combined_text)

    if embedding:  # Verificar se a embedding foi gerada corretamente
        # Adicionar ao Weaviate
        client.data_object.create(
            class_name="DocsOportunidades",
            properties={
                "EMPRESA": row['EMPRESA'],
                "SEGMENTO_MERCADO": row['SEGMENTO_MERCADO'],
                "PROCESSO": row['PROCESSO'],
                "ATIVIDADE_RELACIONADA": row['ATIVIDADE_RELACIONADA'],
                "MELHORIA_SUGERIDA": row['MELHORIA_SUGERIDA'],
                "GAPS": row['GAPS'],
                "CAUSA": row['CAUSA'],
                "SOLUCAO": row['SOLUCAO'],
                "GANHOS": row['GANHOS']
            },
            vector=embedding  # Adiciona o embedding gerado
        )

print("Dados processados e armazenados no Weaviate com sucesso.")