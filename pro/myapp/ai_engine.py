"""
AI Module — pose analysis engine.

Framework-agnostic core used by both:
  - the live webcam path (views.user_submit_frame), fed landmarks captured
    in-browser by MediaPipe's JS pose model, and
  - the offline path (cv_video_analysis.py), fed landmarks extracted
    server-side from an uploaded video with OpenCV + MediaPipe's Python
    "solutions.pose" model.

Both paths hand this module the same thing: a list of 33 MediaPipe Pose
landmarks, each {"x": float, "y": float, "z": float, "visibility": float}.
This module never touches a camera, a video file, or the network — that
keeps it trivially testable and reusable across both entry points.
"""

import math

# ---------------------------------------------------------------------
# MEDIAPIPE POSE LANDMARK INDICES (33-point model)
# ---------------------------------------------------------------------

LM = {
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16,
    "left_hip": 23, "right_hip": 24,
    "left_knee": 25, "right_knee": 26,
    "left_ankle": 27, "right_ankle": 28,
    "left_foot_index": 31, "right_foot_index": 32,
}

# body_part -> the 3-point angle (a-b-c, angle measured at b) for each side.
# Picking the right joint triplet per exercise is what turns raw landmarks
# into a single meaningful number (the "joint angle" from the abstract).
JOINT_TRIPLETS = {
    "knee": {
        "left": ("left_hip", "left_knee", "left_ankle"),
        "right": ("right_hip", "right_knee", "right_ankle"),
    },
    "hip": {
        "left": ("left_shoulder", "left_hip", "left_knee"),
        "right": ("right_shoulder", "right_hip", "right_knee"),
    },
    "shoulder": {
        "left": ("left_elbow", "left_shoulder", "left_hip"),
        "right": ("right_elbow", "right_shoulder", "right_hip"),
    },
    "elbow": {
        "left": ("left_shoulder", "left_elbow", "left_wrist"),
        "right": ("right_shoulder", "right_elbow", "right_wrist"),
    },
    "ankle": {
        "left": ("left_knee", "left_ankle", "left_foot_index"),
        "right": ("right_knee", "right_ankle", "right_foot_index"),
    },
    # Trunk lean, approximated from the knee triplet (no single "spine"
    # landmark exists in the 33-point model) — good enough as a default.
    "spine": {
        "left": ("left_shoulder", "left_hip", "left_knee"),
        "right": ("right_shoulder", "right_hip", "right_knee"),
    },
    "full_body": {
        "left": ("left_hip", "left_knee", "left_ankle"),
        "right": ("right_hip", "right_knee", "right_ankle"),
    },
}

MIN_VISIBILITY = 0.5  # below this, a landmark is considered unreliable


# ---------------------------------------------------------------------
# ANGLE MATH
# ---------------------------------------------------------------------

def calculate_angle(a, b, c):
    """Angle at point b (in degrees), formed by points a-b-c.
    Each point is a dict with 'x' and 'y' (z ignored — 2D projection is
    stable enough for posture scoring and avoids depth-noise issues)."""

    ax, ay = a["x"], a["y"]
    bx, by = b["x"], b["y"]
    cx, cy = c["x"], c["y"]

    ba = (ax - bx, ay - by)
    bc = (cx - bx, cy - by)

    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.hypot(*ba)
    mag_bc = math.hypot(*bc)

    if mag_ba == 0 or mag_bc == 0:
        return None

    cosine = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cosine))


def _side_visibility(landmarks, triplet):
    return sum(landmarks[LM[name]].get("visibility", 1.0) for name in triplet)


def get_joint_angle(landmarks, exercise):
    """Pick whichever side (left/right) is more visible to the camera and
    return (angle_degrees, side_used). Returns (None, None) if neither side
    is reliably visible."""

    triplets = JOINT_TRIPLETS.get(exercise.body_part, JOINT_TRIPLETS["full_body"])

    best_side, best_visibility = None, -1
    for side, triplet in triplets.items():
        visibility = _side_visibility(landmarks, triplet)
        if visibility > best_visibility:
            best_side, best_visibility = side, visibility

    if best_visibility / 3 < MIN_VISIBILITY:
        return None, None

    a_name, b_name, c_name = triplets[best_side]
    a, b, c = landmarks[LM[a_name]], landmarks[LM[b_name]], landmarks[LM[c_name]]

    angle = calculate_angle(a, b, c)
    return angle, best_side


# ---------------------------------------------------------------------
# POSTURE ACCURACY
# ---------------------------------------------------------------------

def posture_accuracy_from_angle(angle, exercise):
    """100 when inside the exercise's target angle band, decaying
    linearly per degree of deviation outside it."""

    if angle is None:
        return 0.0

    lo, hi = exercise.target_angle_min, exercise.target_angle_max

    if lo <= angle <= hi:
        return 100.0

    deviation = min(abs(angle - lo), abs(angle - hi))
    return max(0.0, 100.0 - deviation)


def generate_instant_feedback(accuracy, visible=True):
    if not visible:
        return "Can't see the joint clearly — step back or adjust the camera angle."
    if accuracy >= 85:
        return "Great form, keep going!"
    if accuracy >= 60:
        return "Adjust your posture slightly for better alignment."
    return "Posture off target — slow down and realign with the demo."


# ---------------------------------------------------------------------
# REPETITION COUNTING (stateful across frames via session.rep_phase)
# ---------------------------------------------------------------------

def update_rep_state(session, angle, exercise):
    """A rep = one full cycle of moving from the 'extended' resting
    position into the exercise's target band ('flexed') and back out to
    'extended' again. State persists on the session between requests
    since each HTTP call is otherwise stateless.

    Returns (rep_completed: bool, new_phase: str).
    """

    if angle is None:
        return False, session.rep_phase

    hi = exercise.target_angle_max

    if session.rep_phase == "extended" and angle <= hi:
        return False, "flexed"

    if session.rep_phase == "flexed" and angle >= hi:
        return True, "extended"

    return False, session.rep_phase


def is_target_reached(session):
    """Exercise-completion detection: has the patient hit the prescribed
    reps x sets for this plan item?"""

    prescribed_total = session.plan_item.prescribed_reps * session.plan_item.prescribed_sets
    return session.completed_reps >= prescribed_total


# ---------------------------------------------------------------------
# SESSION-LEVEL SUMMARY (used when finalizing a completed session)
# ---------------------------------------------------------------------

def summarize_session(frame_logs):
    """Aggregate per-frame posture accuracy into the numbers a
    PerformanceReport needs. `frame_logs` is any iterable of objects/dicts
    with a `posture_accuracy` attribute or key."""

    values = [
        f["posture_accuracy"] if isinstance(f, dict) else f.posture_accuracy
        for f in frame_logs
    ]

    if not values:
        return 0.0, 0.0, "No frames captured for this session."

    avg_accuracy = round(sum(values) / len(values), 2)
    feedback = generate_instant_feedback(avg_accuracy)

    return avg_accuracy, avg_accuracy, feedback
