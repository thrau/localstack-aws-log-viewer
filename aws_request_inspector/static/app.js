function startWebsocketConnection() {
    const exampleSocket = new WebSocket("ws://localhost:4566/aws-request-inspector/stream");

    exampleSocket.onmessage = (event) => {
        let data = event.data
        let doc = JSON.parse(data);

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
                record["internal"] = '<span class="badge bg-secondary is-internal">internal</span>';
            }

            // prepare element
            var dom = $("<div></div>");
            dom.loadTemplate($("#tpl-event-record"), record);
            let row = $(dom[0].firstChild);
            row.on("click", loadDetailContainer);

            if (record["is_internal"] && !$("#showInternalSwitch").is(':checked')) {
                row.attr("hidden", true);
            }

            $("#event-records").prepend(row);
        }

        if (doc["type"] === "response") {
            let containerId = "#request-" + doc['request_id'];
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

function deepJsonParse(text) {
    const parseRecursive = (obj) => {
        for (const key in obj) {
            if (typeof obj[key] === 'string' && obj[key].startsWith('{')) {
                try {
                    obj[key] = JSON.parse(obj[key]);
                } catch (error) {
                    // Handle JSON parsing error
                    console.error(`Error parsing JSON at key '${key}': ${error.message}`);
                }
            } else if (typeof obj[key] === 'object' && obj[key] !== null) {
                parseRecursive(obj[key]); // Recursively parse nested objects
            }
        }
    };

    let doc = JSON.parse(text);
    parseRecursive(doc);
    return doc;
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
        doc['request_data_pretty'] = JSON.stringify(deepJsonParse(doc['request_data']), undefined, 2);

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
            doc['response_data_pretty'] = JSON.stringify(deepJsonParse(doc['response_data']), undefined, 2);
        }

        $("#event-details").loadTemplate($("#tpl-event-details"), doc);
    });
}

function app() {
    startWebsocketConnection();

    $("#clear-log-button").on("click", function (item) {
        $("#event-records").html("");
        $("#event-details").html("");
    });

    const updateInternalRequests = () => {
        let hidden = !$("#showInternalSwitch").is(':checked');

        let internal = $("#event-records tr span.is-internal");
        for (let i = 0; i < internal.length; i++) {
            $(internal[i].parentNode.parentNode).attr("hidden", hidden);
        }
    }

    $("#showInternalSwitch").on("change", updateInternalRequests);

    $.get("./query", function (data) {
        let records = data['records'].reverse();

        for (let i = 0; i < records.length; i++) {
            let record = records[i];

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
                record["internal"] = '<span class="badge bg-secondary is-internal">internal</span>';
            }
        }
        $("#event-records").loadTemplate($("#tpl-event-record"), records);
        $("#event-records tr").on("click", loadDetailContainer);
        updateInternalRequests();
    });

}

window.onload = app;


