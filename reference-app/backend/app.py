import logging
import os

from flask import Flask, jsonify, request, Response
from flask_opentracing import FlaskTracing
from flask_cors import CORS
from jaeger_client import Config
from flask_pymongo import PyMongo
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory
from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics

app = Flask(__name__)
CORS(app)

app.config['MONGO_DBNAME'] = 'example-mongodb'
app.config['MONGO_URI'] = 'mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb'
mongo = PyMongo(app)

metrics = GunicornInternalPrometheusMetrics(app)
metrics.info("app_info", "Backend service", version="1.0.1")

by_full_path_counter = metrics.counter('full_path_counter', 'counting requests by full path', labels={'full_path': lambda: request.full_path})
by_endpoint_counter = metrics.counter('endpoint_counter', 'counting request by endpoint', labels={'endpoint': lambda: request.endpoint})

logging.getLogger("").handlers = []
logging.basicConfig(format="%(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

JAEGER_AGENT_HOST = os.getenv('JAEGER_AGENT_HOST', 'localhost')


def init_tracer(service):

    config = Config(
        config={
            "sampler": {"type": "const", "param": 1},
            "logging": True,
            "reporter_batch_size": 1,
        },
        service_name=service,
        validate=True,
        metrics_factory=PrometheusMetricsFactory(service_name_label=service),
    )

    # this call also sets opentracing.tracer
    return config.initialize_tracer()


tracer = init_tracer("backend")
flask_tracer = FlaskTracing(tracer, True, app)



@app.route("/")
@by_full_path_counter
@by_endpoint_counter
def homepage():
    with tracer.start_span('hello-world'):
        return "Hello World"

@app.route('/error-500')
@by_full_path_counter
@by_endpoint_counter
def error5xx():
    with tracer.start_span('error-500'):
       Response("error-500", status=500, mimetype='application/json')

@app.route("/api")
@by_full_path_counter
@by_endpoint_counter
def my_api():
    answer = "something"
    return jsonify(repsonse=answer)


@app.route("/star")
@by_full_path_counter
@by_endpoint_counter
def add_star():
    star = mongo.db.stars
    star_id = star.insert({"name": "name", "distance": "distance"})
    new_star = star.find_one({"_id": star_id})
    output = {"name": new_star["name"], "distance": new_star["distance"]}
    return jsonify({"result": output})


if __name__ == "__main__":
    app.run(debug=True,)