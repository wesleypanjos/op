import os
import sys
from dotenv import load_dotenv
import dspy
from dspy.primitives.prediction import Prediction
from dspy.teleprompt import BootstrapFewShot
import re
import streamlit as st

class QuestionAnswerSignature(dspy.Signature):
    """Extract precise answers from given context"""
    context = dspy.InputField(desc="Background information")
    question = dspy.InputField(desc="Specific query")
    answer = dspy.OutputField(desc="Concise, accurate response")

class QuestionAnswerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(QuestionAnswerSignature)
    
    def forward(self, context, question):
        return self.predictor(context=context, question=question)

class ProcessImprovementQA:
    def __init__(self, api_key=None, model='gpt-4o-mini', max_tokens=2048, temperature=0.2):
        """
        Initialize the ProcessImprovementQA system.
        
        Args:
            api_key (str, optional): OpenAI API key. If None, will try to load from environment.
            model (str): The OpenAI model to use
            max_tokens (int): Maximum tokens for the model
            temperature (float): Sampling temperature
        """
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        else:
            load_dotenv()
            if not st.secrets('OPENAI_API_KEY'):
                raise ValueError("OPENAI_API_KEY not found in environment variables.")
        
        self.configure_model(model, max_tokens, temperature)
        
    def configure_model(self, model, max_tokens, temperature):
        """Configure the OpenAI model for DSPy."""
        openai_model = dspy.OpenAI(model=model, max_tokens=max_tokens, temperature=temperature)
        dspy.settings.configure(lm=openai_model)
        
    def _create_context(self, ramo_empresa, direcao, nome_processo, atividade, evento, causa):
        """Create the context string from the given parameters."""
        return f"""
        - Gerente Sênior de Transformação de Processos, com +15 anos de experiência em consultoria empresarial.
        - Certificações: PMP, Lean Six Sigma Black Belt, ITIL Expert.
        - Abordagem sistemática para melhorias organizacionais.
        ***Contexto do Processo:***
        - Ramo: {ramo_empresa}
        - Processo: {nome_processo}
        - Atividade: {atividade}
        - Evento: {evento}
        - Causa: {causa}
        ***Diretrizes para Análise:***
        1. Identificar ineficiências e gargalos.
        2. Propor soluções estratégicas e viáveis.
        3. Elaborar plano detalhado de implementação.
        4. Estimar impacto econômico e operacional.
        5. Alinhar com objetivos organizacionais.
        ***Escopo:***
        - Avaliar criticamente processos.
        - Propor inovações práticas.
        - Estimar investimento e retorno.
        - Criar roadmap claro.
        """

    def _create_train_examples(self, new_resultados, context, direcao):
        """Create training examples from the provided data."""
        train_examples = []
        for resultado in new_resultados:
            example = dspy.Example(
                context=context,
                question=f"Oportunidade de Melhoria: {resultado['Oportunidade de Melhoria']}, Direcionadores: {direcao}",
                answer=f"Solução: {resultado['Solução']} | Backlog de Atividades: {resultado['Backlog de Atividades']} | Investimento: {resultado['Investimento']} | Ganhos: {resultado['Ganhos']}"
            ).with_inputs('context', 'question')
            train_examples.append(example)
        return train_examples

    def _validate_answer(self, example, pred, trace=None):
        """Validate the generated answer."""
        try:
            if not isinstance(pred, Prediction):
                return False
            if not pred.answer or not (0 < len(pred.answer) < 5000):
                return False
            return True
        except Exception:
            return False

    def _transform_answer(self, answer_str):
        """Transform the answer string into a structured dictionary."""
        patterns = {
            'Solução': r'Solução:\s*(.+?)(?=\s*\||\s*$)',
            'Backlog de Atividades': r'Backlog de Atividades:\s*(.+?)(?=\s*\||\s*$)',
            'Investimento': r'Investimento:\s*(.+?)(?=\s*\||\s*$)',
            'Ganhos': r'Ganhos:\s*(.+?)(?=\s*\||\s*$)'
        }
        
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, answer_str, re.DOTALL)
            if match:
                value = match.group(1).strip()
                result[key] = ' '.join([item.strip() for item in value.split('\n') if item.strip()])
        
        return result

    def get_improvement_suggestion(self, new_resultados, oportunidade_melhoria, ramo_empresa, 
                                 direcao, nome_processo, atividade, evento, causa):
        """
        Generate an improvement suggestion based on the provided parameters.
        
        Args:
            new_resultados (list): List of previous improvement results
            oportunidade_melhoria (str): The improvement opportunity to analyze
            ramo_empresa (str): Company sector
            direcao (str): Direction/goal
            nome_processo (str): Process name
            atividade (str): Activity name
            evento (str): Event description
            causa (str): Root cause
            
        Returns:
            dict: Structured improvement suggestion
        """
        # Create context
        context = self._create_context(ramo_empresa, direcao, nome_processo, 
                                     atividade, evento, causa)
        
        # Create and compile QA module
        train_examples = self._create_train_examples(new_resultados, context, direcao)
        teleprompter = BootstrapFewShot(
            metric=self._validate_answer,
            max_bootstrapped_demos=4
        )
        compiled_module = teleprompter.compile(
            QuestionAnswerModule(), 
            trainset=train_examples
        )
        
        # Generate answer
        question = f"Oportunidade de Melhoria: {oportunidade_melhoria}, Direcionadores: {direcao}"
        prediction = compiled_module(context=context, question=question)
        
        # Transform and return the answer
        return self._transform_answer(prediction.answer)