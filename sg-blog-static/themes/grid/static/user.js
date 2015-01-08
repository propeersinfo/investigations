/*
// enrich links to userecho.com
$(document).ready(function() {
    $('a[href^="http://sovietgroove.userecho.com"]').each(function() {
        $(this).mouseenter(function() {
            UE.Popin.preload();
        });
        $(this).click(function() {
            UE.Popin.show();
            return false; // preventing browser from following the link
        });
    })
});
*/

// set a cookie with typical params
// code by quirksmode
function set_cookie(name, value) {
    var days = 365;
    var expires;
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        expires = "; expires="+date.toGMTString();
    } else {
        expires = "";
    }
    document.cookie = name+"="+value+expires+"; path=/";
}

// code by quirksmode
function get_cookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

/*
 * I18N by JavaScript.
 * Server side: set cookie 'user_lang' to value like 'en' or 'ru' (relying on the request header)
 * Client side: execute the following JS code.
 * HTML should look like the following:
 * <div class='i18n'>No lang: <i lang="EN">EN</i> <i lang="RU">RU</i> <i>No lang</i></div>
 */
$(document).ready(function() {
    function get_element_display_mode(elem) {
        var tag = elem.tagName.toLowerCase();
        return (tag == 'div' || tag == 'p') ? 'block' : 'inline';
    }
    var desired_lang = get_cookie('user_lang');
    if(desired_lang) {
        $('.i18n').each(function() {
            $(this).children().each(function(i, alt) {
                if(alt.lang) {
                    var eq = desired_lang.toLowerCase() == alt.lang.toLowerCase();
                    var display = eq ? get_element_display_mode(alt) : 'none';
                    $(alt).css('display', display);
                }
            })
        })
    }
});

//function comment_form_submit(form) {
//    var text_elem = form.elements['text'];
//    var text = $.trim(text_elem.value);
//    if(text.length > 0) {
//        return true;
//    } else {
//        $(text_elem).css('border', '1px solid #f00');
//        return false;
//    }
//}

////////////////////////////////////////////////////
// replace youtube images with video clips
////////////////////////////////////////////////////

function replaceYoutubeImageWithClip(img) {
	var ytid = img.getAttribute('ytid');
	
	repl = document.createElement('iframe');
	repl.setAttribute('width', 300);
	repl.setAttribute('height', 225);
	repl.setAttribute('src', 'http://www.youtube.com/embed/'+ytid+'?autoplay=1&theme=dark');
	repl.setAttribute('frameborder', 0);
	repl.setAttribute('allowfullscreen', 1);
	
	img.parentNode.replaceChild(repl, img)
}
function prepareYoutubeClips() {
  $("img.youtube").each(function(pos,img){
    var preview = img.src;
    img.style.background = "black url(" + preview + ") 50% 50%";
    img.src = "/static/playvideo480.png";
    var a = img.parentNode;
    if(a) {
      a.style.background = "url(" + preview + ")";
      a.style.display = "inline-block";
      a.onclick = function(event) { replaceYoutubeImageWithClip(img); return false; }
    }
  })
}
$(document).ready(function() {
    prepareYoutubeClips()
});

////////////////////////////////////////////////////
// rewrite links to /preview/
////////////////////////////////////////////////////

if(document.location.hostname == 'localhost' && document.location.pathname.indexOf('/preview') == 0) {
    $(document).ready(function() {
        $("a").each(function(pos,a){
            var m = a.href.match(/^(http:..localhost)(.+)$/);
            if(m[2].indexOf('/preview') < 0) {
                a.href = m[1] + '/preview' + m[2];
            }
        });
    });
}

////////////////////////////////////////////////////
// ctrl+arrows navigation
////////////////////////////////////////////////////

$(document).ready(function() {
    if(document.addEventListener) {
        document.addEventListener('keydown', function(event) {
            if (!event.ctrlKey) return;
            var link = null;
            switch (event.keyCode ? event.keyCode : event.which ? event.which : null) {
                case 38: // up arrow
                    link = document.getElementById ('prev-link');
                    break;
                case 40: // down arrow
                    link = document.getElementById ('next-link');
                    break;
            }
            if (link && link.href) {
                document.location = link.href;
            }
        }, false);
    }
});

// return a string like 'Jun 16, 2001'
function format_date_mdy(d) {
    var m_names = new Array("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec");
    var curr_date = d.getDate();
    var curr_month = d.getMonth();
    var curr_year = d.getFullYear();
    return m_names[curr_month] + " " + curr_date + ", " + curr_year;
}

function scroll_bottom() {
    $('html, body').animate({ scrollTop: $(document).height() }, 500);
}

function scroll_top() {
    $('html, body').animate({ scrollTop: '0px' }, 500);
}

function share_popup(url) {
    var w = 700;
    var h = 500;
    var left = (screen.width/2)-(w/2);
    var top = (screen.height/2)-(h/2);
    window.open(url, 'Share', 'toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width='+w+', height='+h+', top='+top+', left='+left);
    return false; // prevent tag A's std behaviour
}

// convert a text input into an element that looks like <a> when non-focused
// and like an editable text input when focused
function setup_plain_editor(input) {
    var plain = $(document.createElement('a'));
    plain.attr('href', '#');
    plain.css({
        'text-decoration': 'none',
        'border-bottom': '1px dashed',

        'line-height': '1.0',
        'display': 'inline-block',
        'vertical-align': 'baseline'
    });
    plain.insertBefore(input);

    function input_focus_lost() {
        if($.trim(input.val()).length > 0) {
            input.hide();
            plain.text(input.val());
            plain.show();
        }
    }

    input_focus_lost();

    input.blur(function() {
        input_focus_lost();
    });

    plain.click(function() {
        input.show();
        input.focus();
        plain.hide();
        return false;
    });
}

$(document).ready(function() {
    //setup_plain_editor('#new_comment_form input[name="name"]');
});

////////////////////////////////////////////////////
// external comments
////////////////////////////////////////////////////

function report_error(selector, msg, fadeOut) {
    var jq = $(selector)
             .css('display', 'table')
             .text(msg);

    if (fadeOut) {
        jq.delay(5000).fadeOut('slow');
    }
}

function add_comment(comment, is_new) {
    if(typeof is_new == 'undefined') {
        is_new = false;
    }
    var date_short = 'n/a';
    var date_long = null;
    if(is_new) {
        date_short = format_date_mdy(new Date());
    } else {
        var date = Date.parse(comment.date);
        if(date) {
            date = new Date(date);
            date_short = format_date_mdy(date);
            date_long = date.toUTCString();
        }
    }

    var clone = $('#comment-template').clone();
    var name_el = clone.find('.comment-name');
    var text_el = clone.find('.comment-text');
    var date_el = clone.find('.comment-date');
    name_el.text(comment.name);
    text_el.text(comment.text);
    date_el.text(date_short);
    if(date_long) date_el.attr('title', date_long);
    clone.appendTo('#comment-list');

//    // setup administrative tools
//    var edit_url = get_rest_url_for_current_document() + '?edit=' + encodeURIComponent(comment.date);
//    var edit_el = $(document.createElement('a'));
//    edit_el.text('[ed]');
//    edit_el.attr('href', edit_url);
//    $(document.createTextNode(' ')).appendTo(name_el);
//    edit_el.appendTo(name_el);
}

// return string like 'http://thisserver/comments/domain/path/path'
function get_rest_url_for_current_document() {
    var host = window.location.hostname;
    var port = window.location.port;
    var portSuffix = (port != '80') ? (':' + port) : '';
    var path = host + window.location.pathname;
    return window.location.protocol + '//' + host + portSuffix + '/comments/' + path;
}

function load_comments() {
    $.ajax({
        //url: get_rest_url_for_current_document()+'?callback=?',
        //dataType: 'jsonp',
        url: get_rest_url_for_current_document(),
        dataType: 'json',
        success: function(json_data) {
            $.each(json_data, function(idx, comment) {
                add_comment(comment);
            });
        },
        error: function(xhr, ajaxOptions, thrownError) {
            report_error('#comment-loading-error', 'Sorry, comments gonna be available later', false);
        }
    });
}

function setup_new_comment_form() {
    var form = $('#new_comment_form');

    // pre set name from cookies
    var input_name = $('#new_comment_form input[name="name"]');
    var name_from_cookie = get_cookie('commenter_name');
    if(name_from_cookie) {
        input_name.val(name_from_cookie);
    }
    setup_plain_editor(input_name);

    form.submit(function () {
        try {
            var name = $('#new_comment_form input[name="name"]').val();
            var text_el = $('#new_comment_form textarea[name="text"]');
            var text = text_el.val();
            var new_comment = {
                'name': name,
                'text': text
            };

            // save commenter's name before to send the comment
            set_cookie('commenter_name', new_comment.name);

            $.ajax({
                url:get_rest_url_for_current_document(),
                type:'POST',
                // NB: content type other than default leads Firefox to use OPTIONS method (that's wrong in practice)
                //contentType: 'application/json',
                data:JSON.stringify(new_comment),
                success:function (res) {
                    add_comment(new_comment, true);
                    text_el.val('');
                    scroll_bottom();
                },
                error: function(x, y, z) {
                    report_error('#new-comment-error', 'Cannot add new comment. Make sure every field is filled', true);
                }
            });
            return false;
        } catch (e) {
            alert('Error submitting form: ' + e);
            return false;
        }
    })
}

$(document).ready(function() {
    if($('#comment-list').length > 0) {
        load_comments();
    }
});

$(document).ready(function() {
    setup_new_comment_form();
});

/////////////////////////////////////////////

function tryRedirectToCanonicalURL() {
    var redirectURL = null;

    var host = window.location.hostname;
    var noRedirect = (host == 'localhost' || host == '127.0.0.1' || host == 'sovietgroove.com' || host == 'www.sovietgroove.com');
    if (!noRedirect) {
        var canonicalBase = 'http://www.sovietgroove.com';
        redirectURL = canonicalBase + window.location.pathname;
    }

    //console.log("url: " + window.location.href);
    //console.log("url: " + redirectURL);

    if (redirectURL) {
        window.location.replace(redirectURL);
    }
}

/////////////////////////////////////////////

// audio player
// respond on clicking 'play' image button by inserting a swf player instead of the button image
$(document).ready(function() {
    $('.audio-player').click(function() {
        var swf = $(this).attr('data-swf-html');
        if(swf) {
            $(this).replaceWith(swf);
        }
        return false;
    });
});

/////////////////////////////////////////////

tryRedirectToCanonicalURL();
