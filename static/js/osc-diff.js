// ****************************
//  scripts for the diff pages
// ****************************
var $clusterSelect = null;
var $resultsSelect = null;
var $compareFromSelect = null;
var $compareToSelect = null;

var $compareFromSelectList = [];

async function buildTimeRangeList(srcDateTimeList, splitDateTime, splitBefore=true) {

    if(!srcDateTimeList || !splitDateTime || splitDateTime.trim == '') {
        return [];
    }

    console.log('Build TimeRange List (split)  : ', splitDateTime);

    //return srcDateTimeList.filter(item => item.filename > splitDateTime);

    const index = srcDateTimeList.findIndex(item => item.filename == splitDateTime);

    if (index == -1) {
        return [];
    }

    const isSplitBefore = (splitBefore === true || splitBefore === false )? splitBefore : true;

    if (isSplitBefore === true) {
        const before = srcDateTimeList.slice(0, index);
        console.log('Build TimeRange List (before) : ', before);
        return before;
    }
    else {
        const after = srcDateTimeList.slice(index);
        console.log('Build TimeRange List (after)  : ', after);
        return after;
    }
    return [];
}

async function calcTimeRange(timeRangeValue, timeRangeDescription) {
    let selectedRange = timeRangeValue;
    const clusterId = $('#cluster-select option:selected').val();

    if (clusterId === undefined  || clusterId == ''){
        $('#loading-icon').hide();
        $('#submit-btn').prop('disabled', false);
        $('#notification').text('');
        warnMessage('warning','No cluster selected');
        for (var i = 0; i < 3; i++) { // flash 3 times - refactor it
            $('#project-location div > button > div.filter-option').fadeOut(250).fadeIn(750);
        }
        return false;
    }

    // Default bounds
    let fromDate = null;
    let toDate = moment();

    // Calculate the 'From' boundary if a specific relative time is chosen
    if (selectedRange && selectedRange != '') {
        let parts = selectedRange.split('-');
        let amount = parseInt(parts, 10);
        let unit = parts[1];
        fromDate = moment().subtract(amount, unit);
    }
    else {
        console.error('The selected Time Range is not valid: %s', selectedRange);
        $('#loading-icon').hide();
        $('#submit-btn').prop('disabled', false);
        $('#notification').text('');
        warnMessage('warning',`The selected Time Range is not valid: ${selectedRange}.`);
        return false;
    }

    // Format dates to strictly match the Python strptime format (YYYYMMDD-HHMMSS)
    // Send an empty string if fromDate is null (meaning "All Time")
    let payload = {
        cluster_id: clusterId,
        start_date: fromDate? fromDate.format('YYYYMMDD-HHmmss') : '',
        end_date: toDate.format('YYYYMMDD-HHmmss')
    };

    rc = await $.ajax({
        url: '/diff/data/list/from', // Ensure this matches your unified Python route
        type: 'GET',
        data: payload,
        dataType: 'json',
        success: function(data) {
//            $compareFromSelect = $('#check-results-from-select');
//            $compareToSelect = $('#check-results-to-select');

            // Empty the native select dropdowns
            $compareFromSelect.empty();
            $compareToSelect.empty();

            // Iterate over the returned JSON objects
            $.each(data, function(index, artifact) {
                // Strip '.json' from the display name to match timestamp
                let dateStr = artifact.filename.replace('.json', '').replace(`-${clusterId}`, '');
                let displayName = moment(dateStr, "YYYYMMDD-HHmmss").format('YYYY-MM-DD HH:mm:ss');

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
            return true;
        },
        error: function(xhr, status, error) {
            console.error("Failed to fetch filtered artifacts: ", error);
            warnMessage("danger", `Failed to fetch filtered artifacts. ${error}`);
            return false;
        }
    });

    return rc;
}

function buildCombo(data, $selecElementRef, clusterId) {
//            $compareFromSelect = $('#check-results-from-select');
//            $compareToSelect = $('#check-results-to-select');

            if (!data || !$selecElementRef || !clusterId) {
                console.log('One or more arguments are missing to build a combobox.');
                return;
            }

            // Empty the native select dropdowns
            $selecElementRef.empty();

            // Iterate over the returned JSON objects
            $.each(data, function(index, artifact) {
                // Strip '.json' from the display name to match timestamp
                let dateStr = artifact.filename.replace('.json', '').replace(`-${clusterId}`, '');
                let displayName = moment(dateStr, "YYYYMMDD-HHmmss").format('YYYY-MM-DD HH:mm:ss');

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

                $selecElementRef.append(optionHTML.clone());
            });

            // Command bootstrap-select to rebuild the visual UI
            $selecElementRef.selectpicker('refresh');
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

// 4. Core AJAX Rendering Logic
function fetchAndRenderResults(clusterId, preselectResult) {

    clearAllTables();

    $.ajax({
        url: AppConfig.urls.diff.listData,
        type: 'GET',
        data: { cluster_id: clusterId },
        dataType: 'json',
        success: function(data) {

            $resultsSelect.empty(); // Clear old options

            if (!data || data.length === 0) {
                $resultsSelect.empty().selectpicker('refresh');
                $compareFromSelectList = [];
                return true;
            }

            // Build the dropdown options dynamically
            $.each(data, function(index, artifact) {
                let diffDates = artifact.filename.replace('_diff.json', '').replaceAll(`-${clusterId}`, '').split('_to_');
                let dateStrFrom = moment(diffDates[0], "YYYYMMDD-HHmmss").format('YYYY-MM-DD HH:mm:ss');
                let dateStrTo = moment(diffDates[1], "YYYYMMDD-HHmmss").format('YYYY-MM-DD HH:mm:ss');
                let displayName = dateStrFrom + ' <b>&#9205;&#9205;</b> ' + dateStrTo;
                let $option = $('<option></option>').val(artifact.filename);

                if (artifact.is_baseline) {
                    let customHtml = displayName + ' <span style="color: #f0ab00;"><b>&#9733; baseline</b></span>';
                    $option.attr('data-content', customHtml);
                    $option.text(displayName + ' (baseline)');
                } else {
                    $option.attr('data-content', displayName);
                    $option.text(displayName);
                }

                $resultsSelect.append($option);
            });

            // Re-enable combo and apply the session-saved value if it exists
            $resultsSelect.prop('disabled', false);
            if (preselectResult) {
                // the only working combination.- following two rows together.
                $resultsSelect.val(preselectResult).selectpicker('refresh');
                $resultsSelect.selectpicker('val', preselectResult);
            }

            console.log("Pre-select Result: ", preselectResult);

            // Force bootstrap-select to rebuild the UI
            $resultsSelect.selectpicker('refresh');
        },
        error: function(xhr, status, error) {
            console.error("Failed to load results for cluster: ", error);
            $resultsSelect.empty().selectpicker('refresh');
        }
    });

    // reload the time-range combos "From" "To"
    // Format dates to strictly match the Python strptime format (YYYYMMDD-HHMMSS)
    // Send an empty string if fromDate is null (meaning "All Time")
    let payload = {
        cluster_id: clusterId,
        start_date: '',
        end_date: '',
    };

    $.ajax({
        url: '/diff/data/list/from', // Ensure this matches your unified Python route
        type: 'GET',
        data: payload,
        dataType: 'json',
        success: function(data) {
            $compareFromSelect = $('#check-results-from-select');
            $compareToSelect = $('#check-results-to-select');

            // Empty the native select dropdowns
            $compareFromSelect.empty();
            $compareToSelect.empty();
            $compareFromSelectList = JSON.parse(JSON.stringify(data));

            // Iterate over the returned JSON objects
            $.each(data, function(index, artifact) {
                // Strip '.json' from the display name to match timestamp
                let dateStr = artifact.filename.replace('.json', '').replace(`-${clusterId}`, '');
                let displayName = moment(dateStr, "YYYYMMDD-HHmmss").format('YYYY-MM-DD HH:mm:ss');

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

            // the only working combination.- following two rows together.
            $compareFromSelect.val(AppConfig.state.diff.resultFrom).selectpicker('refresh');
            $compareFromSelect.selectpicker('val', AppConfig.state.diff.resultFrom);

            // the only working combination.- following two rows together.
            $compareToSelect.val(AppConfig.state.diff.resultTo).selectpicker('refresh');
            $compareToSelect.selectpicker('val', AppConfig.state.diff.resultTo);
        },
        error: function(xhr, status, error) {
            console.error("Failed to fetch filtered artifacts: ", error);
            // Optional: You could trigger a PatternFly Toast here to notify the user of a network error
        }
    });

}

function setEmptyState() {
    // Ensures the dropdown says "Select check result" and cannot be opened
    $resultsSelect.empty().prop('disabled', true).selectpicker('refresh');

    // hide/empty Metadata and Report tables here:
    clearAllTables();
}

function loadReportTables(selectedValue) {
    console.log('Selected Value:', selectedValue);
    var reqUrl = `${[location.protocol, "//", location.host, location.pathname].join("")}${selectedValue}`;
    // Here we load the data from risu.json with ajax and we populate the webpage
    $.ajax({
      url: reqUrl,
      dataType: "json",
      beforeSend: function () {
        if (!selectedValue || selectedValue == '') return false; //cancel request
        $("#report_table_risu_body").append(
          '<tr id="loading"><td>Loading ' +
            selectedValue +
            '... <span class="fa fa-refresh"/></td></tr>'
        );
      },
      success: function(data) {
        buildPage(data); renderDiffTable(data);
      }, // ajax success
      error: function (jqXHR, exception) {
        console.log(jqXHR);
        if (jqXHR.status === 0) {
          warnMessage("danger", "Unable to get JSON file. [0]");
        } else if (jqXHR.status == 404) {
          warnMessage("danger", `Requested JSON file '${selectedValue}' was not found.`);
        } else if (jqXHR.status == 500) {
          warnMessage("danger", "Internal Server Error [500].");
        } else if (exception === "parsererror") {
          warnMessage("danger", "Requested JSON parse failed.");
        } else if (exception === "timeout") {
          warnMessage("danger", "Time out error.");
        } else if (exception === "abort") {
          warnMessage("danger", "Ajax request aborted.");
        } else {
          warnMessage("danger", "Uncaught Error.\n" + jqXHR.responseText);
        }
      },
      complete: function () {
        var $loadingRow = $("#report_table_risu_body tr#loading");
        $loadingRow.remove(); // Clean up UI regardless of success/error
      }, // ajax complete
    }); // ajax query
}

$(document).ready(function() {
    // Initialize Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Initialize the selectpicker
    $('.selectpicker').selectpicker();

    // 1. Read Configuration & Session State securely from the DOM
    AppConfig.urls.diff.listData = $('#app-context').data('api-list');
    AppConfig.state.cluster = $('#app-context').data('active-cluster');
    AppConfig.state.result = $('#app-context').data('active-result');
    AppConfig.state.diff.result = $('#app-context').data('diff-active-result')
    AppConfig.state.diff.resultFrom = $('#app-context').data('diff-active-result-from')
    AppConfig.state.diff.resultTo = $('#app-context').data('diff-active-result-to')

    $clusterSelect = $('#cluster-select');
    $resultsSelect = $('#otherJsons');
    $compareFromSelect = $('#check-results-from-select');
    $compareToSelect = $('#check-results-to-select');

    // 2. Initial Application Load: Sync UI with Backend Session
    if (AppConfig.state.cluster) {
        // Forces the cluster combo to show the active session cluster
        $clusterSelect.val(AppConfig.state.cluster).selectpicker('refresh');
        fetchAndRenderResults(AppConfig.state.cluster, AppConfig.state.diff.result);
    } else {
        // Enforce the completely empty default state
        setEmptyState();
    }

    // 3. Bind Event Listeners

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

    // listener to trigger the Monaco Editor
    // Attach to the document so it survives AJAX reloads
    $(document).on('click', '.btn-view-diff', function(e) {
        e.preventDefault();
        var oldText = $(this).data('old-text');
        var newText = $(this).data('new-text');

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

//    $("#relativeTimeFilter").on("change", function (e) {
//        var timeRangeField = $(this);
//        
//        var timeRangeValue = timeRangeField.data('rtfield');// timeRangeField.html();
//        var timeRangeDescription = timeRangeField.text(); //timeRangeValue.toLowerCase();
//        var sortbutton = $(this).parent().parent().parent().find("button");
//        timeRangeField.parent().parent().find("li").removeClass("selected");
//        timeRangeField.parent().addClass("selected");
//        sortbutton.html(timeRangeDescription + ' <span class="caret"></span>');
//        sortbutton.data("rtfield", timeRangeValue);
//        calcTimeRange(timeRangeValue, timeRangeDescription);
//    });
    $("#relativeTimeFilter").on("change", function (e) {
        var timeRangeField = $(this);
        
        var timeRangeValue = timeRangeField.val()
        var timeRangeDescription = timeRangeField.find("option:selected").text();
        let rc = false;
        calcTimeRange(timeRangeValue, timeRangeDescription).then((val)=>{
            rc = val;
            console.log(`val=${rc}`);
        });
        return rc;
    });

    $clusterSelect.on('change', function() {
        let newCluster = $(this).val();
        AppConfig.state.cluster = newCluster;
        console.log('*** CLUSTER CHANGED : %s', newCluster);

        if (newCluster) {
            AppConfig.state.result = null; // Reset the result when switching clusters
            AppConfig.state.diff.result = null; // Reset the result when switching clusters
            AppConfig.state.diff.resultFrom = null; // Reset the result when switching clusters
            AppConfig.state.diff.resultTo = null; // Reset the result when switching clusters
            fetchAndRenderResults(newCluster, '');
        } else {
            setEmptyState();
        }
    });

    $compareFromSelect.on('change', function() {
        let selectedResult = $(this).val();
        console.log("CompareFrom selected : ", selectedResult);
        if(selectedResult) {
            AppConfig.state.diff.resultFrom = selectedResult;
            buildTimeRangeList($compareFromSelectList, selectedResult)
                .then(result  => {
                console.log("compareToList : ", result);
                buildCombo(result, $compareToSelect, AppConfig.state.cluster);
                $compareToSelect.val(AppConfig.state.diff.resultTo).selectpicker('refresh');
            });
        }
    });

    $compareToSelect.on('change', function() {
        let selectedResult = $(this).val();
        console.log("CompareTo selected   : ", selectedResult);
        if(selectedResult) {
            AppConfig.state.diff.resultTo = selectedResult;
        }
    });

    $resultsSelect.on('change', function() {
        let selectedResult = $(this).val();

        if(selectedResult === undefined || selectedResult == null || selectedResult.trim() == '') {
            return false;
        }

        AppConfig.state.diff.result = selectedResult;

        // reverse check result files from diff result filename
        let clusterId = AppConfig.state.cluster;
        let diffDates = selectedResult.replace('_diff.json', '').replaceAll(`-${clusterId}`, '').split('_to_');

        let dateStrFrom = `${diffDates[0]}-${clusterId}.json`;
        AppConfig.state.diff.resultFrom = dateStrFrom;
        $compareFromSelect.val(AppConfig.state.diff.resultFrom).selectpicker('refresh');
        $compareFromSelect.selectpicker('val', AppConfig.state.diff.resultFrom);

        let dateStrTo = `${diffDates[1]}-${clusterId}.json`;
        AppConfig.state.diff.resultTo = dateStrTo;
        $compareToSelect.val(AppConfig.state.diff.resultTo).selectpicker('refresh');
        $compareToSelect.selectpicker('val', AppConfig.state.diff.resultTo);


//        const clusterId = $('#cluster-select option:selected').val();
        const clusterName = $('#cluster-select option:selected').text().trim();
        const checkResultsFrom = $('#check-results-from-select').val();
        const checkResultsTo = $('#check-results-to-select').val();

        $.ajax({
            url: '/diff/data/state',
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({
                cluster_id: clusterId,
                cluster_name: clusterName,
                check_results_from: checkResultsFrom,
                check_results_to: checkResultsTo,
                selected_diff_result: selectedResult,
            }),
            beforeSend: function () {
                if (clusterId === undefined  || clusterId == ''){
                    $('#loading-icon').hide();
                    $('#submit-btn').prop('disabled', false);
                    $('#notification').text('');
                    warnMessage('warning','No cluster selected');
                    for (var i = 0; i < 3; i++) { // flash 3 times - refactor it
                        $('#project-location div > button > div.filter-option').fadeOut(250).fadeIn(750);
                    }
                    return false;
                }
                $('#loading-icon').show();
                $('#submit-btn').prop('disabled', true);
            },
            success: function (resp) {
//                $('#notification').html(resp.notification);
//                $resultsSelect.val(resp.json_diff_file).selectpicker('refresh'); // jsonFile
//                selectedResult = $resultsSelect.val();
//                if(!selectedResult || selectedResult != resp.json_diff_file) {
//                    selectedResult = resp.json_diff_file;
//                }
//                AppConfig.state.diff.result = selectedResult;
//                window.reportData = resp.data;
//                jsonFilesList = resp.json_diff_list;
//                jsonDiffFile = resp.json_diff_file;
//                console.info("Cluster compare check results success: %s", clusterName);
//                fetchAndRenderResults(AppConfig.state.cluster, AppConfig.state.diff.result);
//                loadReportTables(selectedResult);
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

        loadReportTables(selectedResult);
    });

    $('#submit-diff-btn').on('click', function () {
        const clusterId = $('#cluster-select option:selected').val();
        const clusterName = $('#cluster-select option:selected').text().trim();
        const checkResultsFrom = $('#check-results-from-select').val();
        const checkResultsTo = $('#check-results-to-select').val();
        let selectedResult = ''; // const selectedDiff = $('#jsons').text();

        $.ajax({
            url: '/diff/async-task',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                cluster_id: clusterId,
                cluster_name: clusterName,
                check_results_from: checkResultsFrom,
                check_results_to: checkResultsTo,
                selected_diff_result: selectedResult,
            }),
            beforeSend: function () {
                if (clusterId === undefined  || clusterId == ''){
                    $('#loading-icon').hide();
                    $('#submit-btn').prop('disabled', false);
                    $('#notification').text('');
                    warnMessage('warning','No cluster selected');
                    for (var i = 0; i < 3; i++) { // flash 3 times - refactor it
                        $('#project-location div > button > div.filter-option').fadeOut(250).fadeIn(750);
                    }
                    return false;
                }
                $('#loading-icon').show();
                $('#submit-btn').prop('disabled', true);
            },
            success: function (resp) {
                $('#notification').html(resp.notification);
                $resultsSelect.val(resp.json_diff_file).selectpicker('refresh'); // jsonFile
                selectedResult = $resultsSelect.val();
                if(!selectedResult || selectedResult != resp.json_diff_file) {
                    selectedResult = resp.json_diff_file;
                }
                AppConfig.state.diff.result = selectedResult;
                window.reportData = resp.data;
                jsonFilesList = resp.json_diff_list;
                jsonDiffFile = resp.json_diff_file;
                console.info("Cluster compare check results success: %s", clusterName);
                fetchAndRenderResults(AppConfig.state.cluster, AppConfig.state.diff.result);
                loadReportTables(selectedResult);
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

});
