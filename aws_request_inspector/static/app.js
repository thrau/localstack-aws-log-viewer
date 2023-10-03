function startWebsocketConnection() {
    const exampleSocket = new WebSocket("ws://localhost:4566/aws-request-inspector/stream");

    exampleSocket.onmessage = (event) => {
        let data = event.data
        let doc = JSON.parse(data);

        // $("#event-container").append("<li><pre>" + JSON.stringify(doc, undefined, 2) + "</pre></li>")
        if (doc["type"] === "request") {
            let ts = new Date(doc["timestamp"] * 1000).toISOString();
            let record = doc;

            // prepare data
            record["timestamp"] = ts;
            record["row-id"] = "request-" + record["request_id"];
            record["status"] = "?";
            record["status-class"] = "bg-secondary";
            record["internal"] = "";
            if (record["is_internal"]) {
                record["internal"] = '<span class="badge bg-secondary">internal</span>';
            }

            // prepare element
            var dom = $("<div></div>");
            dom.loadTemplate($("#tpl-event-record"), record);
            let row = $(dom[0].firstChild);
            row.on("click", loadDetailContainer);
            $("#event-records").append(row);
        }

        if (doc["type"] === "response") {
            let containerId = "#request-" + doc['request_id'];
            console.log(doc);
            let record = doc;

            let label = $(containerId + " .request-status-field > span");
            label.html(record["status"]);

            let cssClass;
            if (record["status"] >= 500) {
                cssClass = "bg-danger";
            } else if (record["status"] >= 400) {
                cssClass = "bg-warning";
            } else if (record["status"] >= 200) {
                cssClass = "bg-success";
            }
            label.toggleClass(cssClass);

            //
            // data = doc["response_data"]
            // if (doc['is_error']) {
            //     data = doc['error'];
            // }
            //
            // $(containerId + "-payload > td").append("<hr><div>Response: <pre style='max-width: 800px'>" + JSON.stringify(data, undefined, 2) + "</pre></div>")
        }
    };
}

function loadDetailContainer(item) {
    let requestId = item.currentTarget.id.slice(8);
    $("#event-records tr").removeClass("table-active");
    $(this).toggleClass("table-active");
    $("#details-container").html(
        '<div className="spinner-border text-primary" role="status"><span className="sr-only"></span></div>'
    );
    $.get("./query?request_id=" + requestId, function (data) {
        let doc = data['records'][0];
        doc['request_data_pretty'] = JSON.stringify(JSON.parse(doc['request_data']), undefined, 2);

        let requestHeaders = JSON.parse(doc['request_headers']);
        doc['request_headers_pretty'] = "";
        for (let i = 0; i < requestHeaders.length; i++) {
            doc['request_headers_pretty'] += `${requestHeaders[i][0]}: ${requestHeaders[i][1]}\n`;
        }
        let responseHeaders = JSON.parse(doc['response_headers']);
        doc['response_headers_pretty'] = "";
        for (let i = 0; i < responseHeaders.length; i++) {
            doc['response_headers_pretty'] += `${responseHeaders[i][0]}: ${responseHeaders[i][1]}\n`;
        }

        if (doc['err_code'] != null) {
            doc['response_data_pretty'] = JSON.stringify({
                "error": {
                    "code": doc['err_code'],
                    "message": doc['err_msg'],
                }
            }, undefined, 2);
        } else {
            doc['response_data_pretty'] = JSON.stringify(JSON.parse(doc['response_data']), undefined, 2);
        }

        $("#event-details").loadTemplate($("#tpl-event-details"), doc);
    });
}

function app() {

    startWebsocketConnection();

    $.get("./query", function (data) {
        let records = data['records'];

        for (let i = 0; i < records.length; i++) {
            let record = records[i];
            console.log(record);

            record["row-id"] = "request-" + record["request_id"];
            if (record["status"] >= 500) {
                record["status-class"] = "bg-danger";
            } else if (record["status"] >= 400) {
                record["status-class"] = "bg-warning";
            } else if (record["status"] >= 200) {
                record["status-class"] = "bg-success";
            }

            record["internal"] = "";
            if (record["is_internal"]) {
                record["internal"] = '<span class="badge bg-secondary">internal</span>';
            }
        }
        $("#event-records").loadTemplate($("#tpl-event-record"), records);
        $("#event-records tr").on("click", loadDetailContainer);
    });

}

window.onload = app;


