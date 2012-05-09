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

function read_cookie(name) {
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
    var desired_lang = read_cookie('user_lang');
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

function comment_form_submit(form) {
    var text_elem = form.elements['text'];
    var text = $.trim(text_elem.value);
    if(text.length > 0) {
        return true;
    } else {
        $(text_elem).css('border', '1px solid #f00');
        return false;
    }
}

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
// ctrl+arrows navigation
////////////////////////////////////////////////////

$(document).ready(function() {
    if(document.addEventListener) {
        document.addEventListener('keydown', function(event) {
            switch (event.keyCode ? event.keyCode : event.which ? event.which : null) {
                case 0x25:
                    link = document.getElementById ('prev-link');
                    break;
                case 0x27:
                    link = document.getElementById ('next-link');
                    break;
            }
            if (typeof(link) != 'undefined' && link && link.href)
                document.location = link.href;
        }, false);
    }
});

if(document.location.hostname == 'localhost') {
    $(document).ready(function() {
        $("a").each(function(pos,a){
            var m = a.href.match(/^(http:..localhost)(.+)$/);
            if(m[2].indexOf('/preview') < 0) {
                a.href = m[1] + '/preview' + m[2];
            }
        });
    });
}
