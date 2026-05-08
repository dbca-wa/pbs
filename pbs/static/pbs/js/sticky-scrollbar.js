/**
 * Adds a sticky horizontal scrollbar fixed at the bottom of the viewport
 * that mirrors the scroll position of the #changelist-form .results container.
 */
(function($) {
    $(document).ready(function() {
        var $results = $('#changelist-form .results');
        if ($results.length === 0) return;

        var $table = $results.find('table');
        if ($table.length === 0) return;

        // Proxy div: a thin fixed bar that mimics the scrollable width
        var $proxy = $('<div class="sticky-hscroll-proxy"><div></div></div>');
        $proxy.css({
            position: 'fixed',
            bottom: '0',
            overflowX: 'scroll',
            overflowY: 'hidden',
            zIndex: 1019,
            height: '16px',
        });
        $proxy.find('div').css({ height: '1px' });
        $('body').append($proxy);

        var syncing = false;

        // Sync proxy -> results
        $proxy.on('scroll', function() {
            if (syncing) return;
            syncing = true;
            $results.scrollLeft($proxy.scrollLeft());
            syncing = false;
        });

        // Sync results -> proxy
        $results.on('scroll', function() {
            if (syncing) return;
            syncing = true;
            $proxy.scrollLeft($results.scrollLeft());
            syncing = false;
        });

        function update() {
            var tableWidth = $table.outerWidth(true);
            var containerWidth = $results.outerWidth();
            var offset = $results.offset();

            $proxy.css({
                left: offset.left,
                width: containerWidth,
            });
            $proxy.find('div').css({ width: tableWidth });

            // Show proxy bar only when table is wider than its container
            $proxy.toggle(tableWidth > containerWidth);
        }

        update();
        $(window).on('resize', update);
        // Re-check after dynamic content changes (e.g. inline rows added)
        new MutationObserver(update).observe($results[0], { childList: true, subtree: true });
    });
})(jQuery);
