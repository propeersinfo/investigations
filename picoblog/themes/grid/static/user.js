/*
 * Internationalization by JavaScript.
 * Usage: execute the following JS code. HTML should look like the following:
 * <body lang="ru">
 * <div class='i18n'>No lang: <i lang="EN">EN</i> <i lang="RU">RU</i> <i>No lang</i></div>
 */
$(document).ready(function() {
    function get_element_display_mode(elem) {
        var tag = elem.tagName.toLowerCase();
        return (tag == 'div' || tag == 'p') ? 'block' : 'inline';
    }
    var desired_lang = $('body').get(0).lang;
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
//    //alert($(form.text))
//    try {
//        alert($(form)[0].effect)
//        jQuery(form.text).effect("highlight", {}, 3000);
//    } catch(e) {
//        //alert(e)
//        return false;
//    }
//    return false;
//}

//$(document).ready(function() {
//    var form = $('#comment-form');
//    form.submit(function() {
//        q = form.find('#comment-text');
//        if(q.length == 1) {
//            q.effect("highlight", {}, 3000);
//        }
//        return false;
//    })
//})

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
});