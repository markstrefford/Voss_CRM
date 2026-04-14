from pathlib import Path

import modal

backend_dir = Path(__file__).parent

app = modal.App("voss-crm")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir(backend_dir / "app", remote_path="/root/app")
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("voss-crm-secrets")],
    scaledown_window=300,  # 5 min idle before scale-to-zero
)
@modal.asgi_app()
def fastapi_app():
    from app.main import app

    return app
