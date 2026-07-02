from datetime import time
from Nailtech_website import create_app, db
from Nailtech_website.models import WorkingHours, Service

app = create_app()
app.app_context().push()

slots = [
    (0, [time(8,0), time(10,0), time(12,0), time(14,0), time(16,0)]),  # Monday
    (1, [time(8,0), time(11,0), time(13,0), time(15,0)]),              # Tuesday
    (2, [time(8,0), time(11,0), time(13,0), time(15,0)]),              # Wednesday
    (3, [time(8,0), time(10,0), time(12,0), time(14,0), time(16,0)]),  # Thursday
    (4, [time(8,0), time(11,0), time(13,0), time(15,0)]),              # Friday
    (5, [time(8,0), time(10,0), time(12,0), time(14,0), time(16,0)]),  # Saturday
]

services = Service.query.all()

for service in services:
    for weekday, times in slots:
        for t in times:
            # Avoid duplicates
            exists = WorkingHours.query.filter_by(service_id=service.id, weekday=weekday, slot_time=t).first()
            if not exists:
                db.session.add(WorkingHours(weekday=weekday, service_id=service.id, slot_time=t))

db.session.commit()
print("Working hours added for all services!")
