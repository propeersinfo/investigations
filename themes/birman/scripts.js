jQuery.fn.exists = function() { return jQuery(this).length > 0; }

<!-- code related to replacing youtube images with clips -->
//function byclass(className, callback) {
//	var ee = document.getElementsByClassName(className)
//	for(i = 0; i < ee.length; i++) {
//		callback(ee[i])
//	}
//}
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
    img.src = "static/playvideo480.png"
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