from django.core.management.base import BaseCommand, CommandError

from myapp.models import ExerciseSession
from myapp.cv_video_analysis import analyze_recorded_video


class Command(BaseCommand):
    help = "Run the MediaPipe + OpenCV pose analysis over a session's recorded video."

    def add_arguments(self, parser):
        parser.add_argument("session_id", type=int)

    def handle(self, *args, **options):
        session_id = options["session_id"]

        try:
            session = ExerciseSession.objects.get(id=session_id)
        except ExerciseSession.DoesNotExist:
            raise CommandError(f"ExerciseSession {session_id} does not exist")

        if not session.recorded_video:
            raise CommandError(f"Session {session_id} has no recorded_video uploaded")

        self.stdout.write(f"Analyzing session {session_id} ({session.plan_item.exercise.name})...")

        report = analyze_recorded_video(session)

        self.stdout.write(self.style.SUCCESS(
            f"Done. avg_accuracy={session.avg_accuracy} reps={session.completed_reps} "
            f"flagged_for_review={report.flagged_for_review}"
        ))
