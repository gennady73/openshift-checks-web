// ****************************
//  scripts for the home pages
// ****************************
var $clusterSelect = null;
var $resultsSelect = null;

// 4. Visual Decoration Logic
function renderDiffTable(data) {
}

// 4. Core AJAX Rendering Logic
function fetchAndRenderResults(clusterId, preselectResult) {

    clearAllTables();

    $.ajax({
        url: AppConfig.urls.listData,
        type: 'GET',
        data: { cluster_id: clusterId },
        dataType: 'json',
        success: function(response) {

            $resultsSelect.empty(); // Clear old options

            if (!response || response.length === 0) {
                $resultsSelect.empty().selectpicker('refresh');
                return true;
            }

            // Build the dropdown options dynamically
            $.each(response, function(index, artifact) {
                let dateStr = artifact.filename.replace('.json', '').replace(`-${clusterId}`, '');
                let displayName = moment(dateStr, "YYYYMMDD-HHmmss").format('YYYY-MM-DD HH:mm:ss');
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

/**
 * Toggle mark of "check result" file as "baseline" for comparison.
 * @param {string} checkResultFile - afile name of "check result"
 */
async function toggleBaseline(checkResultFile) {

  var $div_otherJsons = $("#otherJsons");
  const clusterId = $('#cluster-select option:selected').val();
  const selectedCheckResultFile = $("#otherJsons").val(); //$('#jsons').text();

  let rc = await $.ajax({
    url: '/baseline',
    type: "POST",
    dataType: "json",
    async: false,
    data: JSON.stringify({
      cluster_id: clusterId,
      selected_result: checkResultFile,
    }),
    beforeSend: function () {
        if (clusterId === undefined  || clusterId == '') {
            $('#loading-icon').hide();
            $('#submit-btn').prop('disabled', false);
            $('#notification').text('');

            warnMessage('warning','No cluster selected');

            for (var i = 0; i < 3; i++) { // flash 3 times - refactor it
                $('#project-location div > button > div.filter-option').fadeOut(250).fadeIn(750);
            }

            return false;
        }

      if(!selectedCheckResultFile && !checkResultFile) {
        warnMessage('danger','No file selected.');
        return false;
      }
      else if(selectedCheckResultFile && !checkResultFile) {
        checkResultFile = selectedCheckResultFile;
      }

      $('#loading-icon').show();
      $('#submit-btn').prop('disabled', true);

      console.log("Toggle Baseline");
    },
    success: function (data) {
       if (data.is_baseline == true) {
            console.log("Baseline set on : ", checkResultFile);
       }
       else if (data.is_baseline == false) {
            console.log("Baseline removed from : ", checkResultFile);
       }

    },
    error: function (xhr, status, err) {
        console.error("AJAX error:", err);
        warnMessage('danger','No file selected.', err);
    },
  });

    console.log("toggle-baseline-btn : ", rc);
}

$(document).ready(function() {
    // Initialize Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // 1. Read Configuration & Session State securely from the DOM
    AppConfig.urls.listData = $('#app-context').data('api-list');
    AppConfig.state.cluster = $('#app-context').data('active-cluster');
    AppConfig.state.result = $('#app-context').data('active-result');

    $clusterSelect = $('#cluster-select');
    $resultsSelect = $('#otherJsons');

    // 2. Initial Application Load: Sync UI with Backend Session
    if (AppConfig.state.cluster) {
        // Forces the cluster combo to show the active session cluster
        $clusterSelect.val(AppConfig.state.cluster).selectpicker('refresh');
        fetchAndRenderResults(AppConfig.state.cluster, AppConfig.state.result);
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

    $clusterSelect.on('change', function() {
        let newCluster = $(this).val();
        AppConfig.state.cluster = newCluster;
        AppConfig.state.result = null; // Reset the result when switching clusters

        if (newCluster) {
            fetchAndRenderResults(newCluster, '');
        } else {
            setEmptyState();
        }
    });

    $resultsSelect.on('change', function() {
        let selectedResult = $(this).val();
        AppConfig.state.result = selectedResult;
        loadReportTables(selectedResult);
    });

    $("body").on("click", "#toggle-baseline-btn", function (e) {
        debugger;
        console.log("toggle-baseline-btn");
        toggleBaseline($('#otherJsons').val()); // jsonFile
    });

    $('#submit-btn').on('click', function () {
        const clusterId = $('#cluster-select option:selected').val();
        const clusterName = $('#cluster-select option:selected').text().trim();
        let selectedResult = '';

        $.ajax({
            url: '/async-task',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                cluster_id: clusterId,
                cluster_name: clusterName,
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
                AppConfig.state.result = resp.json_check_file;
                AppConfig.state.cluster = resp.cluster_id;
                fetchAndRenderResults(AppConfig.state.cluster, AppConfig.state.result);
                $resultsSelect.val(AppConfig.state.result).selectpicker('refresh');
                selectedResult = $resultsSelect.val();
                AppConfig.state.result = selectedResult;
                window.reportData = resp.data;
                console.info("Cluster get check results success: %s. Filename: %s", clusterName, selectedResult);
                loadReportTables(selectedResult);
            },
            error: function (xhr, status, err) {
                console.error("AJAX error:", err);
                alert("AJAX error: " + err);
            },
            complete: function () {
                $('#loading-icon').hide();
                $('#submit-btn').prop('disabled', false);
            }
        });

    });

});
