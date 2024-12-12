import streamlit as st
import base64
from pathlib import Path
import os
from dotenv import load_dotenv
from process import run_agent_analysis
import pandas as pd
from io import BytesIO
import time
import streamlit as st

load_dotenv()
api_key = st.secrets("OPENAI_API_KEY")

all_resultados=[]

if 'direcionadores' not in st.session_state:
    st.session_state.direcionadores = []

def stylable_container(key, css_styles):
    st.markdown(f"""
        <style>
        div[data-testid="stHorizontalBlock"] > div:nth-child({key}) {{
            {css_styles}
        }}
        </style>
    """, unsafe_allow_html=True)
    return st.container()

def add_bg_from_local(image_file):
    with Path(image_file).open("rb") as file:
        encoded_string = base64.b64encode(file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{encoded_string});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def load_css(css_file):
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def get_button_style(button_class):
    if button_class == "current":
        return "background-color: #01374C; color: white; font-weight: bold; font-size: 24px;"
    elif button_class == "previous":
        return "background-color: #4B4843; color: white; font-weight: normal; font-size: 24px;"
    else:
        return "background-color: #4B484340; color: #333333; font-size: 18px;"

def setup_navigation():
    st.sidebar.markdown("<h1 style='text-align: center; color: #AC8D61;'>Navegação</h1>", unsafe_allow_html=True)
    
    pages = ["🔍 Oportunidade de melhorias", "📋 Planilha Final"]
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    for i, page in enumerate(pages):
        button_class = "current" if i == st.session_state.current_page else "previous" if i == st.session_state.current_page - 1 else ""

        if st.sidebar.button(page, key=f"nav_{i}", use_container_width=True, disabled=(i == st.session_state.current_page)):
            st.session_state.current_page = i
            st.rerun()

        st.markdown(f"""
            <style>
            div.row-widget.stButton > button[key="nav_{i}"] {{
                {get_button_style(button_class)}
            }}
            </style>
            """, unsafe_allow_html=True)

    return pages

def add_direcionador(new_direcionador):
    if new_direcionador and new_direcionador not in st.session_state.direcionadores:
        st.session_state.direcionadores.append(new_direcionador)
        return True
    return False

def remove_direcionador(direcionador_to_remove):
    if direcionador_to_remove in st.session_state.direcionadores:
        st.session_state.direcionadores.remove(direcionador_to_remove)

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Oportunidade de melhorias', index=False)
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['Oportunidade de melhorias'].column_dimensions[chr(65 + col_idx)].width = column_width + 2
    return output.getvalue()

def render_diagnostico():
    if 'form_inputs' not in st.session_state:
        st.session_state.form_inputs = {
            'ramo_empresa': '',
            'nome_processo': '',
            'atividade': '',
            'evento': '',
            'causa': ''
        }
    
    if 'all_resultados' not in st.session_state:
        st.session_state.all_resultados = []
        
    st.write("## Oportunidade de Melhoria")

    with st.form(key='add_direcionador_form'):
        new_direcionador = st.text_input(
            "Novo Direcionador",
            placeholder="Digite um novo direcionador",
            key="new_direcionador"
        )
        if st.form_submit_button("Adicionar Direcionador"):
            if add_direcionador(new_direcionador):
                st.success(f"Direcionador '{new_direcionador}' adicionado com sucesso!")
                st.rerun()
            else:
                if not new_direcionador:
                    st.warning("Por favor, digite um direcionador.")
                else:
                    st.warning("Este direcionador já existe.")

    for direcionador in st.session_state.direcionadores:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(direcionador)
        with col2:
            if st.button("Remover", key=f"remove_{direcionador}"):
                remove_direcionador(direcionador)
                st.rerun()

    with st.form(key='oportunidade_melhoria_form'):
        ramo_empresa = st.text_input(
            "Ramo da empresa", 
            value=st.session_state.form_inputs['ramo_empresa'],
            placeholder="Digite o ramo da empresa"
        )
        nome_processo = st.text_input(
            "Nome do processo", 
            value=st.session_state.form_inputs['nome_processo'],
            placeholder="Digite o nome do processo"
        )
        atividade = st.text_input(
            "Atividade", 
            value=st.session_state.form_inputs['atividade'],
            placeholder="Digite a atividade"
        )
        evento = st.text_input(
            "Evento", 
            value=st.session_state.form_inputs['evento'],
            placeholder="Digite o evento"
        )
        causa = st.text_input(
            "Causa", 
            value=st.session_state.form_inputs['causa'],
            placeholder="Digite a causa"
        )

        submit_button = st.form_submit_button(label='Obter Oportunidade de melhorias')

        if submit_button:
            st.session_state.form_inputs = {
                'ramo_empresa': ramo_empresa,
                'nome_processo': nome_processo,
                'atividade': atividade,
                'evento': evento,
                'causa': causa
            }

            if ramo_empresa and st.session_state.direcionadores and nome_processo and atividade and evento and causa:
                with st.spinner('Oportunidade de melhorias em andamento...'):
                    start_time = time.time()
                    new_resultados = []
                    
                    if type(st.session_state.direcionadores) == str:
                        direcao = st.session_state.direcionadores
                        processo = f"""ramo_empresa: {ramo_empresa}, direcionadores: {direcao}, nome_do_processo: {nome_processo}, atividade: {atividade}, evento: {evento}, causa: {causa}"""
                        analyst = run_agent_analysis(processo)
                        analyst['Direcionador'] = direcao
                        new_resultados.append(analyst)
                    else:
                        for direcao in st.session_state.direcionadores:
                            processo = f"""ramo_empresa: {ramo_empresa}, direcionadores: {direcao}, nome_do_processo: {nome_processo}, atividade: {atividade}, evento: {evento}, causa: {causa}"""
                            analyst = run_agent_analysis(processo)
                            analyst['Direcionador'] = direcao
                            new_resultados.append(analyst)
                    
                    if new_resultados:
                        st.session_state.all_resultados.extend(new_resultados)
                        resultados = pd.concat(st.session_state.all_resultados, ignore_index=True)
                        execution_time = time.time() - start_time
                        
                        st.success(f"Oportunidade de melhorias obtidas para {len(st.session_state.direcionadores)} direcionadores em {execution_time:.2f} segundos.")
                        
                        st.session_state.resultados = resultados
                        st.session_state.excel_file = convert_df_to_excel(resultados)
                        st.session_state.show_download_button = True
            else:
                st.warning("Por favor, preencha todos os campos e adicione pelo menos um direcionador.")

    if hasattr(st.session_state, 'show_download_button') and st.session_state.show_download_button:
        st.download_button(
            label="📥Baixar Excel",
            data=st.session_state.excel_file,
            file_name='oportunidade_melhoria.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )




def render_planilha_final():
    if 'resultados' not in st.session_state:
        st.warning("Não foi executado a obtenção das Oportunidade de melhorias.")
        return
    
    resultados = st.session_state.resultados
    st.session_state.resultados_dict = resultados.to_dict('records')

    st.write("## Planilha Final")
    changes_made = False
    deleted_indices = set()

    for idx, row in enumerate(st.session_state.resultados_dict):
        if idx in deleted_indices:  # Skip opportunities already marked for deletion
            continue
        
        with st.form(key=f'opportunity_form_{idx}'):
            st.write(f"### Oportunidade {idx + 1} - Direcionador: {row.get('Direcionador', 'N/A')}")
            
            oportunidade_de_melhoria = st.text_area(
                "Oportunidade de Melhoria", 
                value=row['Oportunidade de Melhoria'], 
                height=100
            )
            solucao = st.text_area(
                "Solução", 
                value=row['Solução'], 
                height=100
            )
            backlog_de_atividades = st.text_area(
                "Backlog de Atividades", 
                value=row.get('Backlog de Atividades', ''), 
                height=100
            )
            investimento = st.text_area(
                "Investimento", 
                value=row.get('Investimento', ''), 
                height=100
            )
            ganhos = st.text_area(
                "Ganhos", 
                value=row.get('Ganhos', ''), 
                height=100
            )
            
            col1, col2 = st.columns(2)
            with col1:
                save_button = st.form_submit_button(label=f"Salvar Edição para Oportunidade {idx + 1}")
            with col2:
                delete_button = st.form_submit_button(label=f"Excluir Oportunidade {idx + 1}", type="secondary")
            
            if save_button:
                row.update({
                    'Oportunidade de Melhoria': oportunidade_de_melhoria,
                    'Solução': solucao,
                    'Backlog de Atividades': backlog_de_atividades,
                    'Investimento': investimento,
                    'Ganhos': ganhos
                })
                changes_made = True
                st.success(f"Edição salva para Oportunidade {idx + 1}")
            
            if delete_button:
                deleted_indices.add(idx)
                st.warning(f"Oportunidade {idx + 1} marcada para exclusão.")

    if deleted_indices:
        st.session_state.resultados_dict = [
            row for idx, row in enumerate(st.session_state.resultados_dict) if idx not in deleted_indices
        ]
        changes_made = True

    if changes_made:
        edited_df = pd.DataFrame(st.session_state.resultados_dict)
        st.session_state.resultados = edited_df
        st.session_state.excel_file = convert_df_to_excel(edited_df)
        st.session_state.show_download_button = True

    if hasattr(st.session_state, 'show_download_button') and st.session_state.show_download_button:
        st.download_button(
            label="📥 Baixar Excel com Todas as Edições",
            data=st.session_state.excel_file,
            file_name='Oportunidade_de_melhorias_final.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


def main():
    st.set_page_config(page_title="Oportunidade de Melhoria", layout="wide")
    add_bg_from_local('background.png')
    load_css('style.css')
    
    pages = setup_navigation()
    progress_value = (st.session_state.current_page + 1) / len(pages)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<p class="big-font">{pages[st.session_state.current_page]}</p>', unsafe_allow_html=True)
    with col2:
        st.image('logo.png', width=200)
    
    st.progress(progress_value)

    main_container = st.container()
    with main_container:
        if pages[st.session_state.current_page] == "🔍 Oportunidade de melhorias":
            render_diagnostico()  
        elif pages[st.session_state.current_page] == "📋 Planilha Final":
            render_planilha_final()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state.current_page > 0:
            if st.button("Anterior", key="prev_button"):
                st.session_state.current_page -= 1
                st.rerun()
    with col3:
        if st.session_state.current_page < len(pages) - 1:
            if st.button("Próximo", key="next_button"):
                st.session_state.current_page += 1
                st.rerun()
        elif st.session_state.current_page == len(pages) - 1:
            if st.button("Finalizar", key="finish_button"):
                st.success("Processo finalizado com sucesso!")

if __name__ == "__main__":
    main()