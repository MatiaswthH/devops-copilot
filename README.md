# DevOps Copilot

> Un agente de IA que diagnostica incidentes y fallos de deploy en Kubernetes,
> consultando el estado real de la plataforma y los runbooks del equipo.

Proyecto de práctica para aprender **Platform Engineering** e **AI Engineering**
modernos, construyendo una solución end-to-end sobre un problema real.

---

## Tabla de contenidos

1. [Conceptos fundamentales](#1-conceptos-fundamentales)
2. [El problema](#2-el-problema)
3. [La solución](#3-la-solución)
4. [Cómo lo resuelve (flujo de diagnóstico)](#4-cómo-lo-resuelve-flujo-de-diagnóstico)
5. [Arquitectura](#5-arquitectura)
6. [Tecnologías](#6-tecnologías)
7. [Estructura del proyecto](#7-estructura-del-proyecto)
8. [Roadmap de implementación](#8-roadmap-de-implementación)
9. [Requisitos previos](#9-requisitos-previos)

---

## 1. Conceptos fundamentales

Antes de construir, es importante entender los conceptos sobre los que se apoya
el proyecto. Están divididos en dos mundos que convergen aquí.

### 1.1 Platform Engineering

**Platform Engineering** es la disciplina de construir y mantener plataformas
internas (*Internal Developer Platforms*, IDP) que permiten a los equipos de
desarrollo trabajar con infraestructura compleja (Kubernetes, CI/CD, cloud) de
forma self-service, sin necesidad de ser expertos en ella. El objetivo es
reducir la **carga cognitiva** del desarrollador.

- **Internal Developer Platform (IDP)**: el "producto" que el equipo de
  plataforma construye para los desarrolladores. Incluye un portal, un catálogo
  de servicios, plantillas estándar y automatización.
- **Golden Path**: el camino recomendado y pre-aprobado para hacer algo (por
  ejemplo, crear un microservicio nuevo). Es una plantilla que ya incluye las
  mejores prácticas del equipo: estructura del código, CI/CD, observabilidad.
- **GitOps**: modelo operativo donde el estado deseado de la infraestructura y
  las aplicaciones vive en Git. Una herramienta (ArgoCD) sincroniza
  continuamente el cluster con lo que dice el repositorio. Git es la única
  fuente de verdad.
- **Runbook**: documento operativo que describe cómo diagnosticar y resolver un
  problema conocido (por ejemplo, "qué hacer cuando un pod entra en
  CrashLoopBackOff").

### 1.2 AI Engineering

**AI Engineering** es la disciplina de construir aplicaciones sobre modelos de
lenguaje (LLMs): no entrenar modelos, sino integrarlos en sistemas reales con
herramientas, datos y guardrails.

- **LLM (Large Language Model)**: modelo de lenguaje (GPT, Claude, Llama,
  Mistral...) capaz de razonar sobre texto y generar respuestas. En este
  proyecto usamos modelos **locales** vía Ollama.
- **Agente (Agentic AI)**: un sistema donde el LLM no solo responde texto, sino
  que **decide qué acciones tomar**: llamar herramientas, consultar datos,
  iterar sobre resultados y producir una conclusión. Un agente = LLM +
  herramientas + memoria + ciclo de razonamiento.
- **Tool calling / function calling**: capacidad del LLM de invocar funciones
  externas (por ejemplo, "obtener los logs de un pod"). El LLM decide *cuándo*
  y *con qué argumentos* llamarlas.
- **MCP (Model Context Protocol)**: protocolo abierto (creado por Anthropic,
  hoy un estándar de la industria) que define cómo exponer herramientas y datos
  a un LLM de forma estandarizada. En vez de integrar cada herramienta a mano,
  se construye un **servidor MCP** que cualquier cliente/agente compatible
  puede consumir.
- **RAG (Retrieval-Augmented Generation)**: técnica para que el LLM responda
  usando información propia (documentos, runbooks) que no está en su
  entrenamiento. Los documentos se convierten en vectores (*embeddings*), se
  guardan en una base vectorial, y en cada consulta se recuperan los fragmentos
  más relevantes para incluirlos en el contexto del LLM.
- **Embeddings**: representación numérica (vector) del significado de un texto.
  Permite buscar por similitud semántica, no por palabras exactas.
- **LLMOps / Evals**: el equivalente a DevOps para sistemas con LLMs:
  trazabilidad de las llamadas, evaluación sistemática de la calidad de las
  respuestas y monitoreo en producción.

---

## 2. El problema

En equipos que trabajan con Kubernetes, los fallos de deploy y los incidentes
son parte del día a día. Cuando algo falla, el diagnóstico típico es:

1. Revisar el estado de la aplicación en ArgoCD (¿está `Degraded`? ¿falló el
   último sync?).
2. Inspeccionar el cluster con `kubectl`: estado de pods, eventos, restarts.
3. Leer logs de los contenedores buscando el error real.
4. Interpretar errores crípticos: `CrashLoopBackOff`, `OOMKilled`,
   `ImagePullBackOff`, `FailedScheduling`...
5. Buscar en la wiki del equipo si ese problema ya ocurrió y cómo se resolvió.
6. Formular una hipótesis y aplicar la remediación.

**Consecuencias:**

- Un diagnóstico toma entre 15 minutos y varias horas, según la experiencia de
  quien lo hace.
- La información está **dispersa** en 4-5 herramientas distintas.
- Requiere conocimiento experto de Kubernetes que no todo el equipo tiene.
- El conocimiento acumulado (runbooks) existe, pero nadie lo encuentra en el
  momento del incidente.

**En una frase:** diagnosticar un fallo en Kubernetes es lento, manual y
depende de expertos, aunque la información necesaria ya existe en la
plataforma.

---

## 3. La solución

**DevOps Copilot** es un agente conversacional al que le preguntas en lenguaje
natural:

> "¿Por qué falló el deploy de `payments-api`?"

Y que responde con un diagnóstico estructurado:

- **Qué pasó**: el pod está en `CrashLoopBackOff` desde el deploy de las 14:32.
- **Causa probable**: la aplicación falla al conectar a la base de datos —
  falta la variable de entorno `DB_HOST` (visible en los logs).
- **Evidencia**: extractos relevantes de los logs y eventos del cluster.
- **Remediación sugerida**: pasos concretos, citando el runbook del equipo que
  documenta este mismo caso.

El agente **no inventa** la respuesta: la construye consultando el estado real
de la plataforma (ArgoCD + Kubernetes) a través de herramientas MCP, y la
fundamenta en los runbooks del equipo recuperados con RAG.

**Por qué es una buena solución:**

- Reduce el tiempo de diagnóstico de horas a segundos.
- Democratiza el conocimiento experto: cualquier dev obtiene un diagnóstico de
  nivel senior.
- Es extensible: cada nueva herramienta MCP (costos, métricas, CI) amplía lo
  que el agente puede diagnosticar.
- Es un ejemplo real de la convergencia Platform Engineering + AI: el agente
  es un consumidor más de la plataforma interna.

---

## 4. Cómo lo resuelve (flujo de diagnóstico)

El agente sigue un ciclo de razonamiento *observe → decide → actúa*:

```
Usuario: "¿Por qué falló el deploy de payments-api?"
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ AGENTE (LangGraph + LLM local)                              │
│                                                             │
│ 1. Razona: "primero necesito el estado del deploy"          │
│    └─► MCP tool: get_argocd_app_status("payments-api")      │
│        ◄── { sync: "OutOfSync", health: "Degraded" }        │
│                                                             │
│ 2. Razona: "¿qué pods están fallando?"                      │
│    └─► MCP tool: get_pods("payments-api")                   │
│        ◄── pod payments-api-7d9f...: CrashLoopBackOff (5)   │
│                                                             │
│ 3. Razona: "necesito los logs del pod"                      │
│    └─► MCP tool: get_pod_logs(pod)                          │
│        ◄── "Error: DB_HOST is not defined"                  │
│                                                             │
│ 4. Razona: "¿hay un runbook sobre esto?"                    │
│    └─► RAG: search_runbooks("DB_HOST CrashLoopBackOff")     │
│        ◄── runbook: "Variables de entorno faltantes"        │
│                                                             │
│ 5. Sintetiza el diagnóstico final con evidencia y           │
│    remediación                                              │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
Diagnóstico estructurado: causa raíz + evidencia + remediación
```

Puntos clave del flujo:

- **El LLM decide el orden y las herramientas**: no es un script rígido; el
  agente adapta la investigación según lo que va encontrando.
- **MCP desacopla al agente de la plataforma**: el agente solo conoce la
  interfaz MCP; las herramientas viven en un servidor independiente.
- **RAG aporta el conocimiento del equipo**: el diagnóstico cita runbooks
  reales, no solo conocimiento genérico del modelo.
- **Todo queda trazado**: cada decisión y llamada a herramienta se registra en
  Langfuse para evaluar y mejorar el agente.

---

## 5. Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                        USUARIO (dev)                             │
│                    pregunta en lenguaje natural                  │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  AGENTE                                                          │
│  LangGraph (ciclo de razonamiento) + Ollama (LLM local)          │
│  Langfuse (trazas y evaluación)                                  │
└───────────────┬──────────────────────────────┬───────────────────┘
                │ MCP (stdio)                  │ RAG
                ▼                              ▼
┌───────────────────────────────┐   ┌──────────────────────────────┐
│  SERVIDOR MCP PROPIO          │   │  BASE VECTORIAL (Qdrant)     │
│  - get_argocd_app_status      │   │  - embeddings de runbooks    │
│  - get_pods / get_pod_logs    │   │  - búsqueda semántica        │
│  - get_k8s_events             │   └──────────────┬───────────────┘
│  - describe_service           │                  │
└───────────────┬───────────────┘                  │ indexa
                │                                  ▼
                ▼                        ┌──────────────────────────┐
┌───────────────────────────────┐        │  RUNBOOKS (Markdown)     │
│  CLUSTER kind (Kubernetes)    │        │  documentados en         │
│  - ArgoCD (GitOps)            │        │  Backstage TechDocs      │
│  - app sana de ejemplo        │        └──────────────────────────┘
│  - app "rota" de ejemplo      │
│  - Backstage (catálogo/IDP)   │
└───────────────────────────────┘
```

---

## 6. Tecnologías

Todas son **open source o gratuitas** para este proyecto. Costo total: $0.

### 6.1 Plataforma (Platform Engineering)

| Tecnología | Rol en el proyecto | Por qué |
|---|---|---|
| **Kubernetes (kind)** | Cluster local donde viven las apps de ejemplo | kind corre un cluster real dentro de Docker; es el estándar para desarrollo local |
| **ArgoCD** | GitOps: sincroniza los manifiestos desde Git al cluster | Estándar de facto de GitOps; su API expone el estado de los deploys (clave para el diagnóstico) |
| **Backstage** | Portal del IDP: catálogo de servicios + TechDocs (runbooks) | El portal de plataforma interna más adoptado (CNCF) |
| **Helm** | Empaquetado de los manifiestos de ejemplo | Estándar para desplegar apps en Kubernetes |

### 6.2 Agente (AI Engineering)

| Tecnología | Rol en el proyecto | Por qué |
|---|---|---|
| **MCP (Model Context Protocol)** | Protocolo entre el agente y las herramientas de la plataforma | Estándar abierto y el patrón dominante para tool-use; habilidad muy demandada |
| **LangGraph** | Orquestación del agente (ciclo razonar → actuar → observar) | Framework de agentes más usado en producción; control explícito del flujo |
| **Ollama** | Servir el LLM localmente (Llama 3.1 / Qwen2.5) | $0 de costo, datos privados, ideal para práctica |
| **RAG + embeddings** | Recuperación de runbooks relevantes | Fundamenta las respuestas en documentación real del equipo |
| **Qdrant** | Base vectorial (corre en Docker) | Ligera, open source, fácil de self-hostear |
| **Langfuse** | Trazabilidad y evaluación del agente (LLMOps) | Open source y self-hosteable; permite ver cada decisión del agente |

### 6.3 Lenguaje y tooling

| Tecnología | Rol |
|---|---|
| **Python 3.11+** | Lenguaje del servidor MCP y del agente |
| **uv / pip** | Gestión de dependencias Python |
| **Docker** | Contenedores para Qdrant, Langfuse y kind |
| **Git + GitHub** | Fuente de verdad para GitOps |

---

## 7. Estructura del proyecto

```
mcp/
├── README.md                  # este documento
├── docs/
│   └── runbooks/              # runbooks del equipo (fuente del RAG)
├── platform/
│   ├── kind/                  # configuración del cluster local
│   ├── argocd/                # instalación y ApplicationSets de ArgoCD
│   └── apps/
│       ├── healthy-app/       # app de ejemplo que funciona
│       └── broken-app/        # app que falla a propósito (casos de prueba)
├── mcp-server/                # servidor MCP propio (Python)
│   └── src/                   # herramientas: argocd, kubernetes
├── agent/                     # agente LangGraph + RAG
└── backstage/                 # catálogo y TechDocs
```

---

## 8. Roadmap de implementación

- [x] **Fase 1 — Infraestructura**: cluster kind + ArgoCD + apps de ejemplo
      (una sana, una rota con fallos típicos: env var faltante, OOM,
      ImagePullBackOff).
- [ ] **Fase 2 — Servidor MCP**: herramientas `get_argocd_app_status`,
      `get_pods`, `get_pod_logs`, `get_k8s_events`, probadas contra el cluster.
- [ ] **Fase 3 — Agente básico**: LangGraph + Ollama consumiendo el servidor
      MCP; primer diagnóstico end-to-end.
- [ ] **Fase 4 — RAG de runbooks**: documentos en Markdown → embeddings →
      Qdrant → herramienta `search_runbooks` del agente. Backstage con el
      catálogo y TechDocs.
- [ ] **Fase 5 — LLMOps**: trazas con Langfuse y un set de evaluaciones
      (preguntas con diagnóstico esperado) para medir la calidad del agente.

---

## 9. Requisitos previos

- **Docker Desktop** instalado y corriendo (necesario para kind y Qdrant).
- **Python 3.11+**.
- **kubectl** y **kind** (se instalan en la Fase 1).
- **Ollama** (se instala en la Fase 3).
- 16 GB de RAM recomendados (el LLM local y el cluster comparten recursos).
