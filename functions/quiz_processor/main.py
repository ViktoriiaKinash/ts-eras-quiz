import base64
import json
import os
from google.cloud import monitoring_v3
import sendgrid
from sendgrid.helpers.mail import Mail
from datetime import datetime

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")

def quiz_event_handler(event, context):
    payload = json.loads(
        base64.b64decode(event["data"]).decode("utf-8")
    )

    era = payload["era"]
    email = payload.get("user_email", "viktoriakinash@student.agh.edu.pl")

    # -----------------------
    # Send Email (SendGrid)
    # -----------------------
    if SENDGRID_API_KEY:
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email="noreply@ts-eras-quiz.com",
            to_emails=email,
            subject="Your Era Quiz Result",
            html_content=f"<strong>Your era is:</strong> {era}"
        )
        sg.send(message)

    # -----------------------
    # Custom Metric
    # -----------------------
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/ts/era_assignments"
    series.metric.labels["era"] = era
    series.resource.type = "global"

    point = monitoring_v3.Point()
    point.value.int64_value = 1
    point.interval.end_time.GetCurrentTime()

    series.points.append(point)

    client.create_time_series(
        request={"name": project_name, "time_series": [series]}
    )

    print(f"Processed quiz event for era={era} at {datetime.utcnow()}")
