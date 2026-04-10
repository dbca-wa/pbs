var Vis =  (function visModule(window, document, $) {
    var _getToolsVisibility = function getToolsVisibility(store, key){
        var state = JSON.parse(store.getItem(key) || "false");
        return state;
    };
    function _setToolsVisibility(store, key, state) {
        var val = JSON.stringify(state);
        store.setItem(key, JSON.stringify(val));
    };
    function _ensureToolsHidden(tools, toolsButton, store, visKey) {
        if (!tools.hasClass("d-none")) {
            toolsButton.removeClass("btn-danger");
            tools.addClass("d-none");
            toolsButton.addClass("btn-success");
            this.setToolsVisibility(store, visKey, false);
        }
    };
    function _ensureToolsVisible(tools, toolsButton, store, visKey) {
        if (tools.hasClass("d-none")) {
            toolsButton.removeClass("btn-success");
            tools.removeClass("d-none");
            toolsButton.addClass("btn-danger");
            this.setToolsVisibility(store, visKey, true);
        }
    }
    var module = {
        getToolsVisibility: _getToolsVisibility,
        setToolsVisibility: _setToolsVisibility,
        ensureToolsHidden: _ensureToolsHidden,
        ensureToolsVisible: _ensureToolsVisible
    };
    return module;
})(window, document, $);
