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
		text = text.replace(/\s/g, '%20') // NB: escape() handles unicode in a way incompatible with GAE.
		text = text.replace(/\"/g, '%22')
		text = text.replace(/\'/g, '%27')
		text = text.replace(/\(/g, '_')
		text = text.replace(/\)/g, '_')
		//text = "75%20(1979)"
		//alert("adjusting header for " + headerId + "; text = " + text)
		span.style.backgroundImage = "url(/font?text=" + text + ")"
	}
}
