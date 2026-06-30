"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

# Resolve project root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "")
        if not username:
            print("❌ USERNAME_LANGSMITH_HUB não configurada no .env")
            return False

        full_name = f"{username}/{prompt_name}"

        # Build ChatPromptTemplate from YAML messages
        messages_data = prompt_data.get("messages", [])
        template_messages = []

        for msg in messages_data:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                template_messages.append(
                    SystemMessagePromptTemplate.from_template(content)
                )
            else:
                template_messages.append(
                    HumanMessagePromptTemplate.from_template(content)
                )

        prompt_template = ChatPromptTemplate.from_messages(template_messages)

        # Push to LangSmith Hub
        tags = prompt_data.get("techniques", [])
        description = prompt_data.get("description", "")

        print(f"   Fazendo push para: {full_name}")
        print(f"   Tags: {tags}")
        print(f"   Descrição: {description}")

        hub.push(
            full_name,
            prompt_template,
            tags=tags,
            new_repo_description=description,
            new_repo_is_public=True,
        )

        print(f"   ✅ Push realizado com sucesso: {full_name}")
        return True

    except Exception as e:
        print(f"   ❌ Erro ao fazer push: {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    # Check required top-level fields
    required_fields = ["name", "version", "description", "messages"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    # Check messages structure
    messages = prompt_data.get("messages", [])
    if not messages:
        errors.append("Nenhuma mensagem definida")
    else:
        has_system = any(m.get("role") == "system" for m in messages)
        if not has_system:
            errors.append("Faltando mensagem com role 'system'")

        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            if not content.strip():
                errors.append(f"Mensagem {i} tem conteúdo vazio")
            if "[TODO]" in content or "[todo]" in content.lower():
                errors.append(f"Mensagem {i} ainda contém [TODO]")

    # Check techniques
    techniques = prompt_data.get("techniques", [])
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    # Load prompt YAML
    yaml_path = str(PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml")
    print(f"Carregando prompt de: {yaml_path}")

    prompt_data = load_yaml(yaml_path)
    if prompt_data is None:
        print(f"❌ Não foi possível carregar: {yaml_path}")
        return 1

    print(f"   ✓ Prompt carregado: {prompt_data.get('name', 'N/A')}")

    # Validate prompt
    print("\nValidando prompt...")
    is_valid, errors = validate_prompt(prompt_data)

    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("   ✓ Prompt válido")

    # Push to LangSmith
    print("\nFazendo push para o LangSmith Hub...")
    prompt_name = prompt_data.get("name", "bug_to_user_story_v2")

    success = push_prompt_to_langsmith(prompt_name, prompt_data)

    if success:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "")
        print(f"\n✅ Push concluído com sucesso!")
        print(f"   Verifique em: https://smith.langchain.com/hub/{username}/{prompt_name}")
        return 0
    else:
        print("\n❌ Falha no push do prompt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
