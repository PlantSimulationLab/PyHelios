"""
PyHelios Runtime GPU Detection Module

This module provides runtime GPU detection capabilities for PyHelios testing and validation.
Detection fails fast rather than falling back silently.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def is_gpu_runtime_available() -> bool:
    """
    Check if GPU runtime (CUDA/OptiX) is available for PyHelios.

    Returns:
        bool: True if GPU runtime is available, False otherwise

    Raises:
        RuntimeError: If GPU detection system is unavailable (fail-fast)
    """
    try:
        from pyhelios.config.dependency_resolver import PluginDependencyResolver
        resolver = PluginDependencyResolver()
        return resolver._check_cuda()
    except ImportError as e:
        raise RuntimeError(
            f"GPU detection system unavailable: {e}. "
            f"This indicates a PyHelios installation or import issue."
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"GPU detection failed: {e}. "
            f"Check CUDA installation and GPU drivers."
        ) from e


def get_gpu_runtime_info() -> Dict[str, Any]:
    """
    Get detailed GPU runtime information for PyHelios.

    Returns:
        Dict containing GPU runtime status and details

    Raises:
        RuntimeError: If GPU detection system is unavailable (fail-fast)
    """
    try:
        from pyhelios.config.dependency_resolver import PluginDependencyResolver
        resolver = PluginDependencyResolver()

        cuda_available = resolver._check_cuda()

        info = {
            'cuda_available': cuda_available,
            'gpu_runtime_available': cuda_available,
        }

        if not cuda_available:
            info['error_message'] = 'CUDA/GPU not available'
            info['suggestions'] = [
                'Install NVIDIA CUDA toolkit',
                'Ensure NVIDIA GPU drivers are installed',
                'Check that nvcc is in PATH'
            ]

        return info

    except ImportError as e:
        raise RuntimeError(
            f"GPU detection system unavailable: {e}. "
            f"This indicates a PyHelios installation or import issue."
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"GPU detection failed: {e}. "
            f"Check CUDA installation and GPU drivers."
        ) from e


def validate_gpu_requirements() -> None:
    """
    Validate that GPU requirements are met for GPU-dependent operations.

    Raises:
        RuntimeError: If GPU requirements are not met (fail-fast)
    """
    if not is_gpu_runtime_available():
        gpu_info = get_gpu_runtime_info()
        error_msg = gpu_info.get('error_message', 'GPU not available')
        suggestions = gpu_info.get('suggestions', [])

        raise RuntimeError(
            f"GPU requirements not met: {error_msg}. "
            f"Required for GPU-dependent plugins (radiation, energybalance, etc.). "
            f"Solutions: {'; '.join(suggestions)}"
        )