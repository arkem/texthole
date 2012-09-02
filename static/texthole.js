var current_tag = 'None';
var current_user = 'None';

function logged_in() {
    return current_user != 'None';
}

function page_setup(tag, user) {
    if (tag != 'None') {
        current_tag = tag;
        display_tag(tag);
    }
    if (user != 'None') {
        current_user = user;
        $(".loggedin").show();
    }
}

function display_tag(tag) {
    if (!/[A-Za-z0-9_-]{8}/.test(tag)) return false;
    $.getJSON('/download/' + tag, function(result) {
        if (result['status']) {
            if (result['editable']) {
                $(".editable").show();
            } else {
                $(".editable").hide();
            }
            display_tag_draw(tag, result['body']); 
        }
    });
    return true;
}

function display_tag_draw(tag, text) {
    var link = "Viewing: <a href='/" + tag + "'>" + tag + "</a>";
    $('#viewarea_label').html(link);
    $('#content').text(text);
    $('#viewarea').show();
}

function create_tag(tag) {
    var message = {};
    message.body = $("#inputarea").val();
    if (message.body.length == 0 ||
        message.body == $("#content").text()) return;

    if (logged_in()) {
        message.authenticated = $("anonymous").attr("checked") != "checked";
    } else {
        if (tag != 'None') return; // Can't edit if not logged in.
        message.authenticated = false;
    }
    if (tag != 'None') {
        message.overwrite = tag;
    }
    message.expiry = $("#expiry").val()
    $.ajax({url: "/upload",
            type: "POST",
            data: {data: JSON.stringify(message)},
            success: function(result) {
                current_tag = result['message_id'];
                display_tag_draw(result['message_id'], message.body);
                $(".editable").show();
            }}
    );
}

function delete_tag(tag) {
    if (!logged_in()) return;
    message = {};
    message.delete = tag
    message.authenticated = true;
    $.ajax({url: "/upload",
            type: "POST",
            data: {data: JSON.stringify(message)},
            success: function(result) {
                current_tag = 'None';
                $(".editable").hide();
                $("#viewarea").hide();
                $("#inputarea").val("");
            }}
    );

}
