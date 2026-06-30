"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Resolve project root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt do LangSmith Hub e salva localmente como YAML.
    Se o prompt não estiver disponível no Hub, usa o arquivo local existente.

    Returns:
        True se sucesso, False caso contrário
    """
    prompt_name = "leonanluppi/bug_to_user_story_v1"
    output_path = str(PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml")

    print(f"Fazendo pull do prompt: {prompt_name}")

    try:
        prompt = hub.pull(prompt_name)
        print(f"   ✓ Prompt carregado com sucesso do Hub")

        messages = []
        for msg in prompt.messages:
            class_name = msg.__class__.__name__
            if "System" in class_name:
                role = "system"
            elif "Human" in class_name:
                role = "user"
            else:
                role = "assistant"

            if hasattr(msg, 'prompt') and hasattr(msg.prompt, 'template'):
                content = msg.prompt.template
            elif hasattr(msg, 'content'):
                content = msg.content
            else:
                content = str(msg)

            messages.append({"role": role, "content": content})

        data = {
            "name": "bug_to_user_story_v1",
            "version": "1.0",
            "description": "Original low-quality prompt pulled from LangSmith Hub",
            "messages": messages,
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if save_yaml(data, output_path):
            print(f"   ✓ Prompt salvo em: {output_path}")
            return True
        else:
            print(f"   ❌ Erro ao salvar prompt")
            return False

    except Exception as e:
        print(f"   ⚠️  Não foi possível fazer pull do Hub: {e}")
        return _fallback_from_local(output_path)


def _fallback_from_local(output_path: str) -> bool:
    """
    Fallback: converte o arquivo v1 local (formato legado) para o formato
    padronizado com messages, caso o Hub esteja inacessível.

    Returns:
        True se o arquivo local existir e for convertido, False caso contrário
    """
    from utils import load_yaml

    local_path = str(PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml")

    if not Path(local_path).exists():
        print(f"   ❌ Arquivo local não encontrado: {local_path}")
        return False

    print(f"   ➜ Usando arquivo local existente: {local_path}")

    existing = load_yaml(local_path)
    if existing is None:
        return False

    # Se já está no formato padronizado (tem campo 'messages'), nada a fazer
    if "messages" in existing:
        print(f"   ✓ Arquivo local já está no formato padronizado")
        return True

    # Converter do formato legado (bug_to_user_story_v1.system_prompt) para
    # o formato padronizado com messages
    v1 = existing.get("bug_to_user_story_v1", existing)
    system_prompt = v1.get("system_prompt", "")
    user_prompt = v1.get("user_prompt", "{bug_report}")

    data = {
        "name": "bug_to_user_story_v1",
        "version": "1.0",
        "description": "Original low-quality prompt (from local file, Hub unavailable)",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    if save_yaml(data, output_path):
        print(f"   ✓ Prompt local convertido e salvo em: {output_path}")
        return True

    return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return 1

    success = pull_prompts_from_langsmith()

    if success:
        print("\n✅ Pull concluído com sucesso!")
        return 0
    else:
        print("\n❌ Falha no pull dos prompts")
        return 1


if __name__ == "__main__":
    sys.exit(main())
