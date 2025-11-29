
# agents/ale_agent.py
"""
Alê - Agente Regulatória
Especialista em MAPA, ANVISA, IBAMA
"""
from agentle.agents.agent import Agent
from agentle.agents.conversations.local_conversation_store import LocalConversationStore
from agentle.generations.providers.openrouter.openrouter_generation_provider import OpenRouterGenerationProvider
from agentle.generations.models.messages.user_message import UserMessage
from agentle.generations.models.message_parts.text import TextPart
from agentle.web.extractor import Extractor
from agentle.web.extraction_preferences import ExtractionPreferences
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field
from typing import List, Optional


# Schema de resposta estruturada de Alê
class AleResponse(BaseModel):
    """Resposta estruturada do agente Alê"""
    viabilidade_regulatoria: str = Field(description="verde, amarelo ou vermelho")
    prazo_estimado_meses: str = Field(description="Prazo em meses, ex: '18-24'")
    custo_estimado: str = Field(description="Custo total, ex: 'R$ 140K-180K'")
    caminho_registro: str = Field(description="Etapas do processo")
    alertas: List[str] = Field(default_factory=list, description="Alertas importantes")
    resumo: str = Field(description="Resumo executivo da análise")
    fonte_normativa: Optional[str] = Field(default=None, description="IN, Portaria, etc")


# Tools que Alê pode usar
async def buscar_portal_mapa(termo: str) -> str:
    """
    Busca informações no Portal do MAPA
    
    Args:
        termo: Termo de busca (ex: "bioestimulantes registro")
    
    Returns:
        Conteúdo relevante extraído
    """
    provider = OpenRouterGenerationProvider.with_fallback_models(["anthropic/claude-3.5-sonnet"])
    extractor = Extractor(llm=provider, model="anthropic/claude-3.5-sonnet")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        urls = [
            "https://www.gov.br/agricultura/pt-br/assuntos/insumos-agropecuarios/insumos-agricolas/fertilizantes/legislacao",
            # Adicionar mais URLs relevantes
        ]
        
        preferences = ExtractionPreferences(
            only_main_content=True,
            wait_for_ms=2000,
            block_ads=True,
            remove_base_64_images=True,
            timeout_ms=15000,
        )
        
        class MapaExtractedContent(BaseModel):
            informacao_relevante: str
            numero_normativa: Optional[str] = None
            data_publicacao: Optional[str] = None
        
        result = await extractor.extract_async(
            browser=browser,
            urls=urls,
            extraction_preferences=preferences,
            prompt=f"Extrair informações sobre: {termo}. Focar em requisitos, prazos e custos.",
            output=MapaExtractedContent
        )
        
        await browser.close()
        
        return result.output_parsed.informacao_relevante


async def consultar_dados_abertos_mapa(categoria: str) -> dict:
    """
    Consulta API de Dados Abertos do MAPA
    
    Args:
        categoria: Categoria de produto (bioestimulantes, biodefensivos, etc)
    
    Returns:
        Dados estruturados sobre registros similares
    """
    # TODO: Implementar chamada real para API do MAPA
    # Por enquanto, retorna mock
    return {
        "registros_similares": 12,
        "prazo_medio_meses": 18,
        "taxa_aprovacao_percent": 78
    }


# Criar agente Alê
def create_ale_agent() -> Agent:
    """Cria e configura o agente Alê"""
    
    system_instructions = """
    Você é Alê, agente de inteligência regulatória da UbyAgro.
    
    Sua especialidade é navegar pela complexidade regulatória do MAPA, ANVISA e IBAMA 
    para produtos do segmento de especialidades agrícolas (biodefensivos, bioestimulantes, 
    adjuvantes, nutrição foliar, biofertilizantes).
    
    SEMPRE:
    - Cite a fonte regulatória específica (IN, Portaria, Decreto)
    - Quantifique prazos e custos
    - Use dados históricos de produtos similares
    - Seja proativa em sugerir caminhos
    - Indique nível de certeza (alta/média/baixa)
    
    NUNCA:
    - Dê certezas absolutas sobre prazos (use "estimativa")
    - Ignore mudanças regulatórias recentes
    - Faça recomendações que violem normas
    
    Tom: Profissional, confiante, didática, meticulosa.
    
    Contexto UbyAgro: Empresa brasileira de especialidades agrícolas com 40 anos de mercado.
    Foco 95% Brasil. Portfólio: bioestimulantes, nutrição foliar, adjuvantes, biodefensivos.
    """
    
    provider = OpenRouterGenerationProvider.with_fallback_models([
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-sonnet"
    ])
    
    agent = Agent(
        instructions=system_instructions,
        generation_provider=provider,
        model="anthropic/claude-3.5-sonnet",
        tools=[buscar_portal_mapa, consultar_dados_abertos_mapa],
        response_schema=AleResponse,
        conversation_store=LocalConversationStore(),
    )
    
    return agent


async def run_ale_analysis(project_context: dict) -> AleResponse:
    """
    Executa análise regulatória completa
    
    Args:
        project_context: {
            "name": "Bioestimulante Algas Soja",
            "category": "bioestimulantes",
            "target_crop": "soja",
            "pdf_content": "...",  # texto extraído do PDF
        }
    
    Returns:
        Análise estruturada de Alê
    """
    agent = create_ale_agent()
    
    user_prompt = f"""
    Analise a viabilidade regulatória do seguinte projeto:
    
    Nome: {project_context['name']}
    Categoria: {project_context['category']}
    Cultura-alvo: {project_context['target_crop']}
    
    Conteúdo técnico:
    {project_context.get('pdf_content', 'Bioestimulante à base de algas marinhas')}
    
    Forneça:
    1. Status de viabilidade regulatória (verde/amarelo/vermelho)
    2. Prazo estimado para registro completo
    3. Custo total estimado (taxas + estudos)
    4. Caminho de registro passo a passo
    5. Alertas ou pontos de atenção
    6. Base normativa (INs, Portarias aplicáveis)
    """
    
    message_history = [
        UserMessage(parts=[TextPart(text=user_prompt)])
    ]
    
    output = await agent.run_async(message_history)
    
    return output.parsed


async def run_ale_chat(user_message: str, project_context: dict, chat_history: list) -> str:
    """
    Chat interativo com Alê sobre projeto específico
    
    Args:
        user_message: Pergunta do usuário
        project_context: Contexto do projeto
        chat_history: Histórico da conversa
    
    Returns:
        Resposta de Alê
    """
    agent = create_ale_agent()
    
    # Adiciona contexto do projeto no início
    context_message = f"""
    [CONTEXTO DO PROJETO]
    Nome: {project_context['name']}
    Categoria: {project_context['category']}
    Cultura: {project_context['target_crop']}
    Status Regulatório Atual: {project_context.get('status_regulatorio', 'Em análise')}
    """
    
    messages = [
        UserMessage(parts=[TextPart(text=context_message)])
    ]
    
    # Adiciona histórico do chat
    messages.extend(chat_history)
    
    # Adiciona nova mensagem do usuário
    messages.append(UserMessage(parts=[TextPart(text=user_message)]))
    
    output = await agent.run_async(messages)
    
    # Retorna texto da resposta (não estruturado para chat)
    return output.content[0].text if output.content else "Desculpe, não consegui gerar resposta."
