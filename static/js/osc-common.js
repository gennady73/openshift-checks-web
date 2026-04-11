// ****************************
//  scripts for all pages
// ****************************

// Initialize Bootstrap tooltips
$('[data-toggle="tooltip"]').tooltip();

// "Config" osc-common.js
// text search minimum characters before we fire the search
var ft_min_char = 3;
// List of json files we're looking
var jsonFilesList = []; //["osc.json", "risu.json", "magui.json", "citellus.json"];

// fill the list

$.ajax({
  url: `${[location.protocol, "//", location.host, location.pathname].join("")}data/list`, // "/diff/data/list",
  type: "GET",
  async: false,
  beforeSend: function () {
    return (!$('#home-settings-tab.active') || $('#home-settings-tab.active').length == 0)? true : false;
  },
  success: function(response) {
    jsonFilesList = response;
    console.debug("jsonFilesList = ", jsonFilesList);
  },
  error: function(xhr) {
    console.error("Error fetching data");
  }
});


var plugin_cats_array = new Array();
var server_array = new Array();

var jsonFile = '';
var jsonDiffFile = '';

//var mypath = window.location.pathname;
//      //////////////////////////////
//      console.log('mypath', mypath);
//var mypage = mypath.split("/").pop();
//      //////////////////////////////
//      console.log('mypage', mypage);
//var myname = mypage.split(".")[0];
//      //////////////////////////////
//      console.log('myname', myname);
//myname = myname === '' ? jsonDiffFile : myname; // 'osc'
//            //////////////////////////////
//      console.log('myname(default)', myname);
// Append html file as fallback
//jsonFilesList.push(myname.concat(".json"));

// Visual Decoration Logic
function renderDiffTable(data) {
  // must be overrided, when need some additional rendering.
}

// function to get query string
function getParameterByName(name) {
  var match = RegExp("[?&]" + name + "=([^&]*)").exec(
    window.location.search
  );
  return match && decodeURIComponent(match[1].replace(/\+/g, " "));
}

// function that filters the unique values of an array
function onlyUnique(value, index, self) {
  return self.indexOf(value) === index;
}

// function to either check or uncheck all categories
function checkAllCat(checked) {
  $(".check-category").each(function (i, j) {
    $(this).prop("checked", checked);
  });
  $("#check_all").prop("checked", checked);
  filterCards();
}

// function that applies all possible filters.
// it's called whenever a filter is triggered.
function filterCards() {
  var count = 0;
  var filter_status = [];
  $(".nx-filter-status:checkbox:checked").each(function () {
    filter_status.push($(this).data("filter"));
  });
  var filter_text = $("#filter_text").val();
  var filter_category = "";
  $(".check-category").each(function (i, j) {
    if ($(this).prop("checked")) {
      filter_category += $(this).attr("name") + "|";
    }
  });

  filter_category = filter_category.slice(0, -1);
  var cb_regex = new RegExp(filter_category);
  $("#list-group > div").each(function (i, j) {
    var plugin_cats = $(this).data("categories");
    var plugin_txt = $(this).children(".plugin-error").first().text();
    var plugin_name = $(this).data("name").toString();
    var plugin_status = $(this).data("state");
    // Validations:
    // - if plugin categories match regex of checked categories
    // - if plugin state match status filter
    // - if plugin (name|text) match text filter, only if there's at least $ft_min_char char
    if (
      cb_regex.test(plugin_cats) &&
      /[A-z0-9]+/.test(cb_regex) &&
      filter_status.includes($(this).data("state")) &&
      (filter_text.length < ft_min_char ||
        (filter_text.length >= ft_min_char &&
          plugin_txt &&
          plugin_txt.toLowerCase().indexOf(filter_text) != -1) ||
        (plugin_name &&
          plugin_name.toLowerCase().indexOf(filter_text) != -1))
    ) {
      $(this).show();
      count += 1;
    } else {
      $(this).hide();
    }
  });
  $("#numresults").html(count);
}

// function that returns various metadata depending on RC
function getPluginState(rc, priority) {
  var plugin_icon;
  var plugin_state;
  var plugin_class;
  var plugin_text_color;
  var plugin_badge;
  if (rc == 30) {
    plugin_icon = "fa fa-angle-double-right";
    plugin_state = "skipped";
    plugin_class = "skipped";
    plugin_text_color = "gray";
  } else if (rc == 40) {
    plugin_icon = "pficon pficon-info";
    plugin_state = "info";
    plugin_class = "info";
    plugin_text_color = "blue";
  } else if (rc == 10) {
    plugin_icon = "fa fa-check-circle-o";
    plugin_state = "okay";
    plugin_class = "success";
    plugin_text_color = "";
  } else {
    plugin_state = "failed";
    plugin_class = "danger";
    plugin_text_color = "";
    if (priority >= 666) {
      plugin_icon = "pficon pficon-error-circle-o";
    } else if (priority >= 333) {
      plugin_icon = "pficon pficon-warning-triangle-o";
    } else {
      plugin_icon = "pficon pficon-info";
      plugin_text_color = "red";
    }
  }
  plugin_badge =
    '<span class="badge badge-pill badge-' +
    plugin_class +
    '">' +
    plugin_state +
    "</span>";
  return {
    icon: plugin_icon,
    state: plugin_state,
    pclass: plugin_class,
    text_color: plugin_text_color,
    badge: plugin_badge,
  };
}

// function that returns pluging names and category
function getPluginNames(item) {
  var plugin_long_name = "";
  var plugin_re = /plugins\/[^\/]+\/(.*)\/([^\/]+)\.[A-z0-9]+$/;
  var plugin_name = item.name;
  var plugin_cat = "";
  if (plugin_re.test(item.plugin)) {
    plugin_cat = plugin_re.exec(item.plugin)[1];
  } else {
    plugin_cat = "magui";
  }
  if (
    /[A-z0-9]+/.test(item.long_name) &&
    !/^undefined$/.test(item.long_name)
  ) {
    plugin_long_name = item.long_name;
  } else {
    plugin_long_name = plugin_name;
  }
  return {
    name: plugin_name,
    long_name: plugin_long_name,
    cat: plugin_cat,
  };
}

// function that parses the plugin cat returned by getPluginNames and return a visual and populates global array
function getPluginCats(cat, subcat) {
  var plugin_cats_visual = "";
  var plugin_cats_list = "";
  var plugin_cats = subcat.split("/");
  if (plugin_cats[0] != cat) {
    plugin_cats.unshift(cat);
  }
  $.each(plugin_cats, function (c, cname) {
    if (cname != "undefined") {
      plugin_cats_visual +=
        '<a href="#" data-category="' +
        cname +
        '" class="label label-primary category-badge">' +
        cname +
        "</a> ";
      plugin_cats_list += cname + ",";
      plugin_cats_array.push(cname);
    }
  });

  plugin_cats_list = plugin_cats_list.slice(0, -1);
  return {
    list: plugin_cats_list,
    visual: plugin_cats_visual,
  };
}

function sortPlugins(sortkey) {
  var mylist = $("#list-group");
  var listitems = mylist.children("div .list-group-item").get();
  var sortdirection = $("#sortDirection").data("direction");
  listitems.sort(function (a, b) {
    if (sortkey == "priority") {
      if (sortdirection == "desc") {
        return $(b).data(sortkey) - $(a).data(sortkey);
      } else {
        return $(a).data(sortkey) - $(b).data(sortkey);
      }
    } else {
      if (sortdirection == "desc") {
        return $(a)
          .data(sortkey)
          .toString()
          .localeCompare($(b).data(sortkey).toString());
      } else {
        return $(b)
          .data(sortkey)
          .toString()
          .localeCompare($(a).data(sortkey).toString());
      }
    }
  });
  $.each(listitems, function (idx, itm) {
    mylist.append(itm);
  });
}

// Get profile counts #FIXME
function getProfileCounts(plugins) {
  var pieskip = 0;
  var piepass = 0;
  var pieerr = 0;
  var pieinfo = 0;
  var pietotal = 0;

  $.each(plugins, function (i, p) {
    var plugin_state = getPluginState(p.rc, p.priority);
    if (plugin_state.state == "okay") {
      piepass += 1;
    } else if (plugin_state.state == "failed") {
      pieerr += 1;
    } else if (plugin_state.state == "skipped") {
      pieskip += 1;
    } else if (plugin_state.state == "info") {
      pieinfo += 1;
    }
  });
  var pieData = {
    type: "pie",
    colors: {
      Failed: "#cc0000",
      Info: "#2b18f9",
      Skipped: "#d1d1d1",
      Okay: "#3f9c35",
    },
    columns: [
      ["Failed", pieerr],
      ["Okay", piepass],
      ["Skipped", pieskip],
      ["Info", pieinfo],
    ],
    pietotal: pieskip + piepass + pieerr + pieinfo,
  };
  return pieData;
}

// Formats the profile table from the object stored in the err field of the check
function printProfileTable(plugins) {
  var row = "";
  row +=
    '                <table class="table table-striped table-bordered table-hover table-condensed">\n';
  row += "                   <thead>\n";
  row += "                      <tr>\n";
  row += "                        <th>Server</th>\n";
  row += "                        <th>Plugin</th>\n";
  row += "                        <th>Status</th>\n";
  row += "                        <th>Message</th>\n";
  row += "                     </tr>\n";
  row += "                  </thead>\n";
  row += "                  <tbody>\n";
  $.each(plugins, function (i, p) {
    var plugin_state = getPluginState(p.rc, p.priority);
    row +=
      "                <tr><td>" +
      p.hostname +
      '</td><td><a href="#plugin-' +
      p.plugin_id +
      '">' +
      p.plugin_name +
      "</a></td><td>" +
      plugin_state.badge;
    if (p.msg == "") {
      row += "</td><td>" + p.msg + "</td></tr>\n";
    } else {
      row += "</td><td><pre>" + p.msg + "</pre></td></tr>\n";
    }
  });
  row += "                  </tbody>\n";
  row += "              </table>\n";
  return row;
}

// function that generates a row to add to the accordion
function printRisuPlugin(
  result,
  out,
  err,
  rc,
  data,
  plugin_var_name = false
) {
  var plugin_names = getPluginNames(result);
  if (plugin_var_name == "metadata-outputs") {
    plugin_names.cat = "metadata";
  }
  var plugin_cats = getPluginCats(result.category, result.subcategory);
  var plugin_state = getPluginState(rc, result.priority);
  if (result.priority == "undefined") {
    result.priority = 0;
  }
  if (result.backend != "profile") {
    // Converting the links to html
    if (Array.isArray(err)) {
      err = err.join();
    }
    var error_text = err.replace(
      /\bhttp[s]*:\/\/([^\s]+)+\b/gi,
      '<a href="$&" target="_blank">$&</a>'
    );
  }

  var c3ChartDefaults = $().c3ChartDefaults();
  var pieChartSmallConfig = c3ChartDefaults.getDefaultPieConfig();

  pieChartSmallConfig.legend = {
    show: true,
    position: "right",
  };
  pieChartSmallConfig.size = {
    width: 260,
    height: 115,
  };

  var itisprofile = 0;
  var item_id = result.id;
  var row = "";
  // we build the text that is going to be appended to the container
  row +=
    '        <div class="list-group-item" data-priority="' +
    result.priority +
    '" data-state="' +
    plugin_state.state +
    '" data-name="' +
    plugin_names.name +
    '" data-categories="' +
    plugin_cats.list +
    '" id="plugin-' +
    item_id +
    '">\n';
  row +=
    '         <textarea class="plugin-error" style="display: none;">' +
    err +
    "</textarea>\n";
  row += '         <div class="list-group-item-header">\n';
  row += '          <div class="list-view-pf-expand">\n';
  row += '           <span class="fa fa-angle-right"></span>\n';
  row += "          </div> <!-- /list-view-pf-expand -->\n";
  row += '          <div class="list-view-pf-main-info">\n';
  row += '           <div class="list-view-pf-left">\n';
  row +=
    '            <span class="' +
    plugin_state.icon +
    '" title="' +
    plugin_state.state +
    '" style="color: ' +
    plugin_state.text_color +
    '"></span>';
  row += "           </div><!-- /list-view-pf-left -->\n";
  row += '           <div class="list-view-pf-body">\n';
  row += '            <div class="list-view-pf-description">\n';
  row +=
    '             <div class="list-group-item-heading">' +
    plugin_names.name +
    "</div>\n";
  row +=
    '             <div class="list-group-item-text pull-left">' +
    plugin_names.long_name +
    "</div>\n";
  row += "            </div><!-- /list-view-pf-description -->\n";
  row +=
    '             <div class="list-view-pf-additional-info-item" style="width: 25%">\n';
  row += "              " + plugin_cats.visual;
  row +=
    "             </div> <!-- /list-view-pf-additional-info-item -->\n";
  row += "           </div><!-- /list-view-pf-body -->\n";
  row += "          </div><!-- /list-view-pf-main-info -->\n";
  row += "         </div><!-- /list-group-item-header -->\n";
  row +=
    '         <div class="list-group-item-container container-fluid hidden">\n';
  row += '          <div class="close">\n';
  row += '           <span class="pficon pficon-close"></span>\n';
  row += "          </div><!-- /close -->\n";
  row += '          <div class="clearfix">\n';
  row += '           <div class="col-md-9">\n';
  if (result.backend == "profile") {
    row += printProfileTable(err);
    var itisprofile = 1;
  } else {
    row += '            <dl class="dl-horizontal">\n';
    row += "             <dt>Description</dt>\n";
    row += "             <dd>" + result.description + "</dd>\n";
    if (typeof result.time !== "undefined") {
      row += "             <dt>Plugin Execution Time</dt>\n";
      row +=
        "             <dd>" +
        Math.round(result.time * 1000) / 1000 +
        "</dd>\n";
    }
    row += "             <dt>Backend</dt>\n";
    row += "             <dd>" + result.backend + "</dd>\n";
    row += "             <dt>Priority</dt>\n";
    row += "             <dd>" + result.priority + "</dd>\n";
    row += "             <dt>KBase</dt>\n";
    row +=
      '             <dd><a href="' +
      result.kb +
      '" target="_blank">' +
      result.kb +
      "</a></dd>\n";
    row += "             <dt>Bugzilla</dt>\n";
    if (/([0-9])+$/.test(result.bugzilla)) {
      row +=
        '        <dd><a href="' +
        result.bugzilla +
        '" target="_blank"><span class="badge badge-danger">' +
        /([0-9]+)$/.exec(result.bugzilla)[1] +
        "</span></a></dd>\n";
    } else if (/\_([0-9]{7})$/.test(plugin_names.name)) {
      row +=
        '        <dd><a href="local-web-resources/bugzilla.redhat.com/show_bug.cgi?id=' +
        /\_([0-9]{7})$/.exec(plugin_names.name)[1] +
        '" target="_blank" class="badge badge-danger">' +
        /\_([0-9]{7})$/.exec(plugin_names.name)[1] +
        "</a></dd>\n";
    } else {
      row += "        <dd>N/A</dd>\n";
    }
    row += "             <dt>Output</dt>\n";
    if (/[A-z0-9]+/.test(error_text)) {
      row += "             <dd><pre>" + error_text + "</pre></dd>\n";
    } else {
      row += "             <dd>N/A</dd>\n";
    }
    row += "            </dl>\n";
    row += "           <p>\n";
    row += "           </p><!-- /p -->\n";
  }
  row += "          </div><!-- /col-md-9 -->\n";
  row += '          <div class="col-md-3">\n';
  row +=
    '            <a href="#plugin-' +
    item_id +
    '"><span class="fa fa-link"></span> Link</a>\n';
  if (itisprofile == "1") {
    row +=
      '<div id="pie-chart-8' +
      item_id +
      '" class="pie-chart-pf example-pie-chart-mini"></div>\n';
    pieChartSmallConfig.bindto = "#pie-chart-8" + item_id;
    pieChartSmallConfig.data = getProfileCounts(err);
  }
  row += "          </div><!-- /col-md-3 -->\n";
  row += "         </div><!-- /row -->\n";
  row += "        </div><!-- /list-group-item-container -->\n";
  row += "       </div><!-- /list-group-item -->\n";
  if (itisprofile == "0") {
    $("#list-group").append(row);
  }
  if (itisprofile == "1") {
    $("#profile-group").append(row);
    if (pieChartSmallConfig.data.pietotal != "0") {
      c3.generate(pieChartSmallConfig);
    }
  }
}

/**
 * Toggle mark of "check result" file as "baseline" for comparison.
 * @param {string} checkResultFile - afile name of "check result"
 */
function toggleBaseline(checkResultFile) {

  var div_otherJsons = $("#otherJsons");
  const clusterId = $('#cluster-select option:selected').val();
  const selectedCheckResultFile = $('#jsons').text();

  return $.ajax({
    url: '/baseline',
    type: "POST",
    dataType: "json",
    async: false,
    data: JSON.stringify({
      cluster_id: clusterId,
      selected_result: checkResultFile,
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
      if (checkResultFile == jsonFile) {
        div_otherJsons
          .children("button")
          .html(jsonFile + ' <span class="caret"></span><span>(Baseline)</span>');
      }
      div_otherJsons
        .children("ul")
        .append('<li><a href="#" class="json-files">' + f + "</a></li>");
      div_otherJsons.removeClass("hidden");
    },
    error: function (xhr, status, err) {
        console.error("AJAX error:", err);
        warnMessage('danger','No file selected.', err);
    },
  });
}

const messageIconClasses = new Map([
  ["danger", "pficon pficon-error-circle-o"],
  ["warning", "pficon pficon-warning-triangle-o"],
  ["success", "pficon pficon-ok"],
  ["info", "pficon pficon-info"]
]);

/**
 * Modernized Alert Function
 * @param {string} severity - danger, warning, success, info
 * @param {string} message - The text to display
 */
function warnMessage(severity, message) {
  // Map 'level' to PatternFly/Bootstrap classes
  const alertClass = `alert-${severity}`;
  //const iconClass = severity === 'danger' ? 'pficon-error-circle-o' : 'pficon-info';
  const iconClass = messageIconClasses.get(severity) || messageIconClasses.get("info");

  const $alert = $(`
    <div class="alert ${alertClass} alert-dismissable">
      <button type="button" class="close" data-dismiss="alert" aria-hidden="true">
        <span class="pficon pficon-close"></span>
      </button>
      <span class="${iconClass}"></span>
      <strong>${severity.charAt(0).toUpperCase() + severity.slice(1)}</strong>
      ${message}
    </div>
  `);

  $alert.fadeOut(10000, function() {
    $(this).remove();

  });

  // Manual Close Event: This ensures it works even if Bootstrap JS is missing
  $alert.find('.close').on('click', function() {
    $alert.fadeOut(300, function() {
      $(this).remove();
    });
  });


  // Use prepend to show at the top, or append if that's your design
  $("#alert_list").prepend($alert);
}


// Count the number of objects
function ObjectLength(object) {
  var length = 0;
  for (var key in object) {
    if (object.hasOwnProperty(key)) {
      ++length;
    }
  }
  return length;
}

function checkForFile(data) {
  var div_otherJsons = $("#otherJsons");
  debugger;
  var f = data['filename']? data['filename'] : data; // jsonFilesList
  var isBaseline = (data['is_baseline'] && data['is_baseline'] == true)? true : false;

  return $.ajax({
    url: f,
    type: "HEAD",
    dataType: "json",
    async: false,
    success: function (data) {
      if (f == jsonFile) {
        if (isBaseline) {
          div_otherJsons
            .children("button")
            .html(jsonFile + ' <span class="caret"></span>');
        }
        else {
          div_otherJsons
            .children("button")
            .html(jsonFile + ' <span class="caret"></span><span style="color: #f0ab00;"><b>&#9733; baseline</b></span>');
        }
      }
      if (isBaseline) {
        div_otherJsons
          .children("ul")
          .append('<li><div class="row"><a href="#" class="json-files">' + f + '</a><span style="color: #f0ab00;"><b>&#9733; baseline</b></span></div></li>');
      }
      else {
        div_otherJsons
          .children("ul")
          .append('<li><div class="row"><a href="#" class="json-files">' + f + '</a></div></li>');
      }
      div_otherJsons.removeClass("hidden");
    },
  });
}

function checkForFileNew(data) {
  var $div_otherJsons = $("#otherJsons");
  debugger;
//  let $compareFromSelect = $('#check-results-from-select');
//  let $compareToSelect = $('#check-results-to-select');

  // Empty the native select dropdowns
//  $compareFromSelect.empty();
//  $compareToSelect.empty();
  $div_otherJsons.empty();
  //if(!jsonFile || jsonFile==''){ // onfile selected - add empty slot on combo
    $div_otherJsons.append($('<option></option>').val("").text("...").clone());
  //}
  // Iterate over the returned JSON objects
  $.each(data, function(index, artifact) {
    // Strip '.json' from the display name to match your Image 3 UI
    let displayName = artifact.filename.replace('.json', '');

    // The value must remain the full filename so the backend can locate it later
    let optionHTML = (jsonFile && jsonFile==artifact.filename)? $('<option selected></option>').val(artifact.filename) : $('<option></option>').val(artifact.filename);

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

//    $compareFromSelect.append(optionHTML.clone());
//    $compareToSelect.append(optionHTML.clone());
      $div_otherJsons.append(optionHTML.clone());
  });

  // Command bootstrap-select to rebuild the visual UI
//  $compareFromSelect.selectpicker('refresh');
//  $compareToSelect.selectpicker('refresh');
  $div_otherJsons.selectpicker('refresh');
}


function scrollToPlugin() {
  if (window.location.hash.substr(1)) {
    var plugin = $("#" + window.location.hash.substr(1));
    $("html, body").animate(
      {
        scrollTop: plugin.offset().top - plugin.height(),
      },
      1000
    );
    plugin
      .show()
      .find(".fa-angle-right:first")
      .toggleClass("fa-angle-down")
      .end()
      .toggleClass("list-view-pf-expand-active")
      .find(".list-group-item-container")
      .removeClass("hidden")
      .end()
      .css("border", "2px solid red");
  }
}

// NEW - BUILD PAGE
function buildPage(data) {
  var div_otherJsons = $("#otherJsons");
  // delete row with "loading" message
  $("tbody#report_table_risu_body tr#loading").remove();

  // delete old content: metadata profile report
  $('tbody#metadata_table_risu_body tr').empty();
  $('tbody#profile_table_risu_body tr#profile-group').empty();
  $('tbody#report_table_risu_body tr#list-group').empty();

  // We need to generate some kind of plugin id with the filename
  $.each(data.metadata, function (i, item) {
    var row = "<tr><th>" + i + "</th><td>" + item + "</td></tr>\n";
    $("#metadata_table_risu > tbody:last-child").append(row);
    // Set title according to metadata
    if (i == "title") {
      //document.getElementById("reporttitle").innerText = item;
      //window.document.title = item;
    } else if (i == "path" && i.indexOf("/") >= 0) {
      document.title = "Report for " + item.split("/").pop();
    }
  });
  div_otherJsons
    .children("button")
    .html(jsonFile + ' <span class="caret"></span>');
  div_otherJsons.children("button").data("jsonFile", jsonFile);
  var dataNum = ObjectLength(data.results);
  var counter = 0;
  $.each(data.results, function (i, item) {
    // This counter will let us know when we are done looping
    // We need this because JS is async
    counter++;

    if (counter == dataNum) {
      // Here we are done with looping all the results, we are going to update the filters above
      var unique = plugin_cats_array.filter(onlyUnique).sort();
      // We generate the category filters here
      var div_cat_list =
        '<div class="row"><label id="label_check_all" class="btn btn-dark active" style="width: 100%"><input type="checkbox" id="check_all" checked autocomplete="off">All</label></div><div class="row">\n';
      $.each(unique, function (c, cname) {
        div_cat_list +=
          ' <div class="col-sm-4"><label><input type="checkbox" name="' +
          cname +
          '" id="cb_cat_' +
          cname +
          '" class="check-category" data-category="' +
          cname +
          '" checked autocomplete="off">' +
          cname +
          "</label></div>\n";
      });
      div_cat_list += "</div>";
      $("#category-list").html(div_cat_list);
      $("#numresults").html(counter);
    }
    // Here we have a risu.json
    if (data.metadata.source == "risu") {
      if (item.backend == "profile") {
        var plugins = new Array();
        $.each(JSON.parse(item.result.err), function (i, o) {
          plugins.push({
            server: "localhost",
            hostname: "localhost",
            msg: o.err,
            rc: o.rc,
            plugin_name: o.plugin,
            plugin_id: o.plugin_id,
          });
        });
        // console.debug(plugins);
        item.result.err = plugins;
      }
      printRisuPlugin(
        item,
        item.result.out,
        item.result.err,
        item.result.rc,
        data
      );
      // Here we have a magui.json
    } else if (data.metadata.source == "magui") {
      if (
        item.plugin == "risu-outputs" ||
        item.plugin == "metadata-outputs"
      ) {
        $.each(item.result, function (s, result) {
          if (s == "err") {
            $.each(result, function (plugin, pdata) {
              // Defining defaults for globals
              var gout = "";
              var gerr = "";
              var grc = 30;
              var plugins = new Array();
              $.each(pdata.sosreport, function (server, obj) {
                // If we have a failed, the global will definitely be failed
                if (obj.rc == 20) {
                  grc = 20;
                }
                if (obj.rc == 40 && grc != 20) {
                  grc = 40;
                }
                if (obj.rc == 10 && grc != 20 && grc != 40) {
                  grc = 10;
                }
                if (
                  obj.rc == 30 &&
                  grc != 20 &&
                  grc != 40 &&
                  grc != 10
                ) {
                  rc = 30;
                }

                var plugin_state = getPluginState(
                  obj.rc,
                  obj.priority
                );
                gout +=
                  plugin_state.badge +
                  " " +
                  server +
                  ": " +
                  obj.out +
                  "<br>";
                gerr +=
                  plugin_state.badge +
                  " " +
                  server +
                  ": " +
                  obj.err +
                  "<br>";
                if (pdata.backend == "profile") {
                  subobject = JSON.parse(obj.err);
                  $.each(subobject, function (i, o) {
                    plugins.push({
                      hostname: server,
                      msg: o.err,
                      rc: o.rc,
                      plugin_name: o.plugin,
                      plugin_id: o.plugin_id,
                    });
                  });
                }
              });
              if (pdata.backend == "profile") gerr = plugins;
              printRisuPlugin(
                pdata,
                gout,
                gerr,
                grc,
                data,
                item.plugin
              );
            }); // each result
          } // s == "err"
        }); // each item.result
      } else {
        printRisuPlugin(
          item,
          item.result.out,
          item.result.err,
          item.result.rc,
          data,
          false,
          "magui"
        );
      } // if risu-outputs
    } // if data source == "magui"
  }); // each data.result
  $("#numtests").html(counter);
  sortPlugins("priority");
  filterCards();
  scrollToPlugin();
}


//  var jsonUrl =`${[location.protocol, "//", location.host, location.pathname].join("")}data/selected`;
//
//  $.ajax({
//    url: jsonUrl,
//    type: "GET",
//    dataType: "json",
//    async: false,
//    beforeSend: function() {
//      debugger; // get jsonFile
//      return ($('#home-results-tab.active').length > 0)? true : false;
//    },
//    success: function(data) {
//        jsonFile = data;
//        console.debug("selected json file ", jsonFile);
//    },
//    error: function(xhr) {
//        console.error("Error fetching data");
//    },
//  });


// This code is only executed when everything else is loaded
$(document).ready(function () {

  var jsonUrl =`${[location.protocol, "//", location.host, location.pathname].join("")}data/selected`;

  $.ajax({
    url: jsonUrl,
    type: "GET",
    dataType: "json",
    async: false,
    beforeSend: function() {
      debugger; // get jsonFile
      return ($('#home-results-tab.active').length > 0)? true : false;
    },
    success: function(data) {
        jsonFile = data;
        console.debug("selected json file ", jsonFile);
    },
    error: function(xhr) {
        console.error("Error fetching data");
    },
  });

  // Initialize the selectpicker
  $('.selectpicker').selectpicker();

  $().setupVerticalNavigation(true);
  var div_otherJsons = $("#otherJsons");
  div_otherJsons.selectpicker('refresh');

  if (jsonFile == null || jsonFile == '') {
    jsonDiffFile =  getParameterByName("json");
    jsonFile = jsonDiffFile; // "osc.json"; //  "risu.json";
  }
  for (i = 0; i < jsonFilesList.length; ++i) {
//    if(jsonFilesList[i]['filename']) {
//      checkForFile(jsonFilesList[i]['filename']);
//    }
//    else {
//      checkForFile(jsonFilesList[i]);
//    }
   //*** checkForFile(jsonFilesList[i]);
  }

  debugger;
  checkForFileNew(jsonFilesList);


  // Chrome is too secure
  var url_file_regex = new RegExp("^file:\/\/");
  if (
    window.chrome &&
    window.chrome.webstore &&
    url_file_regex.test(window.location.href)
  ) {
    warnMessage(
      "warning",
      "Some browsers (ie: Chrome) are not accepting file:// URLs. Firefox supports it, or you can start Chrome with --allow-file-access-from-files"
    );
  }

  $(window).bind("hashchange", function (e) {
    scrollToPlugin();
  });

  // for some unknown reason, this is broken
/*
    $("#expandAll").click(function (e) {
        $("#list-group > div").each(function (i, j) {
            // skip toggle for items with class names: "badge-changed" "badge-new" "badge-removed"
            var c = $(j).find("div.list-group-item-container");
            var h = $(j).find("div.list-group-item-header");
            if($(j).hasClass("list-view-pf-expand-active") &&
            !$(c).hasClass("hidden") &&
            $(h).is(".badge-changed, .badge-new, .badge-removed")){
                console.log("Skip expand action for '%s'", $(c).attr('id'));
            }
            else {
                $(j)
                    .toggleClass("list-view-pf-expand-active")
                    .find(".list-group-item-container")
                    .toggleClass("hidden");
            }
        });
    });
*/

  // listener when the user picks a status filter
  $("body").on("change", ".nx-filter-status", function (e) {
    filterCards();
  });

  // listener when the user writes in the searchbox
  $("#filter_text").keyup(function (e) {
    filterCards();
  });

  // In this section, we have to attach events on the body
  // because we are using dynamic elements

  // listener when the user clicks on category check boxes
  $("body").on("change", ".check-category", function () {
    filterCards();
  });

  // listener when the user checks or uncheck the "All categories"
  $("body").on("change", "#check_all", function () {
    var cb = $(this);
    checkAllCat(cb.prop("checked"));
  });

  // listener when someone is clicking on a badge in an expanded card
  $("body").on("click", ".category-badge", function () {
    var cat = $(this).data("category");
    checkAllCat(false);
    $("#cb_cat_" + cat)
      .prop("checked", true)
      .change();
  });

// *** moved to diff.html ***
//        $("body").on("click", "#metadata_table_risu_header", function (e) {
//          $("#metadata_table_risu_body").toggle();
//        });
//        $("body").on("click", "#profile_table_risu_header", function (e) {
//          $("#profile_table_risu_body").toggle();
//        });
//        $("body").on("click", "#report_table_risu_header", function (e) {
//          $("#report_table_risu_body").toggle();
//        });

  // click the list-view heading then expand a row
  $("body").on("click", ".list-group-item-header", function (event) {
    if (!$(event.target).is("button, a, input, .fa-ellipsis-v")) {
      $(this)
        .find(".fa-angle-right")
        .toggleClass("fa-angle-down")
        .end()
        .parent()
        .toggleClass("list-view-pf-expand-active")
        .find(".list-group-item-container")
        .toggleClass("hidden");
    }
  });

  // click the close button, hide the expand row and remove the active status
  $("body").on("click", ".list-group-item-container .close", function () {
    $(this)
      .parent()
      .addClass("hidden")
      .parent()
      .removeClass("list-view-pf-expand-active")
      .find(".fa-angle-right")
      .removeClass("fa-angle-down");
  });

  $("body").on("click", "#sortDirection", function (e) {
    var sortdir = $("#sortDirection");
    sortdir.removeClass();
    if (sortdir.data("direction") == "desc") {
      sortdir.addClass("fa fa-sort-amount-asc");
      sortdir.data("direction", "asc");
    } else {
      sortdir.addClass("fa fa-sort-amount-desc");
      sortdir.data("direction", "desc");
    }
    sortPlugins($("#plugin-sort").data("sortfield"));
  });

  $("body").on("click", ".plugin-sort-field", function (e) {
    var sortfield = $(this);
    var sortkey = sortfield.html();
    var sortkeyl = sortkey.toLowerCase();
    var sortbutton = $(this).parent().parent().parent().find("button");
    sortfield.parent().parent().find("li").removeClass("selected");
    sortfield.parent().addClass("selected");
    sortbutton.html(sortkey + ' <span class="caret"></span>');
    sortbutton.data("sortfield", sortkeyl);
    sortPlugins(sortkeyl);
  });

  $("body").on("click", ".json-files", function (e) {
    window.location.href =
      [location.protocol, "//", location.host, location.pathname].join(
        ""
      ) +
      "?json=" +
      $(this).html();
  });

  $("body").on("click", "#toggle-baseline-btn", function (e) {
    debugger;
    console.log("toggle-baseline-btn");
    toggleBaseline(jsonFile);
  });

  $('#otherJsons.selectpicker').on('change', function() {
    var selectedValue = $(this).val();
    console.log('Selected Value:', selectedValue);
    var reqUrl = `${[location.protocol, "//", location.host, location.pathname].join("")}${selectedValue}`;
    // Here we load the data from risu.json with ajax and we populate the webpage
    $.ajax({
      url: reqUrl,
      dataType: "json",
      async: true,
//      data: {
//        "json": selectedValue,
//      },
      beforeSend: function () {
        if (!selectedValue || selectedValue == '') return false; //cancel request
        $("#report_table_risu_body").append(
          '<tr id="loading"><td>Loading ' +
            selectedValue +
            '... <span class="fa fa-refresh"/></td></tr>'
        );
      },
      success: function(data) {
        // clean previous data
//        $('#metadata_table_risu_body').empty();
//        $('#profile_table_risu_body').empty();
//        $('#report_table_risu_body').empty();
        jsonFile = selectedValue;
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
  });

  // Here we load the data from risu.json with ajax and we populate the webpage
  //if (!jsonFile || jsonFile == '') jsonFile='osc.json'; // cancel request
  $.ajax({
    url: `${jsonFile}`,  /*`?json=${jsonFile}`,*/
    dataType: "json",
    async: true,
    beforeSend: function () {
      if (!jsonFile || jsonFile == '' || jsonFile == 'osc.json') {
        buildPage({}); renderDiffTable({});
        return false;
      } // cancel request
      $("#report_table_risu_body").append(
        '<tr id="loading"><td>Loading ' +
          jsonFile +
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
        warnMessage("danger", `Requested JSON file '${jsonFile}' was not found.`);
//        // FIXME infinite loop
//        for (i = 0; i < jsonFilesList.length; ++i) {
//          if (jsonFilesList[i] != jsonFile) {
//            window.location.href =
//              [
//                location.protocol,
//                "//",
//                location.host,
//                location.pathname,
//              ].join("") +
//              "?json=" +
//              jsonFilesList[i];
//          }
//        }
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
    }, // ajax error
    complete: function () {
      var $loadingRow = $("#report_table_risu_body tr#loading");
      $loadingRow.remove(); // Clean up UI regardless of success/error
    }, // ajax complete
  }); // ajax query
}); // doc ready
