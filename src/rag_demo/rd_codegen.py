#kevin fink
#kevin@shorecode.org
#Tue Apr 15 2026

import re
from typing import AsyncGenerator

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from rag_demo.rd_filepaths import Files
from rag_demo.rd_logging import set_logging
from rag_demo.rd_codegen_prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


class CodegenRequest(BaseModel):
    description: str
    api_key: str
    model: str = "gpt-5.4"
    confidence_threshold: float = Field(default=0.85, ge=0.5, le=1.0)
    max_iterations: int = Field(default=3, ge=1, le=10)


class CodegenResponse(BaseModel):
    code: str
    node_names: list[str]


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text.strip()


def _extract_node_names(code: str) -> list[str]:
    return re.findall(r'graph\.add_node\(\s*["\'](\w+)["\']', code)


class CodeGenerator:
    def __init__(self):
        files = Files()
        filepaths = files.get_files_list()
        self.logger = set_logging(__file__, filepaths[0])

    def _build_messages(self, request: CodegenRequest) -> list:
        user_content = USER_PROMPT_TEMPLATE.format(
            description=request.description,
            confidence_threshold=request.confidence_threshold,
            max_iterations=request.max_iterations,
            model=request.model,
        )
        return [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

    async def generate(self, request: CodegenRequest) -> CodegenResponse:
        self.logger.info(f"[CodeGenerator] generate: model={request.model}")
        llm = ChatOpenAI(
            openai_api_key=request.api_key,
            model=request.model,
            temperature=0.2,
        )
        messages = self._build_messages(request)
        result = await llm.ainvoke(messages)
        code = _strip_fences(result.content)
        node_names = _extract_node_names(code)
        self.logger.info(f"[CodeGenerator] done: {len(node_names)} nodes extracted")
        return CodegenResponse(code=code, node_names=node_names)

    async def stream_tokens(self, request: CodegenRequest) -> AsyncGenerator[str, None]:
        self.logger.info(f"[CodeGenerator] stream_tokens: model={request.model}")
        llm = ChatOpenAI(
            openai_api_key=request.api_key,
            model=request.model,
            temperature=0.2,
            streaming=True,
        )
        messages = self._build_messages(request)
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                yield token
        self.logger.info("[CodeGenerator] stream complete")
