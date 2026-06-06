# HammerDB CI web field rendering helper.
#
# This keeps JOBCI.start_cmd unchanged and only adjusts the value at the final
# web display step immediately before the existing %html(...) rendering.

proc ci_display_value {field val} {
    # start_cmd may contain escaped double quotes from the saved command text.
    # For copy/paste-friendly display only, show \" as " while preserving the
    # quote characters and leaving all other backslashes untouched.
    if {$field eq "start_cmd"} {
        set val [string map {\\\" \"} $val]
    }
    return $val
}

proc ci_render_field_pre {field val} {
    set val [ci_display_value $field $val]
    wapp-subst {<pre style="white-space:pre-wrap; overflow-wrap:anywhere;">%html($val)</pre>}
}
