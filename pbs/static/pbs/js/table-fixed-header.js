(function($) {

$.fn.fixedHeader = function (options) {
 var navbarHeight = $('nav.navbar.fixed-top').outerHeight() || 40;
 var config = {
   topOffset: navbarHeight
 };
 if (options){ $.extend(config, options); }

 return this.each(function() {
  var o = $(this);
  var $win = $(window);
  var $head = $('thead.header', o);
  var isFixed = 0;
  var $results = $('#changelist-form .results');
  if (!$head.length) return;

  var headTop = $head.offset().top - config.topOffset;

  // Build a fixed wrapper div with overflow:hidden to clip the cloned header
  var $wrapper = $('<div class="fixed-header-wrapper d-none"></div>');
  $wrapper.css({
    position: 'fixed',
    top: navbarHeight + 'px',
    overflow: 'hidden',
    zIndex: 1020,
    backgroundColor: '#fff',
    borderBottom: '1px solid #d5d5d5'
  });

  // Clone the full table into the wrapper so column widths are respected
  var $cloneTable = $('<table></table>');
  $cloneTable.attr('class', o.attr('class'));
  // Explicitly copy font styles from the original table so the cloned header
  // renders at exactly the same size and prevents column width mismatches.
  $cloneTable.css({
    fontSize: o.css('fontSize'),
    fontFamily: o.css('fontFamily'),
    borderCollapse: o.css('borderCollapse'),
    tableLayout: o.css('tableLayout')
  });
  var $cloneThead = $head.clone().removeClass('header').addClass('header-copy');
  $cloneTable.append($cloneThead);
  $wrapper.append($cloneTable);
  $('body').append($wrapper);

  function syncWidths() {
    var containerLeft = $results.length ? $results.offset().left : o.offset().left;
    var containerWidth = $results.length ? $results.outerWidth() : o.width();
    $wrapper.css({ left: containerLeft, width: containerWidth });

    // Sync individual column widths
    $head.find('tr:first th').each(function(i) {
      var w = $(this).outerWidth();
      $wrapper.find('thead tr:first th:eq(' + i + ')').css({ width: w + 'px', minWidth: w + 'px' });
    });

    // Sync horizontal scroll offset
    var scrollLeft = $results.length ? $results.scrollLeft() : 0;
    $cloneTable.css('margin-left', -scrollLeft + 'px');
  }

  function processScroll() {
    if (!o.is(':visible')) return;
    var scrollTop = $win.scrollTop();
    var t = $head.offset().top - config.topOffset;
    if (!isFixed && headTop !== t) { headTop = t; }
    if (scrollTop >= headTop && !isFixed) {
      isFixed = 1;
      syncWidths();
      $wrapper.removeClass('d-none');
    } else if (scrollTop <= headTop && isFixed) {
      isFixed = 0;
      $wrapper.addClass('d-none');
    }
  }

  $win.on('scroll', processScroll);

  // Sync horizontal scroll
  $results.on('scroll.fixedHeader', function() {
    if (isFixed) {
      $cloneTable.css('margin-left', -$results.scrollLeft() + 'px');
    }
  });

  $win.on('resize.fixedHeader', function() {
    headTop = $head.offset().top - config.topOffset;
    if (isFixed) syncWidths();
  });

  processScroll();
 });
};

})(jQuery);
