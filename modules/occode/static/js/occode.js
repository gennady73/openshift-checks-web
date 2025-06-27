/* occode scripts */
'use strict';

var occode = window.occode || {};

require.config({
    baseUrl: occode.config.get('pluginsBaseUrl'),
    paths: {'vs': 'monaco-editor/min/vs'}
});

occode.editorWidget = {
    editor: null,
    resourceName: null,
    editorState: null,
};
occode.editorElement = null;

occode.languages = [];
// OCC
//occode.defaultExt = 'txt';
//occode.defaultLangId = 'plaintext';
//occode.defaultLang = null;
//occode.fallbackLang = null;

occode.defaultExt = 'sh';
occode.defaultLangId = 'shell';
occode.defaultLang = 'shell';
occode.fallbackLang = 'bash';

occode.$editorContainer = null;
occode.$editorBody = null;
occode.$editorLoader = null;
occode.$pagePreloader = null;

occode.editorStates = {
    INIT: 'init',
    LOADED: 'loaded',
    MODIFIED: 'modified',
    BUSY: 'busy',
};

occode.defaultEditorTheme = 'vs-dark';
occode.availableEditorThemes = ['vs', 'vs-dark', 'hc-black'];

occode.APP_BUSY = false;

occode.allowedLangIds = [];

occode.onStateChange = $.noop;

occode.storage.set('occodeterminalEnabled', Number(0)); // OCC
occode.defaultEditorValue = // OCC
    [
        '#!/usr/bin/env bash',
        '# description: Show the pods running in the cluster',
        '',
        '[ -z ${UTILSFILE} ] && source $(echo "$(dirname ${0})/../utils")',
        '',
        'if oc auth can-i get pods -A >/dev/null 2>&1; then',
        '  msg "Total pods: $(oc get pods -A --no-headers | wc -l)"',
        '  exit ${OCINFO}',
        'else',
        '  msg "Couldn\'t get pods, check permissions"',
        '  exit ${OCSKIP}',
        'fi',
        '',
        'exit ${OCUNKNOWN}'
    ].join('\n');

$(function () {
    occode.$pagePreloader = $('div#page-preloader');
    occode.$editorContainer = $('div#editor-container');
    occode.$editorBody = occode.$editorContainer.find('.editor-body');
    occode.$editorLoader = occode.$editorContainer.find('.editor-preloader');
    occode.editorElement = occode.$editorBody.get(0);

    $('ul#dir-tree').treed();
    occode.setEditorState(occode.editorStates.INIT);
    // OCC
    require(['vs/editor/editor.main', 'vs/basic-languages/shell/shell'], function(monaco, shell) {
        occode.languages = monaco.languages.getLanguages();
        occode.allowedLangIds = occode.languages.map(function (lang) { return lang.id; });
        occode.defaultLang = occode.getLanguageByExtension(occode.defaultExt);
        occode.fallbackLang = occode.getLanguageById(occode.defaultLangId);

        $('ul#dir-tree').on('click', '.file-item', function () {
            return occode.openResource($(this));
        });

        $('.header-actions').on('click', function () {
            if (occode.editorWidget.editor) {
                occode.editorWidget.editor.trigger('mouse', $(this).data('actionId'));
            }
        });

        $('#toggle-minimap').on('click', function () {
            occode.minimapEnabled(!occode.minimapEnabled());
        });

        // OCC
        $('#toggle-terminal').on('click', function () {
            var termEnabled = occode.terminalEnabled(!occode.terminalEnabled());
            console.log('terminal enabled=',termEnabled);
            if(termEnabled) {
                $('div#page-row-2').attr('style','position: sticky; bottom:0')
                $("#test_script").val($("#resource-name").attr("title"));
            }
            else {
                  $('div#page-row-2').attr('style','z-index:-1000;')
                  $("#test_script").val("");
            }
        });

        // OCC

        $('#new-project-trigger').on('change', function () {
         console.log( this.value );
         window.location = `/editor?dtree=${this.value}`
        });

        $.contextMenu({
            selector: 'ul#dir-tree .resource-items',
            autoHide: false,
            build: function ($trigger, e) {
                var items = {
                    'title': {name: $trigger.data('pathName'), icon: 'fa-tag', disabled: true},
                    'sep': '---------'
                };
                if ($trigger.hasClass('dir-item')) {
                    items['title']['icon'] = 'fa-folder';
                    if ($trigger.hasClass('expanded')) {
                        items['toggle_collapse'] = {name: 'Collapse', icon: 'fa-compress'};
                    } else {
                        items['toggle_collapse'] = {name: 'Expand', icon: 'fa-expand'};
                    }
                    items['create_new_file'] = {name: 'Create New File', icon: 'fa-file-code-o'};
                } else {
                    items['title']['icon'] = 'fa-file';
                    items['open'] = {name: 'Open', icon: 'fa-external-link', disabled: $trigger.hasClass('selected')};
                }
                return {
                    items: items,
                    callback: function (key, options) {
                        switch (key) {
                            case 'toggle_collapse':
                                options.$trigger.click();
                                break;

                            case 'open':
                                occode.openResource(options.$trigger);
                                break;

                            case 'create_new_file':
                                occode.openNewFileModal(options.$trigger);
                                break;
                        }
                    },
                };
            },
            events: {
                show: function (options) {},
                hide: function (options) {},
            },
        });

        $('#fileNameModal').on('shown.bs.modal', function () {
            $(this).find('#new_filename').focus();
        });

        $('form#fileNameForm').on('submit', function (evt) {
            evt.preventDefault();
            var $form = $(this);
            var $button = $form.find('[type="submit"]');
            var base_url = $form.find('#base_url').val();
            var base_path_name = $form.find('#base_path_name').val();
            var new_filename = $form.find('#new_filename').val();
            if (!(new_filename && occode.validResource(new_filename))) {
                $form.find('.form-msg').empty().append($('<span class="text-danger">Please enter valid file name.</span>').autoremove(10));
            } else {
                var resource_url = base_url + '/' + new_filename; // OCC base_url + '/' + new_filename + '.txt';
                $.ajax({
                    type: 'HEAD',
                    url: resource_url,
                    dataType: 'text',
                    cache: false,
                    beforeSend: function (xhr, settings) {
                        $button.button('loading');
                    },
                    complete: function (xhr, status) {
                        $button.button('reset');
                    },
                }).done(function (data, status, xhr) {
                    $form.find('.form-msg').empty().append($('<span class="text-danger">This file already exists.</span>').autoremove(10));
                }).fail(function (xhr, status, err) {
                    if (xhr.status == 404) {
                        occode.loadEditor({url: resource_url, filePath: base_path_name + '/' + new_filename}, false, true);
                        $('#fileNameModal').modal('hide');
                    } else {
                        $form.find('.form-msg').empty().append($('<span class="text-danger">Internal Error: '+err+'</span>').autoremove(10));
                    }
                });
            }
            return false;
        });

        $('#editor-header #resource-close').on('click', function () {
            if (occode.editorWidget.editorState == occode.editorStates.MODIFIED && !confirm('Close without saving?')) {
                return false;
            }
            occode.saveResourceState();
            occode.clearEditor();
            occode.resetSelectedResource();
            $('#editor-header #resource-mod').hide();
            $('#editor-header #resource-name').text('').attr('title', '');
            $(this).hide();
        });

        $(window).on('resize', function () {
            if (occode.editorWidget.editor) {
                occode.editorWidget.editor.layout();
            }
        });

        $(window).on('beforeunload', function (evt) {
            if (occode.APP_BUSY || occode.editorWidget.editorState == occode.editorStates.BUSY) {
                evt.preventDefault();
                evt.returnValue = 'Editor is working...';
                return evt.returnValue;
            }
        });

        occode.$pagePreloader.fadeOut();

        // OCC Code completion
        //debugger;
        const shellLanguage = shell.language;
        function createCompletionItems(range) {
              const keywordSuggestions = shellLanguage.keywords.map(keyword => ({
                label: keyword,
                kind: monaco.languages.CompletionItemKind.Keyword,
                insertText: keyword,
                documentation: `Shell keyword: ${keyword}`,
                range: range,
              }));

              const builtinSuggestions = shellLanguage.builtins.map(builtin => ({
                label: builtin,
                kind: monaco.languages.CompletionItemKind.Function,
                insertText: builtin,
                documentation: `Built-in shell command: ${builtin}`,
                range: range,
              }));

              return [...keywordSuggestions, ...builtinSuggestions];
            }

//            monaco.languages.registerTokensProviderFactory('shell', async () => {
//              // Use the Monarch tokenizer
//              return monaco.languages.setMonarchTokensProvider('shell', shellLanguage);
//            });
            monaco.languages.setMonarchTokensProvider('shell', shellLanguage);

            monaco.languages.registerCompletionItemProvider('shell', {
              provideCompletionItems: function (model, position) {
                // find out if we are completing a property in the 'dependencies' object.
                var textUntilPosition = model.getValueInRange({
                    startLineNumber: 2,
                    startColumn: 1,
                    endLineNumber: position.lineNumber,
                    endColumn: position.column,
                });

                var wordInfo = model.getWordUntilPosition(position);

                var range = {
                    startLineNumber: position.lineNumber,
                    endLineNumber: position.lineNumber,
                    startColumn: wordInfo.startColumn,
                    endColumn: wordInfo.endColumn,
                };

                // Generate suggestions using the imported shell definitions
                const suggestions = createCompletionItems(range);

                // Optionally, add context-sensitive suggestions based on the current model content
                const lineContent = model.getLineContent(position.lineNumber);
                if (lineContent.trimStart().startsWith('cd')) {
                  suggestions.push({
                    label: 'cd ..',
                    kind: monaco.languages.CompletionItemKind.Snippet,
                    insertText: 'cd ..',
                    documentation: 'Navigate to the parent directory',
                    range: range
                  });
                }
                if (lineContent.trimStart().startsWith('for')) {
                    suggestions.push({
                      label: 'for-loop',
                      kind: monaco.languages.CompletionItemKind.Snippet,
                      insertText: 'for ${1:var} in ${2:items}; do\n\t${3:command}\ndone',
                      insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                      documentation: 'Template for a for loop in a shell script',
                      range: range
                    });
                }
                // OCC suggestions
                /* OCC Constants
                OCOK=0
                OCINFO=1
                OCERROR=2
                OCSKIP=3
                OCUNKNOWN=4
                */
                if (lineContent.match(/\${\s*(OC)?\w*\}?\s*$/)) {
                    const constants = [
                          { label: 'OCOK', detail: '0 - (OCC) Operation completed successfully', insertTextRules: 'monaco.languages.CompletionItemInsertTextRule.KeepWhitespace' },
                          { label: 'OCINFO', detail: '1 - (OCC) Informational message', insertTextRules: 'monaco.languages.CompletionItemInsertTextRule.KeepWhitespace' },
                          { label: 'OCERROR', detail: '2 - (OCC) Error occurred', insertTextRules: 'monaco.languages.CompletionItemInsertTextRule.KeepWhitespace' },
                          { label: 'OCSKIP', detail: '3 - (OCC) Operation skipped', insertTextRules: 'monaco.languages.CompletionItemInsertTextRule.KeepWhitespace' },
                          { label: 'OCUNKNOWN', detail: '4 - (OCC) Unknown status', insertTextRules: 'monaco.languages.CompletionItemInsertTextRule.KeepWhitespace' },
                        ];

                    //const wordInfo = model.getWordUntilPosition(position);
                    //const word = wordInfo.word;

                    const MyConstantSuggestions = constants
                      .filter((c) => c.label.startsWith(wordInfo.word))
                      .map((c) => ({
                        label: c.label,
                        kind: monaco.languages.CompletionItemKind.Constant,
                        insertText: c.label,
                        insertTextRules: c.insertTextRules,
                        documentation: `Constant: ${c.detail}`,
                        range: range
                      }));

                    // Merge the two suggestions
                    let mergedSuggestions = [];
                    if (MyConstantSuggestions.length > 0) {
                        //for suggestion in mergedSuggestions // = [...suggestions, ...MyConstantSuggestions];
                       return { suggestions: [...suggestions, ...MyConstantSuggestions] };
                    }
//                    else {
//                      mergedSuggestions = suggestions;
//                    }
                }
                return { suggestions }; // return { mergedSuggestions };
              },
            });

        // OCC END
    });
});

occode.editorTheme = function () {
    var theme = occode.config.get('editorTheme', occode.defaultEditorTheme);
    return occode.availableEditorThemes.indexOf(theme) > -1 ? theme : occode.defaultEditorTheme;
};

occode.setEditorState = function (state) {
    var prevState = occode.editorWidget.editorState;
    occode.editorWidget.editorState = state;
    if (occode.editorWidget.editorState != prevState) {
        occode.onStateChange(occode.editorWidget.editorState);
    }
};

occode.getExt = function (filename) {
    var m = filename.match(/\.(\w*)$/i);
    // OCC
    //return (m && m.length > 1) ? m[1].toLowerCase() : null;
    // OCC
    var ext = (m && m.length > 1) ? m[1].toLowerCase() : null;
    if (ext === undefined || ext === null || ext === '') {
        console.log(`This file '${filename}' does not have an extension set defaut type: shell`);
        ext = 'sh';
    }
    return ext;
};

occode.getResourceExt = function (resource_url) {
    var m = resource_url.match(/\.(\w*)\.txt$/i);
    return (m && m.length > 1) ? m[1].toLowerCase() : null;
};

occode.getLanguageById = function (langId) {
    return occode.languages.find(function (lang) {
        return lang.id == langId;
    });
};

occode.getLanguageByExtension = function (extension) {
    return occode.languages.find(function (lang) {
        return lang.extensions.indexOf('.'+extension) > -1;
    });
};

occode.getLanguageByMimetype = function (mimetype) {
    return occode.languages.find(function (lang) {
        return lang.mimetypes.indexOf(mimetype) > -1;
    });
};

occode.minimapEnabled = function (minimapFlag) {
    if (typeof minimapFlag === 'undefined') {
        var flag = occode.storage.get('occodeMinimapEnabled');
        return flag === null ? true : !!parseInt(flag);
    } else {
        if (occode.editorWidget.editor) {
            occode.editorWidget.editor.updateOptions({minimap: {enabled: !!minimapFlag}});
            occode.storage.set('occodeMinimapEnabled', Number(!!minimapFlag));
        }
    }
};

// OCC
occode.terminalEnabled = function (terminalFlag) {
    if (typeof terminalFlag === 'undefined') {
        var flag = occode.storage.get('occodeterminalEnabled');
        return flag === null ? true : !!parseInt(flag);
    } else {
        if (occode.editorWidget.editor) {
            occode.editorWidget.editor.updateOptions({terminal: {enabled: !!terminalFlag}});
            occode.storage.set('occodeterminalEnabled', Number(!!terminalFlag));
            return !!terminalFlag;
        }
    }
};

occode.notifyEditor = function (message, category) {
    var msgType = category == 'error' ? 'danger' : 'success';
    var $msg = $('<div class="alert alert-dismissible alert-'+msgType+'" role="alert">'+
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><i class="fa fa-times" aria-hidden="true"></i></button>'+
        '<strong>'+message+'</strong>'+
    '</div>');
    $msg.autoremove(msgType == 'success' ? 5 : 10);
    occode.$editorContainer.find('.editor-notification').empty().append($msg);
};

occode.editorBodyMsg = function (content) {
    return $('<div class="editor-body-msg">'+content+'</div>');
};

occode.resetSelectedResource = function () {
    $('ul#dir-tree .file-item').removeClass('selected');
};

occode.highlightSelectedResource = function (filePath, parentPath) {
    occode.resetSelectedResource();
    var $selectedElement = $('ul#dir-tree .file-item[data-path-name="'+filePath+'"]');
    if ($selectedElement.length) {
        $selectedElement.addClass('selected');
    } else if (parentPath) {
        var $parentItem = $('.dir-item[data-path-name="'+parentPath+'"]');
        if ($parentItem.length) {
            var $parentElement = $parentItem.find('ul:first');
            var $treeItem = $parentElement.find('li.file-item:first');
            if ($treeItem.length) {
                var fileName = filePath.replace(parentPath+'/', '');
                var resource_url = occode.config.get('resourceUrlTemplate').replace('__pathname__', filePath);
                $parentElement.prepend(
                    $treeItem.clone().removeClass('dir-item').addClass('file-item selected').text(fileName).attr({
                        'title': fileName,
                        'data-path-name': filePath,
                        'data-url': resource_url,
                    }).data({
                        pathName: filePath,
                        url: resource_url,
                    })
                );
                if ($parentItem.hasClass('collapsed')) {
                    $parentItem.click();
                }
            }
        }
    }
    $('#editor-header #resource-name').text(occode.strTruncateLeft(filePath, 40)).attr('title', filePath);
};

occode.notifyCursorPosition = function (position) {
    if (position) {
        $('span#line_num').text(position.lineNumber);
        $('span#column_num').text(position.column);
    } else {
        $('span#line_num').text('');
        $('span#column_num').text('');
    }
};

occode.notifyLanguage = function (lang) {
    if (lang && lang.aliases.length) {
        $('span#editor_lang').text(lang.aliases[0]);
    } else {
        $('span#editor_lang').text('');
    }
};

occode.onEditorStateChange = function (state) {
    if (state == occode.editorStates.LOADED) {
        $('#resource-close').show();
    }
    if (state == occode.editorStates.MODIFIED) {
        $('#resource-mod').show();
    } else if (state != occode.editorStates.BUSY) {
        $('#resource-mod').hide();
    }
};

occode.onEditorSave = function (editor) {
    if (occode.editorWidget.editorState != occode.editorStates.MODIFIED/* && !editor.hasWidgetFocus()*/) {
        return null;
    }

    var filePath = occode.$editorContainer.data('filePath');
    var isNewResource = occode.$editorContainer.data('isNewResource');

    if (!window.FormData) {
        occode.notifyEditor('This browser does not support editor save', 'error');
    } else if (!filePath) {
        occode.notifyEditor('Editor is not initialized properly. Reload page and try again.', 'error');
    } else {
        var prevState = occode.editorWidget.editorState;
        var data = new FormData();
        data.set('resource_data', editor.getValue());
        data.set('is_new_resource', Number(isNewResource));

        $.ajax({
            type: 'POST',
            url: occode.config.get('updateResourceBaseUrl') + filePath,
            data: data,
            cache: false,
            processData: false,
            contentType: false,
            beforeSend: function (xhr, settings) {
                occode.setEditorState(occode.editorStates.BUSY);
                occode.$editorLoader.addClass('transparent').show();
            },
            success: function (data, status, xhr) {
                if (status == 'success' && data.success) {
                    occode.setEditorState(occode.editorStates.LOADED);
                    occode.notifyEditor(data.message || 'Saved!');
                    if (occode.$editorContainer.data('isNewResource')) {
                        occode.highlightSelectedResource(filePath, occode.dirname(filePath).replace(/^\/+|\/+$/gm,''));
                        occode.$editorContainer.data('isNewResource', false);
                    }
                } else {
                    occode.setEditorState(prevState);
                    occode.notifyEditor(data.message || 'Error!', 'error');
                }
            },
            error: function (xhr, status, err) {
                occode.setEditorState(prevState);
                occode.notifyEditor('Error: ' + err, 'error');
            },
            complete: function (xhr, status) {
                occode.$editorLoader.hide().removeClass('transparent');
            },
        });
    }
    return null;
};

occode.setEditorEvents = function (editor) {
    // save action
    editor.addAction({
        id: 'save',
        label: 'Save',
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_S],
        precondition: '!editorReadonly',
        keybindingContext: '!editorReadonly',
        contextMenuGroupId: '1_modification',
        contextMenuOrder: 1.5,
        run: occode.onEditorSave,
    });

    // reload action
    editor.addAction({
        id: 'reload',
        label: 'Reload',
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_R],
        precondition: null,
        keybindingContext: null,
        contextMenuGroupId: 'navigation',
        contextMenuOrder: 1,
        run: function (ed) {
            if (occode.editorWidget.editorState == occode.editorStates.INIT || occode.editorWidget.editorState == occode.editorStates.LOADED) {
                occode.loadEditor({url: occode.$editorContainer.data('url'), filePath: occode.$editorContainer.data('filePath')}, true);
            } else if (occode.editorWidget.editorState == occode.editorStates.MODIFIED) {
                alert('Current changes not saved.');
                ed.focus();
            }
        },
    });

    // force reload action
    editor.addAction({
        id: 'force-reload',
        label: 'Force Reload',
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KEY_R],
        precondition: null,
        keybindingContext: null,
        contextMenuGroupId: 'navigation',
        contextMenuOrder: 1.1,
        run: function (ed) {
            if (occode.editorWidget.editorState != occode.editorStates.BUSY) {
                occode.loadEditor({url: occode.$editorContainer.data('url'), filePath: occode.$editorContainer.data('filePath')}, true);
            }
        },
    });

    // change event
    editor.onDidChangeModelContent(function (e) {
        occode.setEditorState(occode.editorStates.MODIFIED);
    });

    // cursor position change
    editor.onDidChangeCursorPosition(function (e) {
        occode.notifyCursorPosition(e.position);
    });

    // state change event
    occode.onStateChange = occode.onEditorStateChange;
};

occode.initEditorBody = function (editorId, resource, isNewResource) {
    occode.$editorContainer.data('editorId', editorId);
    occode.$editorContainer.data('url', resource.url);
    occode.$editorContainer.data('filePath', resource.filePath);
    occode.$editorContainer.data('isNewResource', !!isNewResource);
    occode.highlightSelectedResource(resource.filePath);
    debugger;
    return occode.$editorBody;
};

occode.resetEditorBody = function () {
    occode.$editorContainer.data('editorId', null);
    occode.$editorContainer.data('url', null);
    occode.$editorContainer.data('filePath', null);
    occode.$editorContainer.data('isNewResource', false);
    return occode.$editorBody.empty();
};

occode.saveResourceState = function () {
    if (occode.editorWidget.editor && occode.editorWidget.editor.getModel() && occode.editorWidget.resourceName) {
        occode.storage.set(occode.editorWidget.resourceName, JSON.stringify(occode.editorWidget.editor.saveViewState()));
    }
};

occode.restoreResourceState = function () {
    if (occode.editorWidget.editor && occode.editorWidget.editor.getModel()
    && occode.editorWidget.resourceName && occode.storage.get(occode.editorWidget.resourceName)) {
        occode.editorWidget.editor.restoreViewState(JSON.parse(occode.storage.get(occode.editorWidget.resourceName)));
    }
};

occode.setEditor = function (data, resource, isNewResource) {
    var resourceLang = occode.getLanguageByExtension(occode.getResourceExt(resource.url) || resource.extension || occode.defaultExt) || occode.getLanguageByMimetype(resource.mimetype);
    var lang = resourceLang || occode.defaultLang || occode.fallbackLang;

    if (!occode.editorWidget.editor) {
        occode.terminalEnabled();// OCC
        occode.resetEditorBody();
        debugger;
        occode.editorWidget.editor = monaco.editor.create(occode.editorElement, {
            theme: occode.editorTheme(),
            minimap: {enabled: occode.minimapEnabled()},
            //terminal: {enabled: occode.terminalEnabled()}, // OCC
            fontSize: 13,
            model: null,
            lang: 'shell', // OCC lang, value
            value: occode.defaultEditorValue,
        });
        occode.setEditorEvents(occode.editorWidget.editor);
    } else {
        occode.saveResourceState();
    }

    var oldModel = occode.editorWidget.editor.getModel();
    var newModel = monaco.editor.createModel(data, lang.id);
    occode.editorWidget.editor.setModel(newModel);
    occode.editorWidget.resourceName = resource.url;
    occode.restoreResourceState();
    occode.initEditorBody(occode.editorWidget.editor.getId(), resource, isNewResource);

    occode.setEditorState(occode.editorStates.LOADED);
    occode.editorWidget.editor.focus();
    occode.notifyCursorPosition(occode.editorWidget.editor.getPosition());
    occode.notifyLanguage(lang);

    if (oldModel) {
        oldModel.dispose();
    }
};

occode.clearEditor = function (alt_content) {
    if (occode.editorWidget.editor) {
        if (occode.editorWidget.editor.getModel()) {
            occode.editorWidget.editor.getModel().dispose();
        }
        occode.editorWidget.editor.dispose();
        occode.editorWidget.editor = null;
        occode.editorWidget.resourceName = null;
        occode.setEditorState(occode.editorStates.INIT);
    }
    occode.resetEditorBody().append(alt_content || '');
    occode.notifyCursorPosition(null);
    occode.notifyLanguage(null);
};

occode.loadEditor = function (resource, forceReload, isNewResource) {
    if (!forceReload && (occode.editorWidget.resourceName == resource.url || (occode.editorWidget.editorState == occode.editorStates.MODIFIED && !confirm('Current changes not saved. Are you sure to move on without saving?')))) {
        occode.editorWidget.editor.focus();
        return false;
    }
    if (isNewResource) {
        occode.setEditor(occode.defaultEditorValue, resource, isNewResource);
    } else {
        $.ajax({
            type: 'GET',
            url: resource.url,
            dataType: 'text',
            cache: false,
            beforeSend: function (xhr, settings) {
                occode.$editorLoader.show();
            },
            success: function (data, status, xhr) {
                if (status == 'success') {
                    resource.mimetype = xhr.getResponseHeader('X-File-Mimetype');
                    resource.extension = xhr.getResponseHeader('X-File-Extension');
                    resource.encoding = xhr.getResponseHeader('X-File-Encoding');
                    occode.setEditor(data, resource);
                } else {
                    occode.clearEditor(occode.editorBodyMsg('<h1 class="text-center">Error while loading file !</h1>'));
                }
            },
            error: function (xhr, status, err) {
                occode.clearEditor(
                    occode.editorBodyMsg(
                        '<h1 class="text-center">Error while loading file !</h1>'+
                        '<h2 class="text-center text-danger">'+err+'</h2>'
                    )
                );
            },
            complete: function (xhr, status) {
                occode.$editorLoader.hide();
            },
        });
    }
};

// OCC
occode.preLoadEditor = function (resource, forceReload, isNewResource) {
//    if (!forceReload && (occode.editorWidget.resourceName == resource.url || (occode.editorWidget.editorState == occode.editorStates.MODIFIED && !confirm('Current changes not saved. Are you sure to move on without saving?')))) {
//        occode.editorWidget.editor.focus();
//        return false;
//    }
    if (isNewResource) {
        occode.setEditor('', resource, isNewResource);
    } else {
        $.ajax({
            type: 'GET',
            url: resource.url,
            dataType: 'text',
            cache: false,
//            beforeSend: function (xhr, settings) {
//                occode.$editorLoader.show();
//            },
            success: function (data, status, xhr) {
                if (status == 'success') {
                    resource.mimetype = xhr.getResponseHeader('X-File-Mimetype');
                    resource.extension = xhr.getResponseHeader('X-File-Extension');
                    resource.encoding = xhr.getResponseHeader('X-File-Encoding');
                    occode.setEditor(data, resource);
                } else {
                    //occode.clearEditor(occode.editorBodyMsg('<h1 class="text-center">Error while loading file !</h1>'));
                }
                conslole.log(`preload success status: ${status}, resource.mimetype ${resource.mimetype}`);
            },
            error: function (xhr, status, err) {
                 conslole.log(`preload error status: ${status}`);
//                occode.clearEditor(
//                    occode.editorBodyMsg(
//                        '<h1 class="text-center">Error while loading file !</h1>'+
//                        '<h2 class="text-center text-danger">'+err+'</h2>'
//                    )
//                );
            },
            complete: function (xhr, status) {
                conslole.log(`preload complete status: ${status}`);
               // occode.$editorLoader.hide();
            },
        });
    }
};


occode.validResource = function (filename) {
    var ext = occode.getExt(filename);
    var lang = ext ? occode.getLanguageByExtension(ext) : null;
    return lang ? occode.allowedLangIds.indexOf(lang.id) > -1 : false;
};

occode.openResource = function ($resourceElement) {
        // OCC
    //occode.preLoadEditor($resourceElement, false, false)
    if (!occode.validResource($resourceElement.data('pathName'))) {
        alert('This file type is not allowed to open !');
        return false;
    } else {
        occode.loadEditor({url: $resourceElement.data('url'), filePath: $resourceElement.data('pathName')});
        return true;
    }
};

occode.openNewFileModal = function ($resourceElement) {
    var $modal = $('#fileNameModal');
    $modal.find('.modal-title').text('Create New File');
    $modal.find('#base_url').val($resourceElement.data('url').replace(/\.txt$/i, ''));
    $modal.find('#base_path_name').val($resourceElement.data('pathName'));
    $modal.find('.base-path-name').text($resourceElement.data('pathName'));
    $modal.find('#new_filename').val('');
    $modal.modal({show: true, backdrop: 'static'});
};
