"""Defines exceptions which can be thrown by HttpClient."""

class RPCError(Exception):
    """Represents a structured error returned from Steem/Jussi"""

    @staticmethod
    def build(error, method, args, index=None):
        """Given an RPC error, builds exception w/ appropriate severity."""
        index = '[%d]' % index if index else ''
        message = RPCError.humanize(error)
        message += ' in %s%s(%s)' % (method, index, str(args)[0:1024])

        if RPCError.is_recoverable(error):
            return RPCError(message)
        return RPCErrorFatal(message)

    @staticmethod
    def humanize(error):
        """Get friendly error string from steemd RPC response."""
        detail = error['message'] if 'message' in error else str(error)

        if 'data' not in error:
            name = 'error' # eg db_lock_error
        elif 'name' in error['data']:
            name = error['data']['name']
        elif 'error_id' in error['data']:
            if 'exception' in error['data']:
                etype = error['data']['exception']
            else:
                etype = 'error'
            name = '%s [jussi:%s]' % (etype, error['data']['error_id'])
        else:
            name = 'error [unspecified:%s]' % str(error)

        return "%s: `%s`" % (name, detail)

    @staticmethod
    def is_recoverable(error):
        """Check if error appears recoverable (e.g. network condition)"""
        assert 'message' in error, "missing error msg key: {}".format(error)
        assert 'code' in error, "missing error code key: {}".format(error)
        message = error['message']
        code = error['code']

        # common steemd error
        # {"code"=>-32003, "message"=>"Unable to acquire database lock"}
        if message == 'Unable to acquire database lock':
            return True

        # rare steemd error
        # {"code"=>-32000, "message"=>"Unknown exception",
        #  "data"=>"0 exception: unspecified\nUnknown Exception\n[...]"}
        if message == 'Unknown exception':
            return True

        # generic jussi error
        # {'code': -32603, 'message': 'Internal Error', 'data': {
        #    'error_id': 'c7a15140-f306-4727-acbd-b5e8f3717e9b',
        #    'request': {'amzn_trace_id': 'Root=1-5ad4cb9f-...',
        #      'jussi_request_id': None}}}
        if message == 'Internal Error' and code == -32603:
            return True

        # jussi error (e.g. Timeout)
        # {'code': 1100, 'message': 'Bad or missing upstream response',
        #  'data':{'error_id': 'fc3650d7-72...',
        #          'exception': TimeoutError()}}}, ..."
        if message == 'Bad or missing upstream response' and code == 1100:
            return True

        return False

class RPCErrorFatal(RPCError):
    """Represents a structured steemd error which is not recoverable."""
    pass
