extends GdUnitTestSuite
## The rich-text writer owns its detached formatter, but borrows the caller's output.

var _outputs: Array[RichTextLabel] = []

func after_test() -> void:
	for output in _outputs:
		if is_instance_valid(output):
			output.free()
	_outputs.clear()

func _output() -> RichTextLabel:
	var output := RichTextLabel.new()
	_outputs.append(output)
	return output

func _release_surviving_formatter(formatter: WeakRef) -> bool:
	# Keep the original RED control from leaking its known orphan into later tests.
	var survived := is_instance_valid(formatter.get_ref())
	if survived:
		formatter.get_ref().free()
	return survived

func test_final_writer_reference_releases_formatter_but_not_borrowed_output() -> void:
	var output := _output()
	var writer := GdUnitRichTextMessageWriter.new(output)
	var writer_ref: WeakRef = weakref(writer)
	var formatter_ref: WeakRef = weakref(writer.get("_report_formatter"))
	var alias := writer
	writer = null
	assert_bool(is_instance_valid(alias)).is_true()
	assert_bool(is_instance_valid(writer_ref.get_ref())).is_true()
	assert_bool(is_instance_valid(formatter_ref.get_ref())).is_true()
	alias = null
	assert_bool(is_instance_valid(writer_ref.get_ref())).is_false()
	var formatter_survived := _release_surviving_formatter(formatter_ref)
	assert_bool(formatter_survived).is_false()
	assert_bool(is_instance_valid(output)).is_true()
	output.append_text("Caller still owns this output.")
	assert_str(output.get_parsed_text()).contains("Caller still owns this output.")

func test_message_and_stack_trace_survive_writer_cleanup_without_dangling_callback() -> void:
	var output := _output()
	var writer := GdUnitRichTextMessageWriter.new(output)
	var formatter_ref: WeakRef = weakref(writer.get("_report_formatter"))
	var frames: Array[GdUnitStackTraceElement] = [
		GdUnitStackTraceElement.new("res://test/lifetime_fixture.gd", 17, "lifetime_probe")
	]
	writer.style(GdUnitMessageWriter.BOLD).println_message("Formatter message sentinel")
	writer.print_stack_trace(GdUnitStackTrace.of(frames))
	assert_str(output.get_parsed_text()).contains("Formatter message sentinel")
	assert_str(output.get_parsed_text()).contains("lifetime_probe")
	assert_str(output.get_parsed_text()).contains("lifetime_fixture.gd : 17")
	assert_int(output.meta_clicked.get_connections().size()).is_equal(1)
	var text := output.get_parsed_text()
	writer = null
	var connections_after_release := output.meta_clicked.get_connections().size()
	_release_surviving_formatter(formatter_ref)
	assert_int(connections_after_release).is_equal(0)
	assert_bool(is_instance_valid(output)).is_true()
	assert_str(output.get_parsed_text()).is_equal(text)
	output.append_text("\nCaller can append after cleanup.")
	assert_str(output.get_parsed_text()).contains("Caller can append after cleanup.")

func test_previously_freed_formatter_does_not_double_free_or_destroy_output() -> void:
	var output := _output()
	var writer := GdUnitRichTextMessageWriter.new(output)
	var formatter := writer.get("_report_formatter") as Panel
	formatter.free()
	writer = null
	assert_bool(is_instance_valid(output)).is_true()
	output.append_text("Borrowed output remains usable.")
	assert_str(output.get_parsed_text()).contains("Borrowed output remains usable.")
