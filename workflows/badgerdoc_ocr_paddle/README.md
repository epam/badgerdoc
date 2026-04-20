## Install MLX-VLM for inference of VLMs on Mac using MLX
```bash
pip install -U mlx-vlm
```

## To start mlx server locally run
```bash
mlx_vlm.server --port 11435 --model mlx-community/PaddleOCR-VL-1.5-bf16
```

## To send test request
```bash
curl http://localhost:11435/health
```
