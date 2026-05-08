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

        // Proxy div: a thin fixed bar that mimics the scrollable width.
        // Positioned above any fixed-bottom bar (e.g. Save / Collapse all).
        var $fixedBottom = $('div.fixed-bottom');
        var bottomOffset = $fixedBottom.length ? $fixedBottom.outerHeight() : 0;

        var $proxy = $('<div class="sticky-hscroll-proxy"><div></div></div>');
        $proxy.css({
            position: 'fixed',
            bottom: bottomOffset,
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
            var el = $results[0];
            var rect = el.getBoundingClientRect();
            var overflows = el.scrollWidth > el.clientWidth;

            $proxy.css({ left: rect.left, width: rect.width });
            $proxy.find('div').css({ width: el.scrollWidth });
            $proxy.toggle(overflows);
        }

        update();
        $(window).on('resize load', update);
        // Re-check after dynamic content changes (e.g. inline rows added)
        new MutationObserver(update).observe($results[0], { childList: true, subtree: true });
    });
})(jQuery);
