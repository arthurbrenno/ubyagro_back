# main.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="BioGrow API",
    description="Plataforma de Inteligência Competitiva para o Agro",
    version="1.0.0"
)

# CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS (Pydantic Schemas)
# ============================================================================

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict

class ProjectCreate(BaseModel):
    name: str
    category: Literal["biodefensivos", "bioestimulantes", "adjuvantes", "nutricao_foliar", "biofertilizantes"]
    target_crop: Literal["soja", "milho", "cana", "cafe", "algodao"]
    description: Optional[str] = None

class AgentProgress(BaseModel):
    status: Literal["completed", "processing", "pending", "failed"]
    progress_percent: int
    estimated_time_remaining_seconds: int

class ProjectStatus(BaseModel):
    project_id: str
    status: Literal["processing", "completed", "failed"]
    progress: dict[str, AgentProgress]
    overall_progress_percent: int

class AgentAnalysisDetails(BaseModel):
    agent_name: str
    agent_role: str
    status: Literal["verde", "amarelo", "vermelho"]
    score: int
    summary: str
    details: dict

class ProjectAnalysis(BaseModel):
    project_id: str
    project_name: str
    overall_score: int
    recommendation: Literal["VIAVEL", "VIAVEL_COM_AJUSTES", "NAO_VIAVEL"]
    recommendation_text: str
    analyzed_at: datetime
    agents: dict[str, AgentAnalysisDetails]
    financial_projection: dict
    action_items: List[str]
    alerts: List[dict]

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    chat_id: str
    agent_id: str
    agent_name: str
    message_id: str
    response: dict
    timestamp: datetime

# ============================================================================
# MOCK DATA (Para o Frontend trabalhar enquanto você implementa)
# ============================================================================

MOCK_ANALYSIS_DATA = {
    "project_id": "proj-abc123",
    "project_name": "Bioestimulante Algas Soja",
    "overall_score": 82,
    "recommendation": "VIAVEL_COM_AJUSTES",
    "recommendation_text": "Projeto viável com ajustes menores na formulação para evitar conflito de patente",
    "analyzed_at": datetime.now(),
    "agents": {
        "ale": {
            "agent_name": "Alê",
            "agent_role": "Regulatória",
            "status": "verde",
            "score": 90,
            "summary": "Via livre regulatória. Registro estimado em 18-24 meses via MAPA.",
            "details": {
                "prazo_meses": "18-24",
                "custo_estimado": "R$ 140K-180K",
                "caminho_registro": "SIPEAGRO → Dossiê → Análise MAPA → Publicação",
                "alertas": [],
                "pontos_atencao": ["80% dos bioestimulantes têm 1-2 complementações"]
            }
        },
        "merc": {
            "agent_name": "Merc",
            "agent_role": "Mercado",
            "status": "verde",
            "score": 85,
            "summary": "Mercado de R$ 850M/ano crescendo +15% a.a.",
            "details": {
                "tamanho_mercado": "R$ 850M/ano",
                "crescimento_anual": "+15.3%",
                "potencial_vendas_ano1": "R$ 17M-26M",
                "regiao_foco": "Rio Grande do Sul"
            }
        },
        "pat": {
            "agent_name": "Pat",
            "agent_role": "Patentes",
            "status": "amarelo",
            "score": 75,
            "summary": "Identificadas 2 patentes com potencial conflito.",
            "details": {
                "patentes_relevantes": 12,
                "patentes_conflito": 2,
                "recomendacao": "Ajustar proporção de polissacarídeos"
            }
        },
        "dex": {
            "agent_name": "Dex",
            "agent_role": "Dados e Ciência",
            "status": "verde",
            "score": 88,
            "summary": "73 artigos comprovam eficácia. Dados internos validam.",
            "details": {
                "artigos_encontrados": 73,
                "nivel_evidencia": "Forte",
                "dados_internos": {
                    "performance_observada": "+18% produtividade",
                    "numero_fazendas": 47
                }
            }
        }
    },
    "financial_projection": {
        "investimento_pd": "R$ 1.2M - R$ 1.8M",
        "roi_3anos_percent": "320-480%"
    },
    "action_items": [
        "Contatar Embrapa Soja para parceria",
        "Iniciar testes de formulação alternativa"
    ],
    "alerts": []
}

# ============================================================================
# AUTH (Simplificado para MVP)
# ============================================================================

def verify_token(token: str = Depends(lambda: "mock_token")):
    # MVP: Aceita qualquer token
    # TODO: Implementar JWT real
    if not token:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    return {"user_id": "user-1", "role": "colaborador"}

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """Login simplificado (mock)"""
    return {
        "token": "mock_token_abc123",
        "user": {
            "id": "user-1",
            "name": "João Silva",
            "email": request.email,
            "role": "colaborador"
        }
    }

@app.post("/api/v1/projects")
async def create_project(
    name: str = Form(...),
    category: str = Form(...),
    target_crop: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """
    Cria novo projeto e inicia análise pelos 4 agentes
    
    TODO: 
    - Salvar PDF em storage
    - Enfileirar job de análise assíncrona
    - Processar com os 4 agentes em paralelo
    """
    
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    
    # MVP: Salvar PDF localmente (produção: S3/MinIO)
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{project_id}.pdf"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # TODO: Enfileirar processamento assíncrono
    # await queue.enqueue_analysis(project_id, file_path)
    
    return {
        "project_id": project_id,
        "name": name,
        "category": category,
        "target_crop": target_crop,
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "created_by": current_user["user_id"]
    }

@app.get("/api/v1/projects/{project_id}/status")
async def get_project_status(
    project_id: str,
    current_user: dict = Depends(verify_token)
):
    """
    Retorna status do processamento em tempo real
    
    TODO: Consultar Redis/DB para status real de cada agente
    """
    
    # MVP: Mock de progresso simulado
    return {
        "project_id": project_id,
        "status": "processing",
        "progress": {
            "ale": {
                "status": "completed",
                "progress_percent": 100,
                "estimated_time_remaining_seconds": 0
            },
            "merc": {
                "status": "processing",
                "progress_percent": 75,
                "estimated_time_remaining_seconds": 15
            },
            "pat": {
                "status": "processing",
                "progress_percent": 50,
                "estimated_time_remaining_seconds": 30
            },
            "dex": {
                "status": "pending",
                "progress_percent": 0,
                "estimated_time_remaining_seconds": 60
            }
        },
        "overall_progress_percent": 56
    }

@app.get("/api/v1/projects/{project_id}/analysis")
async def get_project_analysis(
    project_id: str,
    current_user: dict = Depends(verify_token)
):
    """
    Retorna análise completa dos 4 agentes
    
    TODO: Buscar do banco de dados
    """
    
    # MVP: Retornar mock data
    mock_data = MOCK_ANALYSIS_DATA.copy()
    mock_data["project_id"] = project_id
    return mock_data

@app.post("/api/v1/projects/{project_id}/chat/{agent_id}")
async def chat_with_agent(
    project_id: str,
    agent_id: Literal["ale", "merc", "pat", "dex"],
    message: ChatMessage,
    current_user: dict = Depends(verify_token)
):
    """
    Inicia ou continua chat com agente específico
    
    TODO: Implementar usando agentle (seu framework)
    """
    
    chat_id = f"chat-{uuid.uuid4().hex[:8]}"
    message_id = f"msg-{uuid.uuid4().hex[:6]}"
    
    # AQUI É ONDE VOCÊ VAI INTEGRAR COM AGENTLE
    # agent_response = await run_agent(agent_id, message.message, project_context)
    
    # MVP: Mock response
    agent_names = {
        "ale": "Alê",
        "merc": "Merc",
        "pat": "Pat",
        "dex": "Dex"
    }
    
    mock_response = f"[Mock] Resposta do agente {agent_names[agent_id]} para: {message.message}"
    
    return {
        "chat_id": chat_id,
        "agent_id": agent_id,
        "agent_name": agent_names[agent_id],
        "message_id": message_id,
        "response": {
            "text": mock_response,
            "structured_data": {}
        },
        "timestamp": datetime.now()
    }

@app.get("/api/v1/projects")
async def list_projects(
    status: Literal["all", "processing", "completed", "failed"] = "all",
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(verify_token)
):
    """
    Lista projetos do usuário
    
    TODO: Buscar do banco de dados com filtros
    """
    
    # MVP: Mock data
    return {
        "projects": [
            {
                "project_id": "proj-abc123",
                "name": "Bioestimulante Algas Soja",
                "category": "bioestimulantes",
                "target_crop": "soja",
                "status": "completed",
                "overall_score": 82,
                "created_at": datetime.now().isoformat(),
                "analyzed_at": datetime.now().isoformat()
            }
        ],
        "total": 1,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/knowledge-base")
async def list_documents(
    category: str = "all",
    search: str = "",
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(verify_token)
):
    """Lista documentos da base de conhecimento"""
    
    # MVP: Mock data
    return {
        "documents": [
            {
                "doc_id": "doc-001",
                "title": "Guia Completo: Registro de Bioestimulantes no MAPA",
                "type": "guia",
                "category": "regulamentacoes",
                "related_agents": ["ale"],
                "rating": 4.8,
                "rating_count": 23,
                "views": 142,
                "tags": ["MAPA", "bioestimulantes", "registro"]
            }
        ],
        "total": 1,
        "limit": limit,
        "offset": offset
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {
        "message": "BioGrow API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================================================
# PARA RODAR:
# uvicorn main:app --reload --port 8000
# ============================================================================