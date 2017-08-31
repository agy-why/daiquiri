angular.module('core')

.directive('daiquiriTable', ['$timeout', '$compile', '$templateCache', 'TableService', function($timeout, $compile, $templateCache, TableService) {
    return {
        templateUrl: function(element, attrs) {
            var staticurl = angular.element('meta[name="staticurl"]').attr('content');
            return staticurl + 'core/html/table.html';
        },
        scope: {
            'pageSizes': '='
        },
        link: function(scope, element, attrs) {
            scope.table = TableService;

            if (angular.isDefined(attrs.database) && angular.isDefined(attrs.table)) {
                TableService.init(attrs.database, attrs.table, scope.pageSizes);
            }

            // refresh the tooltips everytime a new set of columns is fetched
            scope.$watch(function() {
                return angular.isDefined(scope.table.columns) && scope.table.columns.$resolved;
            }, function(new_value) {
                if (new_value) {
                    var template = $templateCache.get('tooltip.html');

                    $timeout(function() {
                        angular.forEach(scope.table.columns, function(column, index) {
                            var isolated_scope = scope.$new(true);
                            isolated_scope.column = column;
                            isolated_scope.table = scope.table;

                            $('[data-column-index="' + index + '"] .info').popover({
                                title: '<strong>' + column.name + '</strong>',
                                content: $compile(template)(isolated_scope),
                                html: true,
                                trigger: 'hover',
                                placement: 'bottom',
                                container: '.daiquiri-table'
                            });
                        });
                    });
                }
            });

        }
    };
}])

.factory('TableService', ['$http', '$resource', '$q', '$document', function($http, $resource, $q, $document) {

    /* get the base url */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    /* configure the resources */

    var resources = {
        rows: $resource(baseurl + 'serve/api/rows/'),
        columns: $resource(baseurl + 'serve/api/columns/'),
    };

    /* create the metadata service */

    var service = {
        file_base_url: baseurl + 'serve/files/',
        params: {
            page: 1,
            page_size: 10,
            ordering: null,
            filter: null
        },
        i18n: {
            first: gettext('First'),
            previous: gettext('Previous'),
            next: gettext('Next'),
            last: gettext('Last'),
            reset: gettext('Reset'),
            filter: gettext('Filter'),
            count: function() {
                var page_count = Math.ceil(service.count / service.params.page_size);
                if (service.params.filter) {
                    return interpolate(gettext('Page %s of %s (%s rows total, filtering for "%s")'), [service.params.page,page_count, service.count, service.params.filter]);
                } else {
                    return interpolate(gettext('Page %s of %s (%s rows total)'), [service.params.page,page_count, service.count]);
                }
            },
            page_size: function(value) {
                return interpolate(gettext('Show %s of %s rows'), [value, service.count]);
            },
            'description': gettext('Description'),
            'unit': gettext('Unit'),
            'ucd': gettext('UCD'),
            'datatype': gettext('Data type'),
            'arraysize': gettext('Size'),
            'principal': gettext('Principal'),
            'indexed': gettext('Indexed'),
            'std': gettext('STD'),
        },
        page_sizes: [10, 20, 100],
        filter_string: null,
        updated: false,
        active: {},
        modal: {}
    };

    service.init = function(database, table, page_sizes) {
        service.ready = false;

        if (angular.isDefined(page_sizes)) {
            service.page_sizes = page_sizes;
            service.params.page_size = page_sizes[0];
        }

        if (angular.isDefined(database) && angular.isDefined(table)) {
            service.params.database = database;
            service.params.table = table;

            service.columns = resources.columns.query(service.params);
            service.reset();
        } else {
            service.columns = [];
            service.rows = [];
        }
    };

    service.fetch = function() {
        return resources.rows.paginate(service.params, function(response) {
            service.count = response.count;
            service.rows = response.results;

            service.first_page = (service.params.page == 1);
            service.last_page = (service.params.page * service.params.page_size > service.count);

            service.ready = true;
        }).$promise;
    };

    service.first = function() {
        if (!service.first_page) {
            service.params.page = 1;
            service.fetch();
        }
    };

    service.previous = function() {
        if (!service.first_page) {
            service.params.page -= 1;
            return service.fetch();
        }
    };

    service.next = function() {
        if (!service.last_page) {
            service.params.page += 1;
            return service.fetch();
        }
    };

    service.last = function() {
        if (!service.last_page) {
            service.params.page = Math.ceil(service.count / service.params.page_size);
            service.fetch();
        }
    };

    service.reset = function() {
        service.params.page = 1;
        service.params.ordering = null;
        service.params.filter = null;
        service.filter_string = null;
        service.fetch();
    };

    service.filter = function() {
        service.params.filter = service.filter_string;
        service.fetch();
    };

    service.order = function(column_name) {
        if (service.params.ordering == column_name) {
            service.params.ordering = '-' + column_name;
        } else {
            service.params.ordering = column_name;
        }
        service.fetch();
    };

    service.resize = function (column_index) {
        var zero = event.pageX;
        var table = angular.element('.daiquiri-table-pane .table');
        var th = angular.element('[data-column-index="' + column_index + '"]');
        var width = th.width();

        table.addClass('no-select');
        function enterResize(event) {
            var newWidth = width + event.pageX - zero;
            if (newWidth >= 40) th.width(newWidth);
        }

        function exitResize() {
            table.removeClass('no-select');
            $document.off('mousemove',enterResize);
            $document.off('mouseup',exitResize);
        }

        $document.on('mousemove', enterResize);
        $document.on('mouseup', exitResize);
    };

    service.activate = function(column_index, row_index) {
        service.active = {
            column_index: column_index,
            row_index: row_index
        }
    }

    service.open_modal = function(event, column_index, row_index) {
        event.preventDefault();
        event.stopPropagation();

        service.activate(column_index, row_index);

        service.update_modal().then(function() {
            $('#daiquiri-table-modal').modal('show');
        })
    }

    service.update_modal = function() {
        var file_path = service.rows[service.active.row_index][service.active.column_index];
        var url = service.file_base_url + file_path;

        if (service.columns[service.active.column_index].mode == 'note') {
            return $http.get(url).then(function(result) {
                service.modal.title = file_path;
                service.modal.pre = result.data;
            });
        } else if (service.columns[service.active.column_index].mode == 'preview') {
            service.modal.src = url;
            return $q.when();
        } else {
            return $q.when();
        }
    };

    service.previous_modal = function() {
        if (service.active.row_index > 0) {
            // decrement the row_index and update modal
            service.active.row_index -= 1;
            service.update_modal();
        } else if (!service.first_page) {
            // first load previous page
            service.previous().then(function() {
                // set row_index to the last row and update modal
                service.active.row_index = service.rows.length - 1;
                service.update_modal();
            });
        }
    }

    service.next_modal = function() {
        if (service.active.row_index < service.rows.length - 1) {
            // increment the row_index and update modal
            service.active.row_index += 1;
            service.update_modal();
        } else if (!service.last_page) {
            // first load next page
            service.next().then(function() {
                // set row_index to 0 and update modal
                service.active.row_index = 0;
                service.update_modal();
            });
        }
    }

    return service;
}]);
