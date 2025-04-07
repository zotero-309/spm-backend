from app import create_app
from app.application.application import auto_reject
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os

app = create_app()

# Setting up the scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Add a job to run every day at a specific time
scheduler.add_job(
    func=lambda: auto_reject(app), 
    trigger=CronTrigger(hour=17, minute=43), 
    id='daily_job',
    replace_existing=True
)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # 10000 is a default fallback
    app.run(host="0.0.0.0", port=port, debug=True)
