// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

wn.provide("wn.views.calendar");
wn.provide("wn.views.calendars");

wn.views.CalendarFactory = wn.views.Factory.extend({
	make: function(route) {
		var me = this;
		wn.model.with_doctype(route[1], function() {
			var options = {
				doctype: route[1],
				page: me.make_page()
			};
			$.extend(options, wn.views.calendar[route[1]] || {});
			
			wn.views.calendars[route[1]] = new wn.views.Calendar(options);
		});
	}
});


wn.views.Calendar = Class.extend({
	init: function(options) {
		$.extend(this, options);

		wn.require('lib/js/lib/fullcalendar/fullcalendar.css');
		wn.require('lib/js/lib/fullcalendar/fullcalendar.js');

		this.make_page();
		this.setup_options();
		this.make();
	},
	make_page: function() {
		var module = locals.DocType[this.doctype].module;
		this.page.appframe.set_title(wn._("Calendar") + " - " + wn._(this.doctype));
		this.page.appframe.add_module_icon(module==="Core" ? "Calendar" : module)
		this.page.appframe.set_views_for(this.doctype, "calendar");
		
		var me = this;
		$(this.page).on("show", function() {
			me.$cal.fullCalendar("refetchEvents");
		})
		if(this.doctype == 'Patient Encounter Entry'){
			// alert("hello")
			// console.log(['hello',me])
			this.wrapper = $(this.page).find(".layout-main");
			(this.wrapper).prepend($('<div class="help" id="help"></div>').html('Modality: <select class = "form-control" id="sel" style="width:30%;"><option value=""></option></select> \
					Study: <select class = "form-control" id="sel1" style="width:30%;"><option value=""></option></select> <br><br>'));
			

			var dropdown = document.getElementById("sel");
	        wn.call({
	                method: 'clinical.doctype.patient_encounter_entry.patient_encounter_entry.get_modality',
	                callback: function(r) {
	                        for(var i=0;i<(r.message).length;i++){
	                                var opt = document.createElement("option");
	                                opt.value = r.message[i][0];
	                                opt.text = r.message[i][0];
	                                dropdown.appendChild(opt);
	                        }
	                }
	        })

			$("#sel").click(function() {
				var dropdown = document.getElementById("sel1");
				wn.call({
		                method: 'clinical.doctype.patient_encounter_entry.patient_encounter_entry.get_study',
		                args:{modality:$("#sel").val()},
		                callback: function(r) {
		                		// console.log(r)
		                		$("#sel1").empty();
		                		var opt = document.createElement("option");
		                        opt.value = '';
		                        opt.text = '';
		                        dropdown.appendChild(opt);
		                        for(var i=0;i<(r.message).length;i++){
		                                var opt = document.createElement("option");
		                                opt.value = r.message[i][0];
		                                opt.text = r.message[i][0];
		                                dropdown.appendChild(opt);
		                        }
		                }
		        })
				// console.log(me.$wrapper)
				$('.fc').remove()
				$('.alert.alert-info.form-intro-area').remove()
				me.setup_options()
				me.make()
			})
		}

	},
	make: function() {
		var me = this;
		this.$wrapper = $(this.page).find(".layout-main");
		this.$cal = $("<div>").appendTo(this.$wrapper);
		wn.utils.set_footnote(this, this.$wrapper, wn._("Select or drag across time slots to create a new event."));
		// 
		// $('<div class="help"></div>')
		// 	.html(wn._("Select dates to create a new ") + wn._(me.doctype))
		// 	.appendTo(this.$wrapper);

		this.$cal.fullCalendar(this.cal_options);
	},
	field_map: {
		"proj": $("#sel").val(),
		"proj1": $("#sel1").val(),
		"id": "name",
		"start": "start",
		"end": "end",
		"allDay": "all_day",
	},
	styles: {
		"standard": {
			"color": "#999"
		},
		"important": {
			"color": "#b94a48"
		},
		"warning": {
			"color": "#f89406"
		},
		"success": {
			"color": "#468847"
		},
		"info": {
			"color": "#3a87ad"
		},
		"inverse": {
			"color": "#333333"
		}
	},
	setup_options: function() {
		var me = this;
		this.cal_options = {
			header: {
				left: 'prev,next today',
				center: 'title',
				right: 'month,agendaWeek,agendaDay'
			},
			editable: true,
			selectable: true,
			selectHelper: true,
			events: function(start, end, callback) {
				return wn.call({
					method: me.get_events_method || "webnotes.widgets.calendar.get_events",
					type: "GET",
					args: me.get_args(start, end),
					callback: function(r) {
						var events = r.message;
						me.prepare_events(events);
						callback(events);
					}
				})
			},
			eventClick: function(event, jsEvent, view) {
				// edit event description or delete
				var doctype = event.doctype || me.doctype;
				if(wn.model.can_read(doctype)) {
					wn.set_route("Form", doctype, event.name);
				}
			},
			eventDrop: function(event, dayDelta, minuteDelta, allDay, revertFunc) {
				me.update_event(event, revertFunc);
			},
			eventResize: function(event, dayDelta, minuteDelta, allDay, revertFunc) {
				me.update_event(event, revertFunc);
			},
			select: function(startDate, endDate, allDay, jsEvent, view) {
				if(jsEvent.day_clicked && view.name=="month")
					return;
				var event = wn.model.get_new_doc(me.doctype);
				
				event[me.field_map.start] = wn.datetime.get_datetime_as_string(startDate);
				
				if($("#sel").val())
					event[me.field_map.proj] = $("#sel").val()

				if($("#sel1").val())
					event[me.field_map.proj1] = $("#sel1").val()				

				if(me.field_map.end)
					event[me.field_map.end] = wn.datetime.get_datetime_as_string(endDate);

				if(me.field_map.allDay)
					event[me.field_map.allDay] = allDay ? 1 : 0;

				wn.set_route("Form", me.doctype, event.name);
			},
			dayClick: function(date, allDay, jsEvent, view) {
				jsEvent.day_clicked = true;
				return false;
			}
		};
		
		if(this.options) {
			$.extend(this.cal_options, this.options);
		}
	},
	get_args: function(start, end) {
		return {
			doctype: this.doctype,
			start: wn.datetime.get_datetime_as_string(start),
			end: wn.datetime.get_datetime_as_string(end),
			op:$("#sel").val()
		}
	},
	prepare_events: function(events) {
		var me = this;
		$.each(events, function(i, d) {
			// console.log(['event', d])
			d.id = d.name;
			d.editable = wn.model.can_write(d.doctype || me.doctype);
			
			// do not allow submitted/cancelled events to be moved / extended
			if(d.docstatus && d.docstatus > 0) {
				d.editable = false;
			}
				
			$.each(me.field_map, function(target, source) {
				d[target] = d[source];
			});
			
			if(!me.field_map.allDay) 
				d.allDay = 1;
				
			if(d.status) {
				// console.log(['status',status])
				if(me.style_map) {
					$.extend(d, me.styles[me.style_map[d.status]] || {});
				} else {
					$.extend(d, me.styles[wn.utils.guess_style(d.status, "standard")]);
				}
			} else {
				$.extend(d, me.styles["standard"]);
			}
		})
	},
	update_event: function(event, revertFunc) {
		var me = this;
		wn.model.remove_from_locals(me.doctype, event.name);
		return wn.call({
			method: me.update_event_method || "webnotes.widgets.calendar.update_event",
			args: me.get_update_args(event),
			callback: function(r) {
				if(r.exc) {
					show_alert("Unable to update event.")
					revertFunc();
				}
			}
		});		
	},
	get_update_args: function(event) {
		var args = {
			name: event[this.field_map.id]
		};
		args[this.field_map.start] 
			= wn.datetime.get_datetime_as_string(event.start);
			
		if(this.field_map.end) 
			args[this.field_map.end] = wn.datetime.get_datetime_as_string(event.end);

		if(this.field_map.allDay)
			args[this.field_map.allDay] = event.allDay ? 1 : 0;
		
		args.doctype = event.doctype || this.doctype;
		
		return { args: args, field_map: this.field_map };
	}
})