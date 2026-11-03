from collections import OrderedDict

MAX_TRACES = 64

_traces = OrderedDict()


def remember_trace(trace):
    trace_id = trace["trace_id"]
    _traces[trace_id] = trace
    _traces.move_to_end(trace_id)
    while len(_traces) > MAX_TRACES:
        _traces.popitem(last=False)


def get_trace(trace_id):
    trace = _traces.get(trace_id)
    if trace is not None:
        _traces.move_to_end(trace_id)
    return trace