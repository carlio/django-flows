

class FlowHistory(object):

    def __init__(self, state, position, flow_position_instance):
        self._position = position
        self._flow_position_instance = flow_position_instance
        self._history = state['_history'] if '_history' in state else []

        url_name = self._position.url_name

        # if we have moved back in the history, throw away the 'future' parts
        for i, pair in enumerate(self._history):
            if url_name == pair[0]:
                # found the current flow in the history, so reset to its position
                self._history = self._history[:i]
                break

        self._back_url = self._history[-1][1] if len(self._history) > 0 else None


    def add_to_history(self, state):
        url_name = self._position.url_name

        current_action = self._flow_position_instance.get_action()
        url = current_action.get_absolute_url()
        skip_on_back = getattr(current_action, 'skip_on_back', False)

        self._history.append((url_name, url, skip_on_back))
        state['_history'] = self._history


    def get_back_url(self):
        return self._back_url