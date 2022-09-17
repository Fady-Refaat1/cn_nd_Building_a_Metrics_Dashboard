### Overview architecture 

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/project-overview.png)


## Verify the monitoring installation

*TODO:* run `kubectl` command to show the running pods and services for all components. Take a screenshot of the output and include it here to verify the installation

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/all-pods.png)


![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/all-svc.png)


## Setup the Jaeger and Prometheus source
*TODO:* Expose Grafana to the internet and then setup Prometheus as a data source. Provide a screenshot of the home page after logging into Grafana.

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/GrafanaHomePage.png)


## Create a Basic Dashboard
*TODO:* Create a dashboard in Grafana that shows Prometheus as a source. Take a screenshot and include it here.

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/Grafana_with_prometheus.png)


## Describe SLO/SLI
*TODO:* Describe, in your own words, what the SLIs are, based on an SLO of *monthly uptime* and *request response time*.

SLI : The performance level achived example 99% uptime based on SLOs like the actual upTime in month or *request response time* per minute.

## Creating SLI metrics.
*TODO:* It is important to know why we want to measure certain metrics for our customer. Describe in detail 5 metrics to measure these SLIs. 
<ol>
    <li>Latency.the time taken to respond to a request.</li>
    <li>Uptime.time of availability of the app</li>
    <li>CPU Utilization</li>
    <li>Network Capacity. average bandwidth in month</li>
    <li>memory usage</li>
</ol>

## Create a Dashboard to measure our SLIs
*TODO:* Create a dashboard to measure the uptime of the frontend and backend services We will also want to measure to measure 40x and 50x errors. Create a dashboard that show these values over a 24 hour period and take a screenshot.

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/measurement_of_SLIs.png)

## Tracing our Flask App
*TODO:*  We will create a Jaeger span to measure the processes on the backend. Once you fill in the span, provide a screenshot of it here. Also provide a (screenshot) sample Python file containing a trace and span code used to perform Jaeger traces on the backend service.

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/Tracing_Flask_App.png)


```
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

```
## Jaeger in Dashboards
*TODO:* Now that the trace is running, let's add the metric to our current Grafana dashboard. Once this is completed, provide a screenshot of it here.

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/Jaeger_Grafana.png)


## Report Error
*TODO:* Using the template below, write a trouble ticket for the developers, to explain the errors that you are seeing (400, 500, latency) and to let them know the file that is causing the issue also include a screenshot of the tracer span to demonstrate how we can user a tracer to locate errors easily.

TROUBLE TICKET

Name: error when call /star endpoint

Date: September 16 2022, 11:37:06.262

Subject: request not successfully completed 

Affected Area: backend

Severity: critical 

Description: when call the star endpoint it return 500 status code so we need to return the response 200. that is critical because it may we can't make DB connection

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/report-screenShot.png)

## Creating SLIs and SLOs
*TODO:* We want to create an SLO guaranteeing that our application has a 99.95% uptime per month. Name four SLIs that you would use to measure the success of this SLO.

<ol>
<li>Latency : 95% of the requests takes 30 - 40 ms to complete</li>
<li>Uptime : 99.95% service should be available </li>
<li>Error Rate : must be less than 0.5 % of 4xx or 5xx errors</li>
<li>Resource Usage: CPU and RAM usage must not exceed 95% per month.</li>
</ol>

## Building KPIs for our plan
*TODO*: Now that we have our SLIs and SLOs, create a list of 2-3 KPIs to accurately measure these metrics as well as a description of why those KPIs were chosen. We will make a dashboard for this, but first write them down here.


1. Latency : when the latency within the 30 - 40 that indicate of healthy application that have suitable memory to serve the client in month 
   - performance -  This KPI shows the application's overall performance.
   - Monthly uptime - This KPI shows the application's overall usability when the Latency avg per request is low or within 30 - 40 ms.
2. Uptime : Due to our SLOs we want the application up 99.95% per month
   - Monthly downtime - This KPI shows the number of the downtime of the  application.
   - Avg monthly Uptime - This KPI shows the application's overall usabilityThis KPI shows the application's overall usability . 
3. Error Rate : we want the application run without failure so we want the fail requests than 0.05% per month.
   - Monthly uptime - This KPI shows the application's overall usability when the failure rate is low.
   - 50x code responses per month - this KPI shows downtime of the application.

4. Resource Usage: To can see the consumption so let us know if we want to expand the resources to our solution or not in month.
   - Average monthly Resource usage of all the pods - This KPI was selected to show the total amount of resources utilized by all the pods needed to run the application.
   - Monthly quota limit - This KPI was selected to show whether the application is using more resources than its allotted quota.


## Final Dashboard
*TODO*: Create a Dashboard containing graphs that capture all the metrics of your KPIs and adequately representing your SLIs and SLOs. Include a screenshot of the dashboard here, and write a text description of what graphs are represented in the dashboard.

![alt text](https://github.com/Fady-Refaat1/cn_nd_Building_a_Metrics_Dashboard/blob/master/answer-img/FinalDashboard.png)


# Description of the dashboard:
<ul>
<li>Uptime: the up time is 87.5 %</li>
<li>Error Rate: the percentage of failed requests over success requests</li>
<li>CPU Usage: CPU utilization by the service</li>
<li>Memory Usage: Memory utilization by the service</li>
<li>50x, 40x Errors: 50x, 40x respond from our service</li>
</ul>

