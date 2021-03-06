var Dom = {
	get: function(el) {
		if (typeof el === 'string') {
			return document.getElementById(el);
		} else {
			return el;
		}
	},
	add: function(el, dest) {
		var el = this.get(el);
		var dest = this.get(dest);
		dest.appendChild(el);
	},
	remove: function(el) {
		el.parentNode.removeChild(el);
	}
};


var Event = {
	add: function() {
		if (window.addEventListener) {
			return function(el, type, fn) {
				Dom.get(el).addEventListener(type, fn, false);
			};
		} else if (window.attachEvent) {
			return function(el, type, fn) {
				var f = function() {
					fn.call(Dom.get(el), window.event);
				};
				Dom.get(el).attachEvent('on' + type, f);
			};
		}
	}()
};

// Add imgs-input-boxes at will

Event.add(window, 'load', function() {
	var i = 0;
	var n = 0;
	Event.add('add-img', 'click', function() {
	var del = document.createElement('span');
	del.innerHTML = '<img src="/images/minus.png"> ';
	Dom.add(del, 'images');
	var el = document.createElement('span');
	el.innerHTML = '<input name="img'+ ++i +'" type="file" value="img'+ i +'" /> IMG '+ i +' <br />'+
                    '&#160;&#160;&#160;&#160;<input name="description'+ i +'" type="text" " size=40/> <br />';
	Dom.add(el, 'images');
		Event.add(del, 'click', function(e) {
			Dom.remove(el);
         i=i-1
			Dom.remove(this);
		});
	});

// Add tag-input-boxes at will

	Event.add('add-tag', 'click', function() {
		var del = document.createElement('span');
		del.innerHTML = '<img src="/images/minus.png"> ';
		Dom.add(del, 'tags');
		var el = document.createElement('span');
		el.innerHTML = '<input name="tag'+ ++n +'" type="text" /> tag '+ n +' <br />';
		Dom.add(el, 'tags');
		Event.add(del, 'click', function(e) {
			Dom.remove(el);
         n=n-1
			Dom.remove(this);
		});
	});
});
