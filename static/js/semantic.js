// Semantic UI

$(document)
    .ready(function() {

        // fix menu when passed
        $('.masthead')
            .visibility({
                once: false,
                onBottomPassed: function() {
                    $('.fixed.menu').transition('fade in');
                },
                onBottomPassedReverse: function() {
                    $('.fixed.menu').transition('fade out');
                }
            });

        // create sidebar and attach to menu open
        $('.ui.sidebar')
            .sidebar('attach events', '.toc.item');

        // customizes checkboxes
        $('.ui.checkbox')
            .checkbox();

        // customizes dropdown menu
        $('#diet')
            .dropdown();

        // allows user to dismiss notifications
        $('.message .close')
          .on('click', function() {
            $(this)
              .closest('.message')
              .transition('fade')
    ;
  })
;


    });
