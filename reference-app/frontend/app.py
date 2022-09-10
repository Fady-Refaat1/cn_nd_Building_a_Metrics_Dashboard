from flask import Flask, render_template
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Frontend service', version='1.0.1')

@app.route("/")
def homepage():
    return render_template("main.html")


if __name__ == "__main__":
    app.run()
