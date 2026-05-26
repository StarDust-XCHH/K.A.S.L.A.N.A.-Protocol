"""Check whether the project conda environment can use NVIDIA CUDA via PyTorch."""

from __future__ import annotations

import sys


def main() -> None:
    try:
        import torch
    except ImportError:
        print("PyTorch is not installed in this environment.")
        raise SystemExit(1) from None

    print(f"torch.__version__: {torch.__version__}")
    print(f"torch.version.cuda: {torch.version.cuda}")

    cuda_available = torch.cuda.is_available()
    print(f"torch.cuda.is_available(): {cuda_available}")
    if not cuda_available:
        print("PyTorch did not detect an NVIDIA CUDA GPU in this environment.")
        raise SystemExit(1)

    device_index = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(device_index)
    total_gib = props.total_memory / 1024**3
    print(f"CUDA device index: {device_index}")
    print(f"CUDA device name: {torch.cuda.get_device_name(device_index)}")
    print(f"CUDA total memory: {total_gib:.2f} GiB")
    print(f"CUDA compute capability: {props.major}.{props.minor}")

    tensor = torch.ones(1, device="cuda")
    print(f"CUDA smoke tensor: {tensor.item():.0f}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"GPU check failed: {exc}", file=sys.stderr)
        raise
