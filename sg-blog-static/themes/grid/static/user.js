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
	repl.setAttribute('width', 480);
	repl.setAttribute('height', 360);
	repl.setAttribute('src', 'http://www.youtube.com/embed/'+ytid+'?autoplay=1&theme=dark');
	repl.setAttribute('frameborder', 0);
	repl.setAttribute('allowfullscreen', 1);
	
	img.parentNode.replaceChild(repl, img)
}
function prepareYoutubeClips() {
  $("img.youtube").each(function(pos,img){
    var preview = img.src;
    img.style.background = "black url(" + preview + ")";
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

////////////////////////////////////////////////////
// external comments
////////////////////////////////////////////////////

function report_error(selector, msg) {
    $(selector).
        css('display', 'table'). // it maybe an inline element initially
        text(msg).
        delay(5000).
        fadeOut('slow');
}

function add_comment(comment, is_new) {
    if(typeof is_new == 'undefined') {
        is_new = false;
    }
    var date_str = 'n/a';
    if(is_new) {
        date_str = format_date_mdy(new Date());
    } else {
        var date = Date.parse(comment.date);
        if(date) {
            date = new Date();
            date_str = format_date_mdy(date);
        }
    }

    var clone = $('#comment-template').clone();
    clone.find('.comment-name').text(comment.name);
    clone.find('.comment-text').text(comment.text);
    clone.find('.comment-date').text(date_str);
    clone.appendTo('#comment-list');
}

function get_rest_url_for_current_document() {
    var host = window.location.hostname;
    var path = host + window.location.pathname;
    return 'http://' + host + '/comments/' + path;
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
            report_error('#comment-loading-error', 'Cannot load more comments at the moment.');
        }
    });
}

function setup_new_comment_form() {
    var form = $('#new_comment_form');

    // pre set name from cookies
    $('#new_comment_form input[name="name"]').val(get_cookie('commenter_name'));

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
                    report_error('#new-comment-error', 'Cannot post new comment. Make sure every field is filled.');
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
