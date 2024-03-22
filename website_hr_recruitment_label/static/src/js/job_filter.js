odoo.define("web_hr_recruitment_label.job_filter", function(require) {
    "use strict";

    //    Var ajax = require("web.ajax");
    require("web.dom_ready");

    const checkboxes = document.querySelectorAll('.filter_label');
    if ((new RegExp('/jobs.*/label_ids/')).test(window.location.pathname)) {
        var label_ids = window.location.pathname.replace(new RegExp("/jobs.*/label_ids/"), "").split(",");
        for (var i = 0; i < label_ids.length; i++) {
            for (var j = 0; j < checkboxes.length; j++) {
                if (checkboxes[j].id === label_ids[i]) {
                    checkboxes[j].checked = true
                }
            }
        }
    }

    for (var i = 0; i < checkboxes.length; i++) {
        checkboxes[i].addEventListener('change', function() {
            var old_path = window.location.pathname;
            var label_id_path = "/label_ids/"
            var anyChecked = false;
            for (var j = 0; j < checkboxes.length; j++) {
                if (checkboxes[j].checked) {
                    label_id_path = label_id_path + checkboxes[j].id + ","
                    anyChecked = true;
                }
            }
            if (anyChecked) {
                window.location.replace(old_path.replace(new RegExp("/label_ids/[\\d,]*"),"") + label_id_path.replace(/,$/, ""));
            } else {
                window.location.replace(old_path.replace(new RegExp("/label_ids/[\\d,]*"),""));
            }

        })
    }



});
