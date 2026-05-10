from pathlib import Path
from fastapi.responses import HTMLResponse

from app.models import ExampleBundle, ExampleInfo


EXAMPLE_DIR = Path("data/examples")
EXAMPLE_FILE_DIR = Path("data/example_files")
DEMO_PAGE_DIR = Path("data/demo_pages")


EXAMPLES = [
    ExampleInfo(
        example_id="weak_recursion",
        title="递归停止条件反复出错",
        description="真实学习日志：递归题多次因为 base case 和停止条件失败。",
    ),
    ExampleInfo(
        example_id="avoided_dynamic_programming",
        title="动态规划一直回避",
        description="真实学习日志：课程要求 DP，但学生一直跳过状态定义练习。",
    ),
    ExampleInfo(
        example_id="decaying_binary_search",
        title="二分查找边界遗忘",
        description="真实学习日志：之前掌握二分，隔了几周后开始犹豫边界更新。",
    ),
]


def list_examples() -> list[ExampleInfo]:
    return EXAMPLES


def get_example_content(example_id: str) -> tuple[str, str]:
    match = next((example for example in EXAMPLES if example.example_id == example_id), None)
    if not match:
        raise KeyError(example_id)
    path = EXAMPLE_DIR / f"{example_id}.md"
    return match.title, path.read_text(encoding="utf-8")


def get_example_bundle(example_id: str) -> ExampleBundle:
    title, content = get_example_content(example_id)
    file_path = EXAMPLE_FILE_DIR / f"{example_id}_upload.md"
    return ExampleBundle(
        example_id=example_id,
        title=title,
        content=content,
        file_name=file_path.name,
        file_content=file_path.read_text(encoding="utf-8"),
    )


def get_demo_page(example_id: str) -> HTMLResponse:
    match = next((example for example in EXAMPLES if example.example_id == example_id), None)
    if not match:
        raise KeyError(example_id)
    path = DEMO_PAGE_DIR / f"{example_id}.html"
    return HTMLResponse(path.read_text(encoding="utf-8"))
