// ****************************
//  scripts for the diff pages
// ****************************

//function calcTimeRange(timeRangeValue, timeRangeDescription) {
//    let selectedRange = timeRangeValue; //$(this).val();
//
//    // Default bounds (negative infinity to positive infinity)
//    let fromDate = null;
//    let toDate = moment(); // "Now" is always the upper bound for a relative range
//
//    if (selectedRange!== 'none') {
//      // Split the value (e.g., "15-minutes") into amount and unit
//      let parts = selectedRange.split('-');
//      let amount = parseInt(parts, 10);
//      let unit = parts[1];
//
//      // Calculate the exact 'From' time using moment.js
//      fromDate = moment().subtract(amount, unit);
//    }
//
//    // Pass fromDate and toDate to your existing options filtering algorithm here
//      console.debug("timeRangeDescription: ", timeRangeDescription);
//      console.debug("fromDate: ", fromDate);
//      console.debug("toDate: ", toDate);
//    // filterArtifactOptions(fromDate, toDate);
//}

//function calcTimeRange(timeRangeValue, timeRangeDescription) {
//    let selectedRange = timeRangeValue;
//
//    // Default bounds
//    let fromDate = null;
//    let toDate = moment();
//
//    if (selectedRange!== 'none') {
//      let parts = selectedRange.split('-');
//      let amount = parseInt(parts, 10);
//      let unit = parts[1];
//      fromDate = moment().subtract(amount, unit);
//    }
//
//    // Format dates for the server payload (ISO 8601 string is standard)
//    let payload = {
//        start_date: fromDate? fromDate.format() : null,
//        end_date: toDate.format()
//    };
//
//    // Trigger the AJAX request to your Flask backend
//    $.ajax({
//        url: '/api/get-artifacts', // Replace with your actual Flask route
//        type: 'GET',
//        data: payload,
//        dataType: 'json',
//        success: function(response) {
//            let $compareFrom = $('#compareFromSelect'); // Replace with your actual select ID
//            let $compareTo = $('#compareToSelect');     // Replace with your actual select ID
//
//            // 1. Clear the existing options
//            $compareFrom.empty();
//            $compareTo.empty();
//
//            // 2. Iterate through the returned JSON and build new options
//            $.each(response.data, function(index, artifact) {
//                // Assuming 'artifact' contains the filename like '20260326-101026-6-openobserve.json'
//                let optionHTML = $('<option></option>').val(artifact.filename).text(artifact.filename);
//
//                $compareFrom.append(optionHTML.clone());
//                $compareTo.append(optionHTML.clone());
//            });
//
//            // 3. Command bootstrap-select to rebuild the UI with the new DOM elements
//            $compareFrom.selectpicker('refresh');
//            $compareTo.selectpicker('refresh');
//        },
//        error: function(xhr, status, error) {
//            console.error("Failed to fetch artifacts: ", error);
//            // Optionally trigger a PatternFly Toast notification here
//        }
//    });
//}

function calcTimeRange(timeRangeValue, timeRangeDescription) {
    let selectedRange = timeRangeValue;

    // Default bounds
    let fromDate = null;
    let toDate = moment();

    // Calculate the 'From' boundary if a specific relative time is chosen
    if (selectedRange!== 'none' && selectedRange!== 'Priority') {
        let parts = selectedRange.split('-');
        let amount = parseInt(parts, 10);
        let unit = parts[1];
        fromDate = moment().subtract(amount, unit);
    }

    // Format dates to strictly match the Python strptime format (YYYYMMDD-HHMMSS)
    // Send an empty string if fromDate is null (meaning "All Time")
    let payload = {
        start_date: fromDate? fromDate.format('YYYYMMDD-HHmmss') : '',
        end_date: toDate.format('YYYYMMDD-HHmmss')
    };

    // Execute the AJAX call to the Flask endpoint
    $.ajax({
        url: '/diff/data/list/from', // Ensure this matches your unified Python route
        type: 'GET',
        data: payload,
        dataType: 'json',
        success: function(response) {
            let $compareFromSelect = $('#check-results-from-select');
            let $compareToSelect = $('#check-results-to-select');

            // Empty the native select dropdowns
            $compareFromSelect.empty();
            $compareToSelect.empty();

            // Iterate over the returned JSON objects
            $.each(response, function(index, artifact) {
                // Strip '.json' from the display name to match your Image 3 UI
                let displayName = artifact.filename.replace('.json', '');

                // The value must remain the full filename so the backend can locate it later
                let optionHTML = $('<option></option>').val(artifact.filename);

                if (artifact.is_baseline) {
                    // Apply your requested styling to the data-content attribute
                    let customHtml = displayName + ' <span style="color: #f0ab00;">&#9733; baseline</span>';
                    optionHTML.attr('data-content', customHtml);
                    // Fallback text
                    optionHTML.text(displayName + ' (baseline)');
                } else {
                    optionHTML.attr('data-content', displayName);
                    optionHTML.text(displayName);
                }

                $compareFromSelect.append(optionHTML.clone());
                $compareToSelect.append(optionHTML.clone());
            });

            // Command bootstrap-select to rebuild the visual UI
            $compareFromSelect.selectpicker('refresh');
            $compareToSelect.selectpicker('refresh');
        },
        error: function(xhr, status, error) {
            console.error("Failed to fetch filtered artifacts: ", error);
            // Optional: You could trigger a PatternFly Toast here to notify the user of a network error
        }
    });
}


// 4. Visual Decoration Logic
function renderDiffTable(data) {
    var dataResults = data.results || {};

    $.each(dataResults, function(hashId, item) {
        if (item.state_change && item.state_change!== 'unchanged') {

            // Safely scope the find specifically to the report body
            var $changedItem = $('#report_table_risu_body').find('#plugin-' + hashId);

            if ($changedItem.length > 0) {
                var badgeHtml = `<span class="diff-badge badge-${item.state_change}">${item.state_change.toUpperCase()}</span>`;

                $changedItem.addClass(`row-${item.state_change}`);

                // Only append the badge if it doesn't already exist to prevent duplicates on double-clicks
                if ($changedItem.find('.diff-badge').length === 0) {
                    $changedItem.find('.list-group-item-heading').append(badgeHtml);
                }

                // Explicitly force the row open on load
                $changedItem.addClass("list-view-pf-expand-active");
                $changedItem.find(".list-group-item-container").removeClass("hidden").css("display", "block");

                // Explicitly force the down arrow
                $changedItem.find('.list-view-pf-expand span.fa').removeClass('fa-angle-right').addClass('fa-angle-down');
            }

            // Monaco Diff - dynamically inject the button if the old_result exists.
            // Apply Diff-specific logic.
            //var viewType = 'diff';
            //if (viewType === 'diff' && item.state_change && item.state_change!== 'unchanged') {
                //... the existing badge/row highlighting code...

                // Inject the 'View Difference' button if old data exists
                if (item.state_change === 'changed' && item.old_result) {
                    var oldOutput = item.old_result.err || item.old_result.out || item.old_result || '';
                    var newOutput = item.result.err || item.result.out || '';

                    var $diffBtn = $('<button class="btn btn-default btn-sm btn-view-diff" style="margin-bottom: 10px;"><span class="fa fa-columns"></span> View Difference</button>');

                    // Safely attach the massive text blocks to the button's data object
                    $diffBtn.data('old-text', oldOutput);
                    $diffBtn.data('new-text', newOutput);

                    // Find the 'Output' definition term (<dt>) and prepend the button to the data (<dd>) below it
                    $changedItem.find('dt:contains("Output")').next('dd').prepend($diffBtn);
                }
            //}

        }
    });
}

$(document).ready(function() {

    // Initialize the selectpicker
    $('.selectpicker').selectpicker();
    let $compareFromSelect = $('#check-results-from-select');
    let $compareToSelect = $('#check-results-to-select');
//    $compareFromSelect.empty();
//    $compareToSelect.empty();
    // Command bootstrap-select to rebuild the visual UI
    $compareFromSelect.selectpicker('refresh');
    $compareToSelect.selectpicker('refresh');

    var sourceUrl = `/diff/${jsonDiffFile}`;

    if (jsonDiffFile && jsonDiffFile != '') {
        $.getJSON(sourceUrl, function(data) {
            window.reportData = data;
            renderDiffTable(data);
        });
    }

    // Initialize Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip();

    $('#submit-diff-btn').off('click').on('click', function () {
        const clusterId = $('#cluster-select option:selected').val();
        const clusterName = $('#cluster-select option:selected').text().trim();
        const checkResultsFrom = $('#check-results-from-select').val();
        const checkResultsTo = $('#check-results-to-select').val();
        const selectedDiff = $('#jsons').text();

        $.ajax({
            url: '/diff/async-task',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                cluster_id: clusterId,
                cluster_name: clusterName,
                check_results_from: checkResultsFrom,
                check_results_to: checkResultsTo,
                selected_diff_result: selectedDiff,
            }),
            beforeSend: function () {
                if (clusterId === undefined  || clusterId == ''){
                    $('#loading-icon').hide();
                    $('#submit-btn').prop('disabled', false);
                    $('#notification').text('');
                    warnMessage('warning','No cluster selected');
                    for (var i = 0; i < 3; i++) { // flash 3 times - refactor it
                        $('#cluster-select').fadeOut(250).fadeIn(1450);
                    }
                    return false;
                }
                $('#loading-icon').show();
                $('#submit-btn').prop('disabled', true);
            },
            success: function (resp) {
                console.info("Cluster compare check results success: ", clusterName);
                jsonFilesList = resp.json_diff_list;
                jsonDiffFile = resp.json_diff_file;
                jsonFile = resp.json_diff_file;

                //$('#diff-tab-nav').html(resp.diff_tab_nav);
                $('#result-container').html(resp.result_container);
                $('#notification').html(resp.notification);

                checkForFile(jsonDiffFile);
                /*  diff-result */
                if (resp.data) {
                    window.reportData = resp.data;
                    setTimeout(function() {
                        buildPage(window.reportData);
                        renderDiffTable(window.reportData);
                    }, 125);
                }
            },
            error: function (xhr, status, err) {
                console.error("AJAX error:", err);
                alert("AJAX error: " + err);
            },
            complete: function () {
                $('#loading-icon').hide();
                $('#submit-diff-btn').prop('disabled', false);
            }
        });
    });

//    // 4. Visual Decoration Logic
//    function renderDiffTable(data) {
//        var dataResults = data.results || {};
//
//        $.each(dataResults, function(hashId, item) {
//            if (item.state_change && item.state_change!== 'unchanged') {
//
//                // Safely scope the find specifically to the report body
//                var $changedItem = $('#report_table_risu_body').find('#plugin-' + hashId);
//
//                if ($changedItem.length > 0) {
//                    var badgeHtml = `<span class="diff-badge badge-${item.state_change}">${item.state_change.toUpperCase()}</span>`;
//
//                    $changedItem.addClass(`row-${item.state_change}`);
//
//                    // Only append the badge if it doesn't already exist to prevent duplicates on double-clicks
//                    if ($changedItem.find('.diff-badge').length === 0) {
//                        $changedItem.find('.list-group-item-heading').append(badgeHtml);
//                    }
//
//                    // Explicitly force the row open on load
//                    $changedItem.addClass("list-view-pf-expand-active");
//                    $changedItem.find(".list-group-item-container").removeClass("hidden").css("display", "block");
//
//                    // Explicitly force the down arrow
//                    $changedItem.find('.list-view-pf-expand span.fa').removeClass('fa-angle-right').addClass('fa-angle-down');
//                }
//            }
//        });
//    }

    // ========================================================================
    // 5. EVENT DELEGATION: Explicit State Machine
    // ========================================================================
    var $resultContainer = $('#result-container');

    $resultContainer.off('click', '.list-group-item-header').on('click', '.list-group-item-header', function(e) {
        e.stopPropagation();
        e.preventDefault();

        var $item = $(this).closest('.list-group-item');
        var $container = $item.find('.list-group-item-container');
        var $icon = $(this).find('.list-view-pf-expand span.fa');

        // EXPLICIT STATE CHECK: Determines exactly what to do instead of toggling blindly
        var isExpanded = $item.hasClass('list-view-pf-expand-active');

        if (isExpanded) {
            // Row is OPEN. We need to CLOSE it.
            $item.removeClass('list-view-pf-expand-active');
            $icon.removeClass('fa-angle-down').addClass('fa-angle-right'); // Force right arrow
            $container.stop(true, true).slideUp(200);
        } else {
            // Row is CLOSED. We need to OPEN it.
            $item.addClass('list-view-pf-expand-active');
            $icon.removeClass('fa-angle-right').addClass('fa-angle-down'); // Force down arrow
            $container.removeClass('hidden').stop(true, true).slideDown(200);
        }
    });

    $resultContainer.off('click', '.close').on('click', '.close', function(e) {
        e.stopPropagation();
        e.preventDefault();

        var $item = $(this).closest('.list-group-item');
        var $container = $item.find('.list-group-item-container');
        var $icon = $item.find('.list-view-pf-expand span.fa');

        // Explicitly close and force right arrow
        $item.removeClass('list-view-pf-expand-active');
        $icon.removeClass('fa-angle-down').addClass('fa-angle-right');
        $container.stop(true, true).slideUp(200);
    });

    // ========================================================================
    // Table Header Expand/Collapse (Metadata, Profiles, Report)
    // ========================================================================
    $("body").on("click", "#metadata_table_risu_header", function (e) {
      $("#metadata_table_risu_body").toggle();
    });
    $("body").on("click", "#profile_table_risu_header", function (e) {
      $("#profile_table_risu_body").toggle();
    });
    $("body").on("click", "#report_table_risu_header", function (e) {
      $("#report_table_risu_body").toggle();
    });
//    $("body").on('click', 'tr[id$="_header"]', function(e) {
//        e.preventDefault();
//
//        // 1. Get the ID of the clicked header (e.g., "metadata_table_risu_header")
//        var headerId = $(this).attr('id');
//
//        // 2. Dynamically construct the ID of the corresponding body
//        var bodyId = headerId.replace('_header', '_body');
//        var $body = $('#' + bodyId);
//
//        // 3. Toggle the visibility.
//        // Note: We use.toggle() instead of.slideToggle() because animating
//        // a <tbody> element's height often breaks table rendering in web browsers.
//        // $body.toggle(); - does not work instantly.
//        if($body.is(':visible') == true){
//            $body.hide();
//        }
//        else {
//            $body.show();
//        }
//    });

    // ========================================================================
    // 6. GLOBAL EXPAND/COLLAPSE ALL FIX
    // Replaces the default blind toggle with an explicit state machine
    // ========================================================================
    $(document).off('click', '#expandAll').on('click', '#expandAll', function(e) {
        // Prevent the original Risu script in diff-result.html from firing
        e.preventDefault();
        e.stopImmediatePropagation();

        var $btn = $(this);
        var isExpanding = $btn.text().trim() === 'Expand All';
        var $allRows = $('#report_table_risu_body .list-group');

        if (isExpanding) {
            // Intention: EXPAND. Find ONLY the rows that are currently closed.
            var $closedRows = $allRows.not('.list-view-pf-expand-active');

            $closedRows.addClass('list-view-pf-expand-active');
            $closedRows.find('.list-view-pf-expand span.fa').removeClass('fa-angle-right').addClass('fa-angle-down');
            $closedRows.find('.list-group-item-container').removeClass('hidden').stop(true, true).slideDown(200);

            // Update the button text for the next click
            $btn.text('Collapse All');
        } else {
            // Intention: COLLAPSE. Find ONLY the rows that are currently open.
            var $openRows = $allRows.filter('.list-view-pf-expand-active');

            $openRows.removeClass('list-view-pf-expand-active');
            $openRows.find('.list-view-pf-expand span.fa').removeClass('fa-angle-down').addClass('fa-angle-right');
            $openRows.find('.list-group-item-container').stop(true, true).slideUp(200);

            // Update the button text for the next click
            $btn.text('Expand All');
        }
    });

    // listener to trigger the Monaco Editor
    // Attach to the document so it survives AJAX reloads
    $(document).off('click', '.btn-view-diff').on('click', '.btn-view-diff', function(e) {
        e.preventDefault();
        var oldText = $(this).data('old-text');
        var newText = $(this).data('new-text');

        //require.config({
        //    baseUrl: 'http://localhost:5500/occode/static/vendor',
        //    paths: {'vs': 'monaco-editor/min/vs'}
        //});

        $('#monacoDiffModal').modal('show');

        // Monaco requires the container to be visible before it can calculate dimensions.
        // A slight delay ensures the Bootstrap modal animation has finished.
        setTimeout(function() {

            if (!window.diffEditor || !$('#monaco-diff-container').children() || $('#monaco-diff-container').children().length == 0) {
                window.diffEditor = monaco.editor.createDiffEditor(document.getElementById('monaco-diff-container'), {
                    theme: 'vs', /* 'vs-dark' */
                    readOnly: true,
                    automaticLayout: true // Automatically resizes if the user resizes their browser
                });
            }

            var originalModel = monaco.editor.createModel(oldText, "text/plain");
            var modifiedModel = monaco.editor.createModel(newText, "text/plain");

            window.diffEditor.setModel({ original: originalModel, modified: modifiedModel });

        }, 250);
    });


    $("body").on("click", ".relative-time-field", function (e) {
        var timeRangeField = $(this);
        debugger;
        var timeRangeValue = timeRangeField.data('rtfield');// timeRangeField.html();
        var timeRangeDescription = timeRangeField.text(); //timeRangeValue.toLowerCase();
        var sortbutton = $(this).parent().parent().parent().find("button");
        timeRangeField.parent().parent().find("li").removeClass("selected");
        timeRangeField.parent().addClass("selected");
        sortbutton.html(timeRangeDescription + ' <span class="caret"></span>');
        sortbutton.data("rtfield", timeRangeValue);
        calcTimeRange(timeRangeValue, timeRangeDescription);
    });

});
