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

function navigate_button() {
    display_tag($("#navigateinput").val())
}

function display_tag(tag) {
    if (!/[A-Za-z0-9_-]{8}/.test(tag)) return false;
    $.getJSON('/download/' + tag, function(result) {
        if (result['status']) {
            current_tag = tag;
            if (result['editable']) {
                $(".editable").show();
                $("#inputarea").val(result['body']);
            } else {
                $(".editable").hide();
            }
            display_tag_draw(tag, result['body']); 
        }
    });
    return true;
}

function display_tag_draw(tag, text) {
    if (!/[A-Za-z0-9_-]{8}/.test(tag)) return false;
    var link_html = " Available at: <a href='/" + tag +
                    "'>http://texthole.arkem.org/" + tag + "</a>";
    $('#content').text(text);
    $('#link').html(link_html);
    $('#viewarea').show();
    $('#navigateinput').val(tag)
}

function create_tag(tag) {
    var message = {};
    message.body = $("#inputarea").val();
    if (message.body.length == 0 ||
        message.body == $("#content").text()) return;

    if (logged_in()) {
        message.authenticated = !$("#anonymous").is(":checked");
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
                if (!$("#anonymous").is(":checked")) {
                    $(".editable").show();
                } else {
                    $(".editable").hide();
                }
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
                $("#navigateinput").val("");
            }}
    );

}
