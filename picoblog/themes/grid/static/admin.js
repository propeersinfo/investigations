function reply_to_comment(elem, comment_id) {
	//alert(typeof elem);
	$(elem).css({'background':'grey', 'color':'white'});
    $("input#reply-to").val(comment_id);
}
