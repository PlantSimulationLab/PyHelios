"""Decoded normal and bump maps (helios-core 1.3.97).

:class:`NormalMapTexels` is the Python view of ``helios::NormalMapTexels``: the unit
tangent-space normals decoded from a normal or bump map image. Instances are returned by
:meth:`Context.getMaterialNormalMapTexels`, :meth:`Context.getNormalMapTexels` and
:meth:`Global.decodeNormalMapImage`; they are not constructed directly.
"""

from typing import Tuple

import numpy as np

from .wrappers import UContextWrapper as context_wrapper
from .wrappers.DataTypes import NormalMapKind, vec2, vec3


class NormalMapTexels:
    """Tangent-space surface normals decoded from a normal or bump map image.

    The tangent space is that of OpenGL, glTF and Blender: +x points along increasing u (to
    the right in the image), +y along increasing v (up in the image), and +z along the
    primitive's surface normal. Each texel stores the x and y components of a unit normal with
    non-negative z as signed 16-bit normalized integers; z is reconstructed. The strength and
    green-channel flip given when decoding are already applied.

    The object holds a reference to the native decoded data, which stays valid after the
    Context that produced it clears its cache or is destroyed.
    """

    def __init__(self, handle):
        if not handle:
            raise RuntimeError("NormalMapTexels requires a native handle; obtain one from Context.getNormalMapTexels(), "
                               "Context.getMaterialNormalMapTexels() or Global.decodeNormalMapImage().")
        self._handle = handle
        kind, strength, flip_green, width, height = context_wrapper.getNormalMapTexelsInfoWrapper(handle)
        self._file = context_wrapper.getNormalMapTexelsFileWrapper(handle)
        self._kind = NormalMapKind(kind)
        self._strength = strength
        self._flip_green = flip_green
        self._resolution = (width, height)

    def __del__(self):
        handle = getattr(self, '_handle', None)
        if handle:
            self._handle = None
            try:
                context_wrapper.destroyNormalMapTexelsWrapper(handle)
            except Exception:
                # Interpreter shutdown may already have torn down ctypes; nothing else can be done here.
                pass

    def __repr__(self) -> str:
        return (f"NormalMapTexels(file={self._file!r}, kind={self._kind.name}, strength={self._strength}, "
                f"flip_green={self._flip_green}, resolution={self._resolution})")

    @property
    def file(self) -> str:
        """Image file the normals were decoded from (resolved path)."""
        return self._file

    @property
    def kind(self) -> NormalMapKind:
        """Kind of image the normals were decoded from."""
        return self._kind

    @property
    def strength(self) -> float:
        """Strength applied when decoding."""
        return self._strength

    @property
    def flip_green(self) -> bool:
        """Whether the green channel was flipped when decoding (DirectX convention)."""
        return self._flip_green

    @property
    def resolution(self) -> Tuple[int, int]:
        """``(width, height)`` of the image in texels."""
        return self._resolution

    @property
    def xy(self) -> np.ndarray:
        """Copy of the stored x and y components as an int16 array of shape ``(height, width, 2)``.

        Rows run from the top of the image. Divide by 32767 for the components in [-1, 1].
        """
        width, height = self._resolution
        return context_wrapper.getNormalMapTexelsXYWrapper(self._handle).reshape(height, width, 2)

    def getNormal(self, column: int, row_from_top: int) -> vec3:
        """Unit normal of one texel.

        Args:
            column: Column of the texel, from the left of the image
            row_from_top: Row of the texel, from the top of the image

        Returns:
            Unit tangent-space normal, with z >= 0

        Raises:
            ValueError: If the indices are not ints
            HeliosError: If the texel lies outside the image
        """
        for name, value in (("column", column), ("row_from_top", row_from_top)):
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
                raise ValueError(f"{name} must be an int, got {type(value).__name__}")
        return vec3(*context_wrapper.getNormalMapTexelsNormalWrapper(self._handle, int(column), int(row_from_top)))

    def _sample(self, uv, bilinear: bool, name: str):
        if isinstance(uv, vec2):
            if not (np.isfinite(uv.x) and np.isfinite(uv.y)):
                raise ValueError(f"{name}: uv coordinates must be finite")
            out = context_wrapper.sampleNormalMapTexelsWrapper(self._handle, np.array([uv.x, uv.y], dtype=np.float32), 1, bilinear)
            return vec3(float(out[0, 0]), float(out[0, 1]), float(out[0, 2]))
        array = np.ascontiguousarray(uv, dtype=np.float32)
        if array.ndim != 2 or array.shape[1] != 2:
            raise ValueError(f"{name}: uv must be a vec2 or an (N, 2) array of (u,v) coordinates, got shape {array.shape}")
        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name}: uv coordinates must be finite")
        return context_wrapper.sampleNormalMapTexelsWrapper(self._handle, array.reshape(-1), array.shape[0], bilinear)

    def sampleNearest(self, uv):
        """Unit normal of the texel containing a (u,v) coordinate.

        Uses the texel convention of transparency masks and spectral class maps: column
        floor((W-1)u) and row floor((H-1)(1-v)) from the top, clamped to the image.

        Args:
            uv: A vec2, or an (N, 2) array of (u,v) coordinates

        Returns:
            A vec3 for a vec2 argument, or an (N, 3) float32 array of unit normals
        """
        return self._sample(uv, False, "sampleNearest")

    def sampleBilinear(self, uv):
        """Unit normal bilinearly interpolated at a (u,v) coordinate.

        The four texels around (u,v) are blended by distance to their centres, coordinates
        beyond the outermost centres take the edge texels, and the result is renormalized.

        Args:
            uv: A vec2, or an (N, 2) array of (u,v) coordinates

        Returns:
            A vec3 for a vec2 argument, or an (N, 3) float32 array of unit normals
        """
        return self._sample(uv, True, "sampleBilinear")

    def getMemoryBytes(self) -> int:
        """Size of the native texel data in bytes."""
        return context_wrapper.getNormalMapTexelsMemoryBytesWrapper(self._handle)
