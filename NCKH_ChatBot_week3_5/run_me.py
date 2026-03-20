import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "project_root"
VENV_DIR = BASE_DIR / "venv"
CONFIG_FILE = BASE_DIR / "config" / "tenants.json"
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
ENTRY_CANDIDATES = [
    SOURCE_DIR / "main.py",
    BASE_DIR / "main.py",
    BASE_DIR / "app.py",
]
REQUIRED_MODULAR_FILES = [
    SOURCE_DIR / "main.py",
    SOURCE_DIR / "config.py",
    SOURCE_DIR / "models.py",
    SOURCE_DIR / "utils.py",
    SOURCE_DIR / "memory_store.py",
    SOURCE_DIR / "ingestion.py",
    SOURCE_DIR / "runtime_manager.py",
    SOURCE_DIR / "retrieval.py",
    SOURCE_DIR / "tools.py",
    SOURCE_DIR / "prompt_builder.py",
    SOURCE_DIR / "llm_service.py",
]


def run_command(
    cmd: List[str],
    extra_env: Dict[str, str] | None = None,
    allow_fail: bool = False,
    cwd: Path | None = None,
) -> bool:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    try:
        subprocess.check_call(cmd, cwd=str(cwd or BASE_DIR), env=env)
    except subprocess.CalledProcessError as exc:
        if allow_fail:
            return False
        print(f"LỖI THỰC THI: {exc}")
        raise
    return True


def get_python_paths() -> Tuple[Path, Path]:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe", VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "python", VENV_DIR / "bin" / "pip"


def detect_entry_file() -> Path:
    for candidate in ENTRY_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Không tìm thấy file khởi động. Cần có project_root/main.py, main.py hoặc app.py."
    )


def check_modular_layout() -> None:
    present = [path for path in REQUIRED_MODULAR_FILES if path.exists()]
    missing = [path for path in REQUIRED_MODULAR_FILES if not path.exists()]

    if present and not missing:
        print("--- Đã phát hiện đầy đủ cấu trúc modular tuần 1 ---")
        return

    if present and missing:
        print("--- Phát hiện bản modular chưa đầy đủ ---")
        print("Các file còn thiếu:")
        for path in missing:
            print(f"    - {path.relative_to(BASE_DIR)}")
        print("Sẽ thử chạy theo file entry hiện có nếu hợp lệ.")


def ensure_basic_dirs() -> None:
    for rel in ["data", "storage", "memory", "config", "data/shared/files", "data/tenants"]:
        (BASE_DIR / rel).mkdir(parents=True, exist_ok=True)


def ensure_venv() -> None:
    if not VENV_DIR.exists():
        print(f"--- [1/5] Đang tạo môi trường ảo (venv) cho {os.name}... ---")
        run_command([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print("--- [1/5] Venv đã tồn tại, bỏ qua tạo mới. ---")


def ensure_requirements() -> None:
    python_exe, _ = get_python_paths()
    pip_env = {
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_DEFAULT_TIMEOUT": "100",
    }

    print("--- [2/5] Đang kiểm tra và cập nhật thư viện AI... ---")
    run_command(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip", "--retries", "10"],
        extra_env=pip_env,
        allow_fail=True,
    )
    run_command(
        [
            str(python_exe),
            "-m",
            "pip",
            "install",
            "-r",
            str(BASE_DIR / "requirements.txt"),
            "--retries",
            "10",
            "--timeout",
            "100",
        ],
        extra_env=pip_env,
    )


def check_ollama_alive() -> bool:
    import urllib.request

    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


def load_models_from_config() -> List[str]:
    models = {DEFAULT_MODEL}
    if CONFIG_FILE.exists():
        try:
            configs = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            for conf in configs.values():
                model_name = conf.get("model_name")
                if model_name:
                    models.add(model_name)
        except Exception:
            pass
    return sorted(models)


def ensure_ollama_models() -> None:
    print("--- [3/5] Đang kiểm tra danh sách mô hình AI (Ollama)... ---")

    if not check_ollama_alive():
        print("(!) CẢNH BÁO: Không kết nối được tới Ollama Server.")
        print("    Vui lòng mở Ollama trước khi chat.")
        if os.name == "nt":
            try:
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                print("    Đã thử khởi động 'ollama serve' trong cửa sổ mới.")
            except Exception:
                pass
        return

    for model in load_models_from_config():
        print(f"    + Đang kiểm tra/tải mô hình: {model}")
        run_command(["ollama", "pull", model], allow_fail=True)


def validate_entry(entry_file: Path) -> None:
    print(f"--- [4/5] File khởi động được chọn: {entry_file.relative_to(BASE_DIR)} ---")
    if entry_file == SOURCE_DIR / "main.py":
        check_modular_layout()


def start_app() -> None:
    python_exe, _ = get_python_paths()
    entry_file = detect_entry_file()
    validate_entry(entry_file)
    print("--- [5/5] HỆ THỐNG SẴN SÀNG! ĐANG KHỞI ĐỘNG APP... ---")
    run_command([str(python_exe), str(entry_file)], cwd=BASE_DIR)


if __name__ == "__main__":
    try:
        ensure_basic_dirs()
        ensure_venv()
        ensure_requirements()
        ensure_ollama_models()
        start_app()
    except KeyboardInterrupt:
        print("\nĐã dừng tiến trình theo yêu cầu.")
    except Exception as exc:
        print(f"\n[LỖI NGHIÊM TRỌNG]: {exc}")
        try:
            input("Nhấn Enter để thoát...")
        except EOFError:
            pass
         
