from flask import Flask, render_template
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Frontend service', version='1.0.1')


by_full_path_counter = metrics.counter('full_path_counter', 'counting requests by full path', labels={'full_path': lambda: request.full_path})
by_endpoint_counter = metrics.counter('endpoint_counter', 'counting request by endpoint', labels={'endpoint': lambda: request.endpoint})

@app.route("/")
@by_full_path_counter
@by_endpoint_counter
def homepage():
    return render_template("main.html")


if __name__ == "__main__":
    app.run()
