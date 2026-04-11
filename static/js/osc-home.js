// ****************************
//  scripts for the home pages
// ****************************

// 4. Visual Decoration Logic
function renderDiffTable(data) {
}


$(document).ready(function() {
    var sourceUrl = `${jsonFile}`;
debugger; // osc-home
    $.getJSON(sourceUrl, function(data) {
        window.reportData = data;
        renderDiffTable(data);
    });

    // Initialize Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip();

    $('#submit-btn').off('click').on('click', function () {
        const clusterId = $('#cluster-select option:selected').val();
        const clusterName = $('#cluster-select option:selected').text().trim();
        const checkResultsFrom = $('#check-results-from-select').val();
        const checkResultsTo = $('#check-results-to-select').val();
        const selectedResult = $('#jsons').text();

        $.ajax({
            url: '/async-task',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                cluster_id: clusterId,
                cluster_name: clusterName,
                check_results_from: checkResultsFrom,
                check_results_to: checkResultsTo,
                selected_result: selectedResult,
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
                console.info("Cluster get check results success: ", clusterName);
                jsonFilesList = resp.json_check_list;
                jsonFile = resp.json_check_file;

                //$('#home-tab-nav').html(resp.home_tab_nav);
                $('#result-container').html(resp.result_container);
                $('#notification').html(resp.notification);

                checkForFile(jsonFile);
                /* check-result */
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
                $('#submit-btn').prop('disabled', false);
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
        // Prevent the original Risu script in result.html from firing
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

    // ========================================================================
    // 7. GLOBAL FILTER BT TEXT ALL FIX
    // Replaces the default blind toggle with an explicit state machine
    // ========================================================================
    //
    // listener when the user picks a status filter
    $("body").off("change", ".nx-filter-status").on("change", ".nx-filter-status", function (e) {
    filterCards();
    });

    // listener when the user writes in the searchbox
    $(document).off("keyup", "#filter_text").on("keyup", "#filter_text", function(e) {
        filterCards();
    });

});
