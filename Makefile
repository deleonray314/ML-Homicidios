# ============================================================================
# Makefile - ML-Homicidios
# Comandos comunes para desarrollo y despliegue
# ============================================================================

.PHONY: help setup install clean test lint format run-pipeline train dashboard docker-build docker-up docker-down

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
STREAMLIT := streamlit

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------
help:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║          ML-Homicidios - Comandos Disponibles              ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make setup          - Setup completo del proyecto"
	@echo "  make install        - Instalar dependencias"
	@echo ""
	@echo "🧹 Cleaning:"
	@echo "  make clean          - Limpiar archivos temporales"
	@echo "  make clean-data     - Limpiar datos (¡cuidado!)"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test           - Ejecutar tests"
	@echo "  make test-cov       - Tests con cobertura"
	@echo "  make lint           - Linting del código"
	@echo "  make format         - Formatear código"
	@echo ""
	@echo "🔄 Data Pipeline:"
	@echo "  make extract        - Extraer datos de API"
	@echo "  make etl            - Ejecutar pipeline ETL completo"
	@echo "  make run-pipeline   - Pipeline completo (extract + ETL)"
	@echo ""
	@echo "🤖 Machine Learning:"
	@echo "  make train          - Entrenar modelos"
	@echo "  make evaluate       - Evaluar modelos"
	@echo "  make predict        - Generar predicciones"
	@echo ""
	@echo "📊 Dashboard:"
	@echo "  make dashboard      - Lanzar dashboard Streamlit"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-build   - Construir imágenes Docker"
	@echo "  make docker-up      - Levantar servicios Docker"
	@echo "  make docker-down    - Detener servicios Docker"
	@echo ""

# ----------------------------------------------------------------------------
# Setup & Installation
# ----------------------------------------------------------------------------
setup: install create-dirs create-env
	@echo "✅ Setup completo!"

install:
	@echo "📦 Instalando dependencias..."
	$(PIP) install -r requirements.txt

create-dirs:
	@echo "📁 Creando directorios..."
	@mkdir -p data/raw data/processed data/models logs

create-env:
	@if [ ! -f .env ]; then \
		echo "📝 Creando archivo .env desde template..."; \
		cp .env.example .env; \
		echo "⚠️  Recuerda configurar tus credenciales en .env"; \
	else \
		echo "✅ Archivo .env ya existe"; \
	fi

# ----------------------------------------------------------------------------
# Cleaning
# ----------------------------------------------------------------------------
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache/
	@echo "✅ Limpieza completada"

clean-data:
	@echo "⚠️  ¿Estás seguro de eliminar todos los datos? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf data/raw/* data/processed/* data/models/*
	@echo "✅ Datos eliminados"

# ----------------------------------------------------------------------------
# Testing & Quality
# ----------------------------------------------------------------------------
test:
	@echo "🧪 Ejecutando tests..."
	$(PYTEST) tests/ -v

test-cov:
	@echo "🧪 Ejecutando tests con cobertura..."
	$(PYTEST) tests/ --cov=src --cov-report=html --cov-report=term
	@echo "📊 Reporte de cobertura en: htmlcov/index.html"

lint:
	@echo "🔍 Ejecutando linting..."
	flake8 src/ app/ tests/
	mypy src/

format:
	@echo "✨ Formateando código..."
	black src/ app/ tests/
	isort src/ app/ tests/
	@echo "✅ Código formateado"

# ----------------------------------------------------------------------------
# Data Pipeline
# ----------------------------------------------------------------------------
extract:
	@echo "📥 Extrayendo datos de API..."
	$(PYTHON) -m src.data_ingestion.api_client

etl:
	@echo "🔄 Ejecutando pipeline ETL..."
	$(PYTHON) -m src.etl.extract
	$(PYTHON) -m src.etl.transform
	$(PYTHON) -m src.etl.load

run-pipeline: extract etl
	@echo "✅ Pipeline completo ejecutado"

# ----------------------------------------------------------------------------
# Machine Learning
# ----------------------------------------------------------------------------
train:
	@echo "🤖 Entrenando modelos..."
	$(PYTHON) -m src.models.train

evaluate:
	@echo "📊 Evaluando modelos..."
	$(PYTHON) -m src.models.evaluate

predict:
	@echo "🔮 Generando predicciones..."
	$(PYTHON) -m src.models.predict

# ----------------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------------
dashboard:
	@echo "📊 Lanzando dashboard Streamlit..."
	$(STREAMLIT) run app/streamlit_app.py

# ----------------------------------------------------------------------------
# Docker
# ----------------------------------------------------------------------------
docker-build:
	@echo "🐳 Construyendo imágenes Docker..."
	docker-compose build

docker-up:
	@echo "🐳 Levantando servicios Docker..."
	docker-compose up -d
	@echo "✅ Servicios corriendo en background"

docker-down:
	@echo "🐳 Deteniendo servicios Docker..."
	docker-compose down

docker-logs:
	docker-compose logs -f

# ----------------------------------------------------------------------------
# Development
# ----------------------------------------------------------------------------
dev: format lint test
	@echo "✅ Checks de desarrollo completados"

# ----------------------------------------------------------------------------
# Full Pipeline (para producción)
# ----------------------------------------------------------------------------
full-pipeline: run-pipeline train evaluate
	@echo "✅ Pipeline completo ejecutado: datos + entrenamiento + evaluación"
