/**
 *
 */
function generate_menu(urls) {
	var menu = '<p><a href="'+urls[0]+'&xref=0">Draw graph from this function</a></p>';
	menu += '<p><a href="'+urls[0]+'&xref=1">Draw graph to this function</a></p>';

	if (urls[1].length > 0) {
		menu += '<p><a href="'+urls[1]+'">Jump to declaration</a></p>';
	}

	return menu;
}


/**
 *
 */
function function_menu(id, urls) {
  var off = $('#'+id).offset();
  var d = $('#function_menu');

  if(d[0].style.visibility == 'visible') {
    d[0].style.visibility = 'hidden';
    return;
  }

  d[0].style.visibility = 'visible';
  d.offset( {top: off.top + 20, left: off.left } );

  d[0].innerHTML = generate_menu(urls);
}


$(document).ready(function() {
  $("#canvas_code").click(function () {
    $("#canvas_code").unhighlight();
  });

  $("#canvas_code").dblclick(function () {
    var sel = window.getSelection();
    $("#canvas_code").highlight(sel.toString());
  });

});
