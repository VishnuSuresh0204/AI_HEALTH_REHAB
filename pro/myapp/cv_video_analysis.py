"""
AI Module — offline video analysis.

This is the "MediaPipe + OpenCV" backend path from the project abstract:
the patient uploads a video of themselves performing an exercise (instead
of a live webcam feed), and this module:

  1. opens it with OpenCV,
  2. runs MediaPipe's Pose model over every frame server-side,
  3. feeds the landmarks into ai_engine.py (the same angle/accuracy/rep
     logic) to build PoseFrameLog rows and a final PerformanceReport, and
  4. draws the detected skeleton + live stats onto each frame and writes
     it back out as an annotated video, so the patient (and therapist)
     can watch exactly what the AI saw.

Requires: pip install mediapipe opencv-python
"""

import os

import cv2
import mediapipe as mp

from django.conf import settings
from django.utils import timezone

from .models import PoseFrameLog, PerformanceReport
from . import ai_engine

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


def _landmarks_to_dicts(pose_landmarks):
    return [
        {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
        for lm in pose_landmarks.landmark
    ]


def _draw_overlay(frame, pose_landmarks, angle, accuracy, feedback, reps):
    mp_drawing.draw_landmarks(
        frame,
        pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
    )

    angle_text = f"Angle: {angle:.0f} deg" if angle is not None else "Angle: n/a"
    cv2.putText(frame, angle_text, (16, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Accuracy: {accuracy:.0f}%", (16, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Reps: {reps}", (16, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, feedback, (16, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 190), 2)

    return frame


def analyze_recorded_video(session):
    """Process session.recorded_video frame-by-frame: build PoseFrameLog +
    PerformanceReport, and write session.annotated_video with the pose
    skeleton drawn over every frame. Returns the created PerformanceReport."""

    if not session.recorded_video:
        raise ValueError("Session has no recorded_video to analyze")

    exercise = session.plan_item.exercise
    video_path = session.recorded_video.path

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_dir = os.path.join(settings.MEDIA_ROOT, "session_recordings", "analyzed")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"session_{session.id}_annotated.mp4"
    output_path = os.path.join(output_dir, output_filename)

    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    # Clear any previous frame logs so re-running is idempotent
    PoseFrameLog.objects.filter(session=session).delete()
    session.completed_reps = 0
    session.rep_phase = "extended"

    frame_number = 0
    accuracies = []

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            frame_number += 1
            timestamp_ms = int((frame_number / fps) * 1000)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb_frame)

            if not result.pose_landmarks:
                writer.write(frame)  # keep the video in sync even on missed detections
                continue

            landmarks = _landmarks_to_dicts(result.pose_landmarks)
            angle, side_used = ai_engine.get_joint_angle(landmarks, exercise)
            accuracy = ai_engine.posture_accuracy_from_angle(angle, exercise)
            feedback = ai_engine.generate_instant_feedback(accuracy, visible=angle is not None)

            rep_completed, new_phase = ai_engine.update_rep_state(session, angle, exercise)
            session.rep_phase = new_phase
            if rep_completed:
                session.completed_reps += 1

            PoseFrameLog.objects.create(
                session=session,
                frame_number=frame_number,
                timestamp_ms=timestamp_ms,
                joint_angle=angle if angle is not None else 0,
                posture_accuracy=accuracy,
                is_rep_complete=rep_completed,
                landmarks_json=None,
            )
            accuracies.append(accuracy)

            frame = _draw_overlay(frame, result.pose_landmarks, angle, accuracy, feedback, session.completed_reps)
            writer.write(frame)

    cap.release()
    writer.release()

    session.status = "completed"
    session.ended_date = timezone.now()
    session.avg_accuracy = round(sum(accuracies) / len(accuracies), 2) if accuracies else 0
    session.duration_seconds = int(frame_number / fps)
    session.annotated_video.name = f"session_recordings/analyzed/{output_filename}"
    session.save()

    overall_feedback = ai_engine.generate_instant_feedback(session.avg_accuracy)

    report, _ = PerformanceReport.objects.update_or_create(
        session=session,
        defaults={
            "overall_score": session.avg_accuracy,
            "repetition_accuracy": session.avg_accuracy,
            "posture_feedback": overall_feedback,
            "recommendations": (
                "Posture and repetitions were scored automatically from the "
                "uploaded video. A therapist should review before treating "
                "this as final." if session.avg_accuracy < 70 else ""
            ),
            "flagged_for_review": session.avg_accuracy < 60,
        },
    )

    reports_dir = os.path.join(settings.MEDIA_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_filename = f"session_{session.id}_report.txt"
    with open(os.path.join(reports_dir, report_filename), "w") as f:
        f.write(
            f"Rehabilitation Session Report\n"
            f"Patient: {session.patient.name}\n"
            f"Exercise: {exercise.name}\n"
            f"Date: {session.started_date.strftime('%Y-%m-%d')}\n"
            f"Repetitions Completed: {session.completed_reps}\n"
            f"Overall Score: {report.overall_score}\n"
            f"Feedback: {report.posture_feedback}\n"
        )
    report.report_file.name = f"reports/{report_filename}"
    report.save()

    return report
