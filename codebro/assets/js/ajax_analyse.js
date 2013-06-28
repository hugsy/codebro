
/**
 *
 */
function dajax_init(tag, func, pid) {
	var button = $('#btn_'+tag);
	if (button == null) {
		bootbox.alert("Failed to find tag btn_"+tag);
		return;
	}
	
	button[0].disabled = 'disabled';
    button[0].value = 'Please Wait...'; 
    
    func(dajax_callback, {'project_id': pid});
    //setTimeout(function(){bootbox.alert('Yeah, I know, go grab some coffee while I\'m on it ... ');}, 60000);
}


/**
 *
 */
function dajax_callback(data) {
    bootbox.alert(data.message);
	
    if(data.status != 0) {
		/* call has failed */
		var button = $('#btn_parse');
		if (button != null) {
		} else {
			button = $('#btn_unparse');
		}
		button[0].removeAttribute('disabled');
		button[0].value = 'Retry';
		
    } else {
		/* call succeeded, reload page */
		setTimeout( function(){location.reload();}, 3000);
    }
}
