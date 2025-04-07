from app import create_app
from app.application.application import auto_reject
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
app = create_app()

# # Setting up the scheduler
# scheduler = BackgroundScheduler()
# scheduler.start()

# # Add a job to run every day at 9 AM
# scheduler.add_job(
#     func=lambda: auto_reject(app), 
#     trigger=CronTrigger(hour=17, minute=43), 
#     id='daily_job',
#     replace_existing=True
# )

if __name__ == '__main__':
    app.run(debug=True)