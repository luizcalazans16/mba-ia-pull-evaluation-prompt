"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = "prompts/bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    return load_prompts(PROMPT_PATH)


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    for msg in prompt_data.get("messages", []):
        if msg.get("role") == "system":
            return msg.get("content", "")
    return None


class TestPrompts:
    def test_prompt_has_system_prompt(self, system_prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert system_prompt is not None, "Nenhuma mensagem com role 'system' encontrada"
        assert len(system_prompt.strip()) > 0, "O system prompt está vazio"

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        keywords = [
            "you are",
            "você é",
            "senior",
            "product manager",
            "specialist",
            "especialista",
        ]
        prompt_lower = system_prompt.lower()
        assert any(
            k in prompt_lower for k in keywords
        ), f"Nenhuma definição de persona encontrada. Esperado uma das keywords: {keywords}"

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        keywords = [
            "markdown",
            "user story",
            "as a",
            "como um",
            "acceptance criteria",
            "critérios",
            "critérios de aceitação",
        ]
        prompt_lower = system_prompt.lower()
        assert any(
            k in prompt_lower for k in keywords
        ), f"Nenhuma menção a formato de saída encontrada. Esperado uma das keywords: {keywords}"

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        keywords = ["example", "exemplo", "bug report:", "user story:"]
        prompt_lower = system_prompt.lower()
        count = sum(1 for k in keywords if k in prompt_lower)
        assert count >= 2, (
            f"Poucos indicadores de exemplos Few-shot encontrados ({count}). "
            f"Esperado pelo menos 2 das keywords: {keywords}"
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for msg in prompt_data.get("messages", []):
            content = msg.get("content", "")
            assert "[TODO]" not in content, f"Encontrado [TODO] na mensagem com role '{msg.get('role')}'"
            assert "[todo]" not in content.lower(), f"Encontrado [todo] na mensagem com role '{msg.get('role')}'"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques", [])
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}. "
            f"Técnicas listadas: {techniques}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
