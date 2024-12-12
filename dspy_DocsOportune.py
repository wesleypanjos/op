import os
import sys
from dotenv import load_dotenv
import dspy
from openai import OpenAI
import weaviate
from dspy.retrieve.weaviate_rm import WeaviateRM

# Carrega o .env para configurar a chave OPENAI_API_KEY
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Verifica se a chave foi carregada corretamente
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")

# Configura o diretório atual
os.chdir(os.path.abspath(os.curdir))

def custom_excepthook(exctype, value, traceback):
    print(f"Exception type: {exctype}")
    print(f"Exception value: {value}")
    print("Traceback details:")
    return sys.__excepthook__(exctype, value, traceback)

sys.excepthook = custom_excepthook

try:
    class Oportune(dspy.Signature): 
        """
        ** Contexto: **
        Você é um experiente Gerente de Projetos e Processos de uma grande empresa que presta consultoria na área de projetos e possui
        diversas certificações internacionais. 
        Sua tarefa principal é mapear os problemas que são identificados na consultoria, perceber quais são as oportunidades de melhoria
        que irão favorecer o cliente e o projeto como um todo e por fim ter um plano de tarefas bem definido, em tópicos, para o problema
        relatado e identificado juntamente com o cliente. Sua idéias para melhorar os processos da empresa com oportunidades aprendidas 
        durante o seu exercício de consultoria em outros clientes fará toda diferença. A entrada de dados será feita de forma estruturada
        para garantir que todos os campos do diagnostico sejam inseridos, segue o exemplo:

        ** EXEMPLO DE ENTRADA DE DADOS: **
            - ramo_empresa: aqui entra o nicho de mercado da empresa, 
            - direcionadores: o objetivo do projeto, 
            - nome_do_processo: nome dado para identificar o projeto e processo, 
            - atividade: ação que será executada, 
            - evento: situação ou problema identificado, 
            - causa: fato gerador do problema ou situacao que esta no evento
        
        """  
    
        # TEXTO DO PROBLEMA DE ENTRADA
        question = dspy.InputField()
        # AQUI TEMOS AS OPORTUNIDADES QUE VEM DA BASE FRIA (NO CASO ESTAMOS USANDO 5 PASSAGES)
        context = dspy.InputField(desc="traga as oportunidades mais relevantes para o cenário do cliente em questão.")    
    
        # RESPOSTA SEGUINDO OS FEWSHOTS dspy.Example()
        answer = dspy.OutputField(desc="""Dê sua resposta com as **10** melhores oportunidades, cite as possíveis soluções para cada solução, 
                                      cada uma com o investimento que irá ser necessário e os ganhos que irá trazer a empresa, 
                                      modelo de resposta:
                                      
                                      **Oportunidade de Melhoria** : Automatização de Captura de Informações de Pagamentos:
                                      
                                      **Solução** : Desenvolver uma integração com o sistema bancário para captura automática de informações sobre pagamentos realizados e recusados. Isso inclui a baixa automática dos pagamentos no sistema e notificações para as áreas interessadas em caso de problemas.
                                      
                                      **Backlog de Atividades:** Sugestões de atividades específicas que podem ser adicionadas a um backlog de implementação para atingir a solução. 
                                      
                                      **Investimento** : Horas para desenvolvimento de customizações e implantação do projeto.
                                      
                                      **Ganhos:** Automação de atividades manuais e repetitivas, maior agilidade no processo, redução do 
                                      risco de erros operacionais e simplificação da disseminação de informações entre as partes interessadas. 

                                      Dê sugestões simples e eficientes de acordo com o seu conhecimento e contexto. 
                                      Pense passo a passo, gerando mais de uma resposta, avalie cada passo e veja qual dos sugeridos 
                                      é o mais adequado. 
                                      RESPONDA em Português do Brasil.
                            """)

    class OportuneRAG(dspy.Module):
        def __init__(self, num_passages=5): 
            super().__init__()
        
            self.retrieve = dspy.Retrieve(k=num_passages)
            self.generate_answer = dspy.ChainOfThought(Oportune) # Step by Step Cadeia de pensamento...

        def forward(self, question):
            context = self.retrieve(question).passages
            prediction = self.generate_answer(context=context, question=question)        
            return dspy.Prediction(context=context, answer=prediction.answer)   

except Exception as e:
    print(f"ERRO CLASSES: {e}")

print('dspy_DocsOportune.py: OK')









