from modeloDSpy import OportuneRAGClient
from transform_input_to_df import transform_input_to_df

def run_agent_analysis(prompt):
    """
    Executa a análise utilizando os agentes OportuneRAGClient e transform_input_to_df.
    
    Parâmetros:
    prompt (str): Prompt a ser enviado para o agente OportuneRAGClient.
    
    Retorna:
    pandas.DataFrame: Resultado da análise.
    """
    client = OportuneRAGClient()
    answer = client.run_model(prompt)
    df = transform_input_to_df(answer)
    client.close_weaviate_client()
    return df