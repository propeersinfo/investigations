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