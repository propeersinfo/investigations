// replace youtube images with video clips

function replaceYoutubeImageWithClip(img) {
	var ytid = img.getAttribute('ytid')
	
	repl = document.createElement('iframe')
	repl.setAttribute('width', 480)
	repl.setAttribute('height', 360)
	repl.setAttribute('src', 'http://www.youtube.com/embed/'+ytid+'?autoplay=1&theme=dark')
	repl.setAttribute('frameborder', 0)
	repl.setAttribute('allowfullscreen', 1)
	
	img.parentNode.replaceChild(repl, img)
}
function prepareYoutubeClips() {
  $("img.youtube").each(function(pos,img){
    var preview = img.src
    img.style.background = "black url(" + preview + ")"
    img.src = "/static/playvideo480.png"
    var a = img.parentNode
    if(a) {
      a.style.background = "url(" + preview + ")"
      a.style.display = "inline-block"
      a.onclick = function(event) { replaceYoutubeImageWithClip(img); return false; }
    }
  })
}
function replyToComment(commentId) {
	input = $("input#reply-to")
	input.val(commentId)
}
$(document).ready(function() {
  prepareYoutubeClips()
});

// replacing header text with image

jQuery.fn.exists = function() {
	return jQuery(this).length > 0;
}
jQuery.fn.getInnerText = function() {
	function isTextNode() { return this.nodeType == 3 }
	return this.contents().filter(isTextNode).text()
}
// NB: standard escape() handles unicode in a way incompatible with GAE: %UABCD
/*function customEscape(text) {
	//text = text.replace(/&amp;/g, '&')
	var res = ''
	var len = text.length
	for(var i = 0; i < len; i++) {
		var ch = text[i]
		var code = text.charCodeAt(i)
		if(ch >= '0' && ch <= '9')
			res += ch
		else if(ch >= 'a' && ch <= 'z')
			res += ch
		else if(ch >= 'A' && ch <= 'Z')
			res += ch
		else if(code < 256)
			res += '%' + code.toString(16)
		else
			res += ch
	}
	alert(res)
	return res
}*/
// NB: standard escape() handles unicode in a way incompatible with GAE: %UABCD
function customEscape(text) {
	text = text.replace(/\s/g, '%20')
	text = text.replace(/\"/g, '%22')
	text = text.replace(/\'/g, '%27')
	text = text.replace(/&/g,  '%26')
	text = text.replace(/\(/g, '%28')
	text = text.replace(/\)/g, '%29')
	return text
}
function adjustHeader(headerId) {
	function getText(h1) {
		var text = ''
		var elems = [ h1, h1.find("a")   ]
		jQuery.each(elems, function(idx, elem) {
			s = jQuery.trim(elem.getInnerText())
			if(s) text = s
		})
		return text
	}
	var h1 = $("#"+headerId)
	var text = getText(h1)
	if(text) {
		var span = h1.find("span")[0]
		text = customEscape(text)
		//alert("adjusting header for " + headerId + "; text = " + text)
		span.style.backgroundImage = "url(/font?text=" + text + ")"
	}
}

// ctrl+arrows navigation
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
        if (link && link.href)
            document.location = link.href;
    }, false)
});