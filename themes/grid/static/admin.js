function reply_to_comment(elem, comment_id) {
	$(elem).css({'background':'grey', 'color':'white'});
    $("input#reply-to").val(comment_id);
    return false; // prevent following the '#' link
}
