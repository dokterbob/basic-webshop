django.jQuery(function () {
    $ = django.jQuery;

    var object_tools = $('.object-tools:first');
    var title;
    var tool_items = $('<span/>');

    if (object_tools.length == 0) {
        object_tools = $('<ul class="object-tools"></ul>');
        $('#content-main').prepend(object_tools);
    }


    $('.inline-group').each(function(index) {
        title = $(this).find('h2:first').text()
        tool_items.append($('<li><a href="#'+this.id+'">'+title+'</a></li>'));
    });
    
   object_tools.prepend(tool_items);
});

