"""
PlantArchitecture Collision Avoidance -- Animated A/B Comparison

Renders a time-lapse movie of plants growing into a solid obstacle, twice from
the same random seed: once with collision avoidance disabled, once enabled.
The two runs are rendered side by side so the effect of collision avoidance is
directly visible rather than inferred from primitive counts.

Why A/B: a single animation of plants growing tells you nothing about whether
avoidance is working -- plants grow either way. Only the difference between two
otherwise-identical runs isolates what collision detection actually did.

The camera orbits a full revolution during the run so the back face of the wall
is visible; foliage growing through a barrier is only unambiguous when you can
look at the far side of it.

Configuration: soft collision avoidance only. No enableSolidObstacleAvoidance(),
no obstacle pruning -- nothing is deleted to keep the wall clear.

Why an apple tree rather than a canopy of beans:

Steering redirects growth AXES, so it can only hold an organ clear of a barrier
when that organ is small relative to the segment being steered. Bean fails that
test -- ~0.10 m trifoliate leaves fanned off comparably short internodes, so the
blades sweep across the plane however hard the axis turns. With bean, leaves are
~84% of all primitives, and getting them fully clear needed hard obstacle
avoidance layered on top plus pruning to delete the stragglers.

Apple has 0.12 m leaves on a woody structure metres across. The ratio is far
more favourable, so soft avoidance alone does the job and the demonstration
stays honest: every organ that avoids the wall does so by growing elsewhere,
not by being removed.

Reference points from the bean version, still useful when tuning:
  - inertia_weight on setSoftCollisionAvoidanceParameters() is the effective
    "strength" knob (0.0 = full avoidance, 1.0 = ignore).
    enableSolidObstacleAvoidance() has no strength argument at all; its turn
    rate is hardcoded and capped at parallel-to-the-obstacle.
  - Soft and hard avoidance are mutually exclusive for INTERNODES --
    applySolidObstacleAvoidance() runs first and the soft blend sits behind
    `else if (collision_detection_active && !obstacle_found)`
    (PlantArchitecture.cpp:1787). For PETIOLES there is no such gate (line
    1934). So when both are on, hard covers stems and soft covers leaves.
  - enable_obstacle_pruning deletes intersecting organs *and everything
    downstream of them on the shoot* (pruneSolidBoundaryCollisions, line 6073).
    Always check leaf area before crediting a low penetration figure to
    avoidance rather than to amputation.

Output (under docs/examples/output/collision_movie/, override with --outdir):
    collision_avoidance.mp4   (requires ffmpeg on PATH)
    frames_*/frame_*.jpeg     (always written)

Usage:
    python docs/examples/plantarch_collision_movie.py
    python docs/examples/plantarch_collision_movie.py --days 300 --fps 12

Requires the visualizer and plantarchitecture plugins. Rendering is headless,
so no window appears and it works over SSH.
"""

import argparse
import math
import os
import shutil
import subprocess
import sys

import numpy as np

from example_output import display_path, get_output_dir
from pyhelios import Context, PlantArchitecture, Visualizer
from pyhelios.types import vec3, vec2, int2, RGBcolor, SphericalCoord

# A single apple tree beside a wall.
#
# Apple rather than bean: steering redirects growth AXES, so it can only keep an
# organ clear of a barrier if that organ is small relative to the segment being
# steered. Bean has ~0.10 m trifoliate leaves fanned off short internodes, so
# leaf half-width is comparable to the internode length and blades sweep across
# the plane no matter how hard the axis turns. Apple has 0.12 m leaves on a
# woody structure metres across -- a far better ratio, so soft avoidance alone
# is enough and neither hard obstacle avoidance nor pruning is needed.
#
# The wall must sit INSIDE the crown's unobstructed growth envelope. Placed
# beyond its reach it is never encountered, both runs look identical, and the
# animation demonstrates nothing.
WALL_X = 0.22
# Taller than the mature tree (measured max height 1.92 m) so the crown cannot
# simply grow over the top -- foliage on the far side then means growth went
# THROUGH the wall, which is the whole point. Width is kept a little under the
# crown spread so the tree is still visible around the edges.
WALL_SIZE = vec2(1.1, 2.4)  # (span along y, height along z) once rotated upright
# Build the wall via addPatch's rotation argument rather than rotatePrimitive:
# rotatePrimitive rotates the center about the origin too, which displaces the
# patch and sinks most of it below ground.
WALL_ROTATION = SphericalCoord(1, math.pi / 2, math.pi / 2)
# Centred on the wall: this maximises the fraction of the crown that actually
# meets the barrier (offsetting along y cut measured penetration from 12% to 6%
# because less of the tree grows at the wall).
TREE_POSITION = vec3(-0.10, 0.0, 0.0)
SEED = 12345

# Apple growth is extremely unevenly distributed in time. Measured at 5-day
# resolution for this model: days 0-160 are completely static (1453 primitives,
# nothing moves), days 160-215 contain ALL of the growth (1453 -> 12041
# primitives, 1.08 m -> 1.96 m tall), and from day 215 onwards it is static
# again until the tree defoliates around day 380.
#
# Animating from day 0 therefore wastes most frames on a motionless sapling and
# flashes through the interesting part. Instead fast-forward the dormant period
# in one un-filmed step and animate only the window where something happens.
SPINUP_DAYS = 158.0  # advanced before the first frame, not filmed

# Extra frames appended after the growth window. The tree is finished growing by
# then (day ~215), so these carry the camera on past a full revolution and back
# round to the front, ending on a clear view of the completed tree instead of
# stopping mid-orbit with the wall in the way.
TAIL_FRAMES = 5

# Camera orbits one full revolution over the run so both faces of the wall are
# seen. Driven by frame index only, so both runs stay in lockstep.
ORBIT_RADIUS = 3.4
ORBIT_ELEVATION = 0.30
ORBIT_START = 2.60
ORBIT_LOOKAT = vec3(0.05, 0.0, 1.10)


def build_scene(context, collision_enabled):
    """Build an identical canopy + wall scene, toggling only collision avoidance."""
    # Identical seed in both runs, so any divergence comes from collision
    # avoidance and not from different random draws.
    context.seedRandomGenerator(SEED)

    ground = context.addPatch(center=vec3(0, 0, 0), size=vec2(9.0, 9.0),
                              color=RGBcolor(0.35, 0.25, 0.15))
    wall = context.addPatch(center=vec3(WALL_X, 0.0, 0.5 * WALL_SIZE.y),
                            size=WALL_SIZE, rotation=WALL_ROTATION,
                            color=RGBcolor(0.80, 0.78, 0.72))

    plantarch = PlantArchitecture(context)
    # Silence per-timestep progress bars and the harmless "BVH not cached"
    # warning so the per-frame progress lines below stay readable.
    try:
        plantarch.disableMessages()
    except AttributeError:
        # Older PyHelios without message control -- output will be noisier.
        pass
    plantarch.loadPlantModelFromLibrary("apple")

    # Build the tree BEFORE enabling collision detection, so both runs start
    # from a byte-identical sapling. Collision hooks fire during phytomer
    # construction (PlantArchitecture.cpp:605/661/705/1929), so a tree built
    # with avoidance already on diverges from the control at day 0 -- same seed
    # or not. Verified: identical vertex count and centroid at day 0 this way,
    # different if collision is enabled first.
    plant_ids = [plantarch.buildPlantInstanceFromLibrary(
        base_position=TREE_POSITION,
        age=0.0,
    )]

    if collision_enabled:
        plantarch.setCollisionRelevantOrgans(
            include_internodes=True,
            include_leaves=True,
            include_petioles=True,
            include_flowers=False,
            include_fruit=False,
        )
        # inertia_weight is the effective "strength" knob: 0.0 = follow the
        # collision-optimal direction entirely, 1.0 = ignore collisions.
        plantarch.setSoftCollisionAvoidanceParameters(
            view_half_angle_deg=80.0,
            look_ahead_distance=0.40,  # see the wall early enough to turn
            sample_count=256,
            inertia_weight=0.10,       # turn hard once it is seen
        )
        # Soft avoidance only -- no enableSolidObstacleAvoidance() and no
        # pruning. With apple's small leaves on long woody shoots, steering
        # alone is sufficient; nothing has to be deleted to keep the wall clear.
        plantarch.enableSoftCollisionAvoidance(enable_petiole_collision=True)

    return plantarch, {ground, wall}, plant_ids


def measure_penetration(context, environment_uuids):
    """Fraction of plant vertices that lie beyond the wall plane, and how deep.

    This is the objective check on collision avoidance. The side-by-side movie
    shows the effect; these numbers confirm it rather than relying on the eye.

    Only vertices within the wall's actual y/z extent count: the wall is
    deliberately shorter than the tree, and a branch arching over the top is
    not growing *through* anything.
    """
    half_span = 0.5 * WALL_SIZE.x
    wall_top = WALL_SIZE.y

    plant_uuids = [u for u in context.getAllUUIDs() if u not in environment_uuids]
    if not plant_uuids:
        return 0.0, 0.0

    # One native call for every vertex in the plant, rather than one per
    # primitive: this runs once per rendered frame over the whole tree. The
    # flat array is [x, y, z, x, y, z, ...], so each axis is a strided slice
    # and the whole test below vectorizes.
    flat, _offsets = context.getPrimitiveVertices(plant_uuids)
    total = flat.size // 3
    if total == 0:
        return 0.0, 0.0

    x = flat[0::3]
    y = flat[1::3]
    z = flat[2::3]

    blocked = (np.abs(y) <= half_span) & (z >= 0.0) & (z <= wall_top)
    penetrating = blocked & (x > WALL_X)

    beyond = int(np.count_nonzero(penetrating))
    max_x = float(x[penetrating].max()) if beyond else WALL_X
    return 100.0 * beyond / total, max_x


def measure_leaf_area(plantarch, plant_ids):
    """Total leaf area across the canopy.

    Reported alongside penetration so a drop in penetration that came from
    losing foliage (e.g. obstacle pruning) is distinguishable from one that
    came from steering growth around the obstacle.
    """
    return sum(plantarch.getPlantLeafArea(pid) for pid in plant_ids)


def render_run(label, collision_enabled, days, step, frame_dir, width, height):
    """Grow one scenario, writing one frame per growth step. Returns frame paths."""
    os.makedirs(frame_dir, exist_ok=True)
    for stale in os.listdir(frame_dir):
        os.remove(os.path.join(frame_dir, stale))

    frames = []
    stats = None
    with Context() as context:
        plantarch, environment_uuids, plant_ids = build_scene(
            context, collision_enabled)
        try:
            with Visualizer(width, height, headless=True) as vis:
                vis.setBackgroundColor(RGBcolor(0.92, 0.94, 0.97))
                vis.setLightingModel("phong")
                vis.hideWatermark()

                # Fast-forward the dormant period in one un-filmed step so the
                # animation opens on a tree that is about to do something.
                if SPINUP_DAYS > 0:
                    plantarch.advanceTime(SPINUP_DAYS)

                growth_frames = int(days / step)
                n_frames = growth_frames + TAIL_FRAMES
                for i in range(n_frames):
                    plantarch.advanceTime(step)

                    # Orbit the camera a full turn over the growth frames, so
                    # the far side of the wall is seen too -- foliage poking
                    # through is only unambiguous when you can look at the back
                    # of the barrier. The angle depends solely on the frame
                    # index, so both runs orbit in lockstep and the panels stay
                    # comparable.
                    #
                    # The tail frames continue past a full revolution at the
                    # same angular step, carrying the camera back around to the
                    # front so the movie ends on an unobstructed view of the
                    # finished tree rather than stopping behind the wall.
                    azimuth = ORBIT_START + 2.0 * math.pi * i / growth_frames
                    vis.setCameraPositionSpherical(
                        SphericalCoord(ORBIT_RADIUS, ORBIT_ELEVATION, azimuth),
                        ORBIT_LOOKAT,
                    )

                    # Do NOT call clearGeometry() here. The visualizer tracks the
                    # Context incrementally via dirty flags; clearing wipes its
                    # geometry while leaving the Context marked clean, so the
                    # scene silently renders empty from that point on.
                    vis.buildContextGeometry(context)
                    vis.plotUpdate()

                    path = os.path.join(frame_dir, f"frame_{i:04d}.jpeg")
                    vis.printWindow(path)
                    if not os.path.exists(path):
                        raise RuntimeError(
                            f"Frame {i} was not written to {path}. The visualizer "
                            "produced no output for this frame."
                        )
                    frames.append(path)
                    print(f"  [{label}] day {SPINUP_DAYS + (i + 1) * step:6.1f}  "
                          f"{context.getPrimitiveCount():7d} primitives", flush=True)

                pct, max_x = measure_penetration(context, environment_uuids)
                stats = (pct, max_x, measure_leaf_area(plantarch, plant_ids))
        finally:
            plantarch.__exit__(None, None, None)

    return frames, stats


BANNER_HEIGHT = 42
LEFT_BANNER_RGB = (192, 57, 43)    # red   = control, no avoidance
RIGHT_BANNER_RGB = (39, 174, 96)   # green = avoidance enabled


def _make_banner(text, width, rgb, path):
    """Render a caption strip to a PNG.

    ffmpeg's drawtext filter is absent from many builds (including the stock
    Homebrew one), so captions are drawn with Pillow instead of in ffmpeg.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (width, BANNER_HEIGHT), rgb)
    draw = ImageDraw.Draw(img)

    font = None
    for candidate in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                      "/System/Library/Fonts/Supplemental/Arial.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(candidate):
            font = ImageFont.truetype(candidate, 24)
            break
    if font is None:
        font = ImageFont.load_default()

    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text(((width - (right - left)) / 2 - left,
               (BANNER_HEIGHT - (bottom - top)) / 2 - top),
              text, fill=(255, 255, 255), font=font)
    img.save(path)
    return path


def stack_frames(left_frames, right_frames, out_dir, left_label, right_label,
                 width):
    """Compose the two runs into captioned side-by-side frames."""
    os.makedirs(out_dir, exist_ok=True)
    n = min(len(left_frames), len(right_frames))
    composed = []

    try:
        left_banner = _make_banner(left_label, width, LEFT_BANNER_RGB,
                                   os.path.join(out_dir, "_banner_left.png"))
        right_banner = _make_banner(right_label, width, RIGHT_BANNER_RGB,
                                    os.path.join(out_dir, "_banner_right.png"))
        captioned = True
    except ImportError:
        # Pillow unavailable: fall back to plain coloured bands.
        captioned = False
        print("  Pillow not installed -- using coloured bands without text.")

    for i in range(n):
        out = os.path.join(out_dir, f"pair_{i:04d}.jpeg")
        if captioned:
            # Banner first, then the frame: caption sits above each panel.
            filt = (
                "[2:v][0:v]vstack=inputs=2[l];"
                "[3:v][1:v]vstack=inputs=2[r];"
                "[l][r]hstack=inputs=2"
            )
            cmd = ["ffmpeg", "-y", "-loglevel", "error",
                   "-i", left_frames[i], "-i", right_frames[i],
                   "-i", left_banner, "-i", right_banner,
                   "-filter_complex", filt, out]
        else:
            filt = (
                f"[0:v]pad=iw:ih+{BANNER_HEIGHT}:0:{BANNER_HEIGHT}:color=0xC0392B[l];"
                f"[1:v]pad=iw:ih+{BANNER_HEIGHT}:0:{BANNER_HEIGHT}:color=0x27AE60[r];"
                "[l][r]hstack=inputs=2"
            )
            cmd = ["ffmpeg", "-y", "-loglevel", "error",
                   "-i", left_frames[i], "-i", right_frames[i],
                   "-filter_complex", filt, out]
        subprocess.run(cmd, check=True)
        composed.append(out)

    print(f"  Composed {len(composed)} captioned side-by-side frames")
    return composed


def encode_movie(frame_dir, pattern, out_path, fps):
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(fps),
        "-i", os.path.join(frame_dir, pattern),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        out_path,
    ]
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=float, default=60.0,
                        help="Simulated days in the ANIMATED growth window, "
                             f"after the un-filmed {SPINUP_DAYS:.0f}-day "
                             "spin-up (default: 60, i.e. days 158-218 -- the "
                             f"entire growth window). {TAIL_FRAMES} further "
                             "frames are appended past this. Going beyond ~day "
                             "360 defoliates the tree.")
    parser.add_argument("--step", type=float, default=2.0,
                        help="Simulated days per frame (default: 2 -> 30 frames)")
    parser.add_argument("--fps", type=int, default=5,
                        help="Movie frame rate (default: 5 -> 6 s for 30 frames)")
    parser.add_argument("--width", type=int, default=700)
    parser.add_argument("--height", type=int, default=560)
    parser.add_argument("--outdir", default=None,
                        help="Output directory (default: "
                             "docs/examples/output/collision_movie)")
    args = parser.parse_args()

    if args.outdir is None:
        outdir = str(get_output_dir("collision_movie"))
    else:
        outdir = os.path.abspath(args.outdir)
        os.makedirs(outdir, exist_ok=True)

    print("=" * 68)
    print("Collision Avoidance A/B Movie")
    print("=" * 68)
    total_frames = int(args.days / args.step) + TAIL_FRAMES
    print(f"  {args.days} days @ {args.step} d/frame "
          f"+ {TAIL_FRAMES} tail = {total_frames} frames per run "
          f"({total_frames / args.fps:.1f} s @ {args.fps} fps)")
    print(f"  Output directory: {display_path(outdir)}\n")

    print("Run 1/2: collision avoidance DISABLED (control)")
    off_frames, off_stats = render_run(
        "OFF", False, args.days, args.step,
        os.path.join(outdir, "frames_off"), args.width, args.height)

    print("\nRun 2/2: collision avoidance ENABLED")
    on_frames, on_stats = render_run(
        "ON", True, args.days, args.step,
        os.path.join(outdir, "frames_on"), args.width, args.height)

    # Objective check: does avoidance actually keep foliage out of the wall?
    off_pct, off_max, off_area = off_stats
    on_pct, on_max, on_area = on_stats
    print("\n" + "-" * 68)
    print(f"Wall penetration (vertices past the plane at x={WALL_X}, counting "
          "only\nthose within the wall's own y/z extent -- foliage arching over "
          "the top\nis not growing through anything):")
    print(f"  collision OFF: {off_pct:6.2f}% of foliage through wall, "
          f"deepest x = {off_max:.3f}, leaf area = {off_area:.4f}")
    print(f"  collision ON : {on_pct:6.2f}% of foliage through wall, "
          f"deepest x = {on_max:.3f}, leaf area = {on_area:.4f}")
    if off_pct > 0:
        print(f"  -> avoidance reduced penetrating foliage by "
              f"{100.0 * (off_pct - on_pct) / off_pct:.1f}%")
    # Comparable leaf area means the foliage was steered around the wall rather
    # than removed; a big drop would mean organs were pruned away instead.
    if off_area > 0:
        print(f"  -> leaf area retained: "
              f"{100.0 * on_area / off_area:.1f}% of the control")
    if on_pct >= off_pct:
        print("  -> WARNING: avoidance did not reduce penetration. The wall may "
              "sit outside\n     the canopy's growth envelope, in which case "
              "this scene demonstrates nothing.")
    print("-" * 68)

    if not shutil.which("ffmpeg"):
        print(f"\nffmpeg not found on PATH -- frames were written to "
              f"{display_path(outdir)} but no movie was encoded.\n"
              "Install ffmpeg (e.g. 'brew install ffmpeg') and re-run to "
              "produce the mp4.")
        return 0

    print("\nComposing side-by-side frames...")
    pair_dir = os.path.join(outdir, "frames_pair")
    stack_frames(off_frames, on_frames, pair_dir,
                 "COLLISION AVOIDANCE OFF", "COLLISION AVOIDANCE ON",
                 args.width)

    movie = os.path.join(outdir, "collision_avoidance.mp4")
    print("Encoding movie...")
    encode_movie(pair_dir, "pair_%04d.jpeg", movie, args.fps)

    print("\n" + "=" * 68)
    print(f"Movie written to: {display_path(movie)}")
    print("=" * 68)
    print("\nWhat to look for as the camera swings behind the wall:")
    print("  LEFT  (red, OFF): foliage hangs through to the far side")
    print("  RIGHT (green, ON): the far side of the wall stays clear")
    return 0


if __name__ == "__main__":
    sys.exit(main())
