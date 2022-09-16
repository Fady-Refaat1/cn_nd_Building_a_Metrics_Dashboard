import logging
import os
import re
import requests


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


@app.route("/star", methods=["POST"])
@by_full_path_counter
@by_endpoint_counter
def add_star():
    star = mongo.db.stars
    name = request.json["name"]
    distance = request.json["distance"]
    star_id = star.insert({"name": name, "distance": distance})
    new_star = star.find_one({"_id": star_id})
    output = {"name": new_star["name"], "distance": new_star["distance"]}
    return jsonify({"result": output})


@app.route("/trace")
@by_full_path_counter
@by_endpoint_counter
def trace():
    def remove_tags(text):
        tag = re.compile(r"<[^>]+>")
        return tag.sub("", text)

    with tracer.start_span("get-python-jobs") as span:
        res = requests.get("https://jobs.github.com/positions.json?description=python")
        span.log_kv({"event": "get jobs count", "count": len(res.json())})
        span.set_tag("jobs-count", len(res.json()))

        jobs_info = []
        for result in res.json():
            jobs = {}
            with tracer.start_span("request-site") as site_span:
                logger.info(f"Getting website for {result['company']}")
                try:
                    jobs["description"] = remove_tags(result["description"])
                    jobs["company"] = result["company"]
                    jobs["company_url"] = result["company_url"]
                    jobs["created_at"] = result["created_at"]
                    jobs["how_to_apply"] = result["how_to_apply"]
                    jobs["location"] = result["location"]
                    jobs["title"] = result["title"]
                    jobs["type"] = result["type"]
                    jobs["url"] = result["url"]

                    jobs_info.append(jobs)
                    site_span.set_tag("http.status_code", res.status_code)
                    site_span.set_tag("company-site", result["company"])
                except Exception:
                    logger.error(f"Unable to get site for {result['company']}")
                    site_span.set_tag("http.status_code", res.status_code)
                    site_span.set_tag("company-site", result["company"])

    return jsonify(jobs_info)

if __name__ == "__main__":
    app.run(debug=True,)