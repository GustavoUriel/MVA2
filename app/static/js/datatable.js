(function(window){
    window.MVA2 = window.MVA2 || {};

    MVA2.datatable = {
        // Map server response to DataTables expected format
        mapServerResponse: function(apiResponse, recordsFieldName){
            const items = apiResponse[recordsFieldName] || apiResponse.items || [];
            return {
                data: items,
                recordsTotal: apiResponse.total_count || apiResponse.total || items.length,
                recordsFiltered: apiResponse.total_count || apiResponse.total || items.length
            };
        },

        init: function(selector, columns, ajaxUrl, options){
            options = options || {};
            // Build buttons if requested
            var buttons = [];
            if (options.exportButtons !== false){
                buttons.push({ extend: 'excelHtml5', text: 'Export to Excel', className: 'btn btn-sm btn-outline-primary' });
                buttons.push({ extend: 'copyHtml5', text: 'Copy', className: 'btn btn-sm btn-outline-secondary' });
                buttons.push({ extend: 'colvis', text: 'Columns', className: 'btn btn-sm btn-outline-secondary' });
            }

            var cfg = {
                processing: true,
                // default to client-side loading because our API returns {patients: [...]} or {taxonomies: [...]} shapes
                serverSide: options.serverSide === true,
                ajax: {
                    url: ajaxUrl,
                    data: function(d){
                        // include per-column filters if present
                        if (options.columnFilterInputs){
                            options.columnFilterInputs.forEach(function(fn){
                                try{
                                    var obj = fn();
                                    Object.assign(d, obj);
                                }catch(e){}
                            });
                        }
                        return d;
                    },
                    dataSrc: function(json){
                        // If the server returned nothing useful
                        if (!json) return [];

                        // If we get a string back it's likely an HTML page (e.g. login redirect)
                        if (typeof json === 'string'){
                            var s = json.trim().toLowerCase();
                            // crude HTML detection
                            if (s.indexOf('<!doctype') === 0 || s.indexOf('<html') === 0 || s.indexOf('<div') === 0){
                                console.warn('Datatable AJAX returned HTML. This is often caused by an unauthenticated session (login redirect). Redirecting to login.');
                                // redirect user to login so they can re-authenticate
                                try{ window.location.href = '/auth/login'; }catch(e){}
                                return [];
                            }
                            // otherwise try to parse JSON-like strings
                            try{ json = JSON.parse(json); }catch(e){ return []; }
                        }

                        if (Array.isArray(json)) return json;
                        if (json.data) return json.data;
                        if (json.items) return json.items;
                        if (json.patients) return json.patients;
                        if (json.taxonomies) return json.taxonomies;
                        // fallback: try to extract first array value
                        for (var k in json){ if (Array.isArray(json[k])) return json[k]; }
                        return [];
                    },
                    xhrFields: { withCredentials: true }
                },
                columns: columns,
                pageLength: options.pageLength || 25,
                responsive: true,
                dom: options.dom || "<'d-flex justify-content-between mb-2'Bf>rt<'d-flex justify-content-between mt-2'ip>",
                buttons: buttons
            };

            // decorate createdRow to apply color rules and label chips
            var userCreatedRow = cfg.createdRow;
            cfg.createdRow = function(row, data, dataIndex){
                try{
                    var tableId = selector.replace('#','');
                    // apply persisted color rules
                    var rules = [];
                    try{ rules = JSON.parse(localStorage.getItem('datatable_rules_' + tableId) || '[]'); }catch(e){}
                    rules.forEach(function(rule){
                        try{
                            var val = data[rule.col];
                            if (val === undefined || val === null) return;
                            var match = false;
                            switch(rule.op){
                                case 'eq': match = (String(val) === String(rule.value)); break;
                                case 'neq': match = (String(val) !== String(rule.value)); break;
                                case 'gt': match = (parseFloat(val) > parseFloat(rule.value)); break;
                                case 'lt': match = (parseFloat(val) < parseFloat(rule.value)); break;
                                case 'contains': match = (String(val).indexOf(rule.value) !== -1); break;
                            }
                            if (match){
                                var colIdx = -1;
                                for (var i=0;i<columns.length;i++){
                                    if (columns[i].data === rule.col){ colIdx = i; break; }
                                }
                                if (colIdx >= 0){ $('td', row).eq(colIdx).css('background-color', rule.color); }
                            }
                        }catch(e){}
                    });
                }catch(e){ console.error('rule apply', e); }

                // render labels (global labels, not per-row labels in this iteration)
                try{
                    var labelKey = 'datatable_labels_' + selector.replace('#','');
                    var labels = JSON.parse(localStorage.getItem(labelKey) || '[]');
                    if (labels && labels.length){
                        var chipHtml = labels.map(function(l){ return '<span class="badge rounded-pill me-1" style="background:'+l.color+';color:#000">'+l.name+'</span>'; }).join('');
                        // put chips into last cell
                        $('td', row).last().prepend('<div class="mb-1">'+chipHtml+'</div>');
                    }
                }catch(e){ console.error('labels render', e); }

                if (typeof userCreatedRow === 'function') userCreatedRow(row, data, dataIndex);
            };

            // ensure the selector exists and is a table
            var $el = $(selector);
            if (!$el || $el.length === 0){ console.error('Datatable selector not found:', selector); return null; }
            if ($el[0].tagName.toLowerCase() !== 'table'){ console.error('Datatable selector is not a table element:', selector, $el[0]); return null; }

            var table = null;
            try{
                table = $(selector).DataTable(cfg);
            }catch(initErr){
                console.error('DataTable init failed for selector', selector, initErr);
                // Provide a visual hint in the table container
                try{
                    var container = document.querySelector(selector);
                    if (container && container.parentNode){
                        var errDiv = document.createElement('div');
                        errDiv.className = 'alert alert-danger small';
                        errDiv.textContent = 'Failed to initialize table. See console for details.';
                        container.parentNode.insertBefore(errDiv, container);
                    }
                }catch(e){}
                return null;
            }

            // Add per-column text filters in the header if enabled
            if (options.columnFilters){
                $(selector + ' thead tr').clone(true).appendTo(selector + ' thead');
                $(selector + ' thead tr:eq(1) th').each(function(i){
                    var title = $(this).text();
                    $(this).html('<input class="form-control form-control-sm" placeholder="Filter '+title+'" />');
                    $('input', this).on('keyup change clear', function(){
                        if (table.column(i).search() !== this.value){ table.column(i).search(this.value).draw(); }
                    });
                });
            }

            // Inline editing: double-click to edit a cell
            if (options.inlineEdit){
                $(selector + ' tbody').on('dblclick', 'td', function(e){
                    var cell = table.cell(this);
                    var colIdx = cell.index().column;
                    var rowData = table.row(cell.index().row).data();
                    var colDef = columns[colIdx] || {};
                    var field = colDef.data;
                    if (!field || colDef.editable === false) return;
                    var original = cell.data();
                    var $input = $('<input type="text" class="form-control form-control-sm"/>').val(original);
                    $(this).html($input);
                    $input.focus();
                    function finish(save){
                        var val = $input.val();
                        if (save && val !== original){
                            var id = rowData.id || rowData.ID || rowData.pk || rowData._id || rowData.patient_id || rowData.taxonomy_id;
                            if (id){
                                var url = (options.patchUrl || ajaxUrl) + '/' + id;
                                fetch(url, {
                                    method: options.patchMethod || 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    credentials: 'same-origin',
                                    body: JSON.stringify({ [field]: val })
                                }).then(function(resp){ if (!resp.ok) throw new Error('Server error'); return resp.json(); })
                                .then(function(data){ cell.data(data[field] !== undefined ? data[field] : val).draw(); })
                                .catch(function(err){ console.error('Save failed', err); cell.data(original).draw(); });
                            } else { cell.data(val).draw(); }
                        } else { cell.data(original).draw(); }
                    }
                    $input.on('blur', function(){ finish(true); });
                    $input.on('keydown', function(ev){ if (ev.key === 'Enter') finish(true); if (ev.key === 'Escape') finish(false); });
                });
            }

            // Wire UI buttons for labels and rules if present
            try{
                var tableId = selector.replace('#','');
                var labelsBtn = document.getElementById(tableId + '_labels_btn');
                var labelsModal = document.getElementById(tableId + '_labels_modal');
                var rulesBtn = document.getElementById(tableId + '_color_rules_btn');
                var rulesModal = document.getElementById(tableId + '_color_rules_modal');
                if (labelsBtn && labelsModal){
                    labelsBtn.addEventListener('click', function(){ MVA2.datatable.showLabelsManager(tableId); new bootstrap.Modal(labelsModal).show(); });
                }
                if (rulesBtn && rulesModal){
                    rulesBtn.addEventListener('click', function(){ MVA2.datatable.showRulesManager(tableId, columns); new bootstrap.Modal(rulesModal).show(); });
                }
            }catch(e){ console.error('ui wire', e); }

            return table;
        },

        // persistence helpers
        getStoredLabels: function(tableId){ try{ return JSON.parse(localStorage.getItem('datatable_labels_' + tableId) || '[]'); }catch(e){ return []; } },
        setStoredLabels: function(tableId, labels){ localStorage.setItem('datatable_labels_' + tableId, JSON.stringify(labels || [])); },
        getStoredRules: function(tableId){ try{ return JSON.parse(localStorage.getItem('datatable_rules_' + tableId) || '[]'); }catch(e){ return []; } },
        setStoredRules: function(tableId, rules){ localStorage.setItem('datatable_rules_' + tableId, JSON.stringify(rules || [])); },

        // UI: show labels manager
        showLabelsManager: function(tableId){
            var list = document.getElementById(tableId + '_labels_list');
            var name = document.getElementById(tableId + '_new_label_name');
            var color = document.getElementById(tableId + '_new_label_color');
            var add = document.getElementById(tableId + '_add_label');
            var labels = MVA2.datatable.getStoredLabels(tableId) || [];
            function render(){
                list.innerHTML = labels.map(function(l,i){ return '<div class="d-flex justify-content-between align-items-center mb-1"><div><span class="badge rounded-pill me-2" style="background:'+l.color+';color:#000">'+l.name+'</span></div><div><button class="btn btn-sm btn-outline-danger" data-idx="'+i+'">Remove</button></div></div>'; }).join('');
                list.querySelectorAll('button[data-idx]').forEach(function(btn){ btn.addEventListener('click', function(){ labels.splice(parseInt(this.dataset.idx,10),1); MVA2.datatable.setStoredLabels(tableId, labels); render(); }); });
            }
            render();
            add.onclick = function(){ if (!name.value) return; labels.push({ name: name.value, color: color.value }); MVA2.datatable.setStoredLabels(tableId, labels); name.value=''; render(); };
        },

        // UI: show color rules manager
        showRulesManager: function(tableId, columns){
            var list = document.getElementById(tableId + '_rules_list');
            var selCol = document.getElementById(tableId + '_rule_col');
            var selOp = document.getElementById(tableId + '_rule_op');
            var val = document.getElementById(tableId + '_rule_value');
            var color = document.getElementById(tableId + '_rule_color');
            var add = document.getElementById(tableId + '_add_rule');
            var rules = MVA2.datatable.getStoredRules(tableId) || [];
            function render(){
                list.innerHTML = rules.map(function(r,i){ return '<div class="d-flex justify-content-between align-items-center mb-1"><div><strong>'+r.col+'</strong> '+r.op+' <em>'+r.value+'</em></div><div><span class="badge" style="background:'+r.color+'">&nbsp;&nbsp;&nbsp;</span> <button class="btn btn-sm btn-outline-danger" data-idx="'+i+'">Remove</button></div></div>'; }).join('');
                list.querySelectorAll('button[data-idx]').forEach(function(btn){ btn.addEventListener('click', function(){ rules.splice(parseInt(this.dataset.idx,10),1); MVA2.datatable.setStoredRules(tableId, rules); render(); }); });
            }
            render();
            add.onclick = function(){ if (!selCol.value) return; rules.push({ col: selCol.value, op: selOp.value, value: val.value, color: color.value }); MVA2.datatable.setStoredRules(tableId, rules); val.value=''; render(); };
        }
    };
})(window);
